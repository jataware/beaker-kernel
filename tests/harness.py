import asyncio
import json
import pytest
import signal
import threading
import time
import urllib.parse
import traitlets
from collections import defaultdict

from jupyter_client import KernelConnectionInfo, LocalPortCache
from jupyter_client.asynchronous.client import AsyncKernelClient
from jupyter_client.provisioning.provisioner_base import KernelProvisionerBase
from jupyter_client.provisioning.local_provisioner import LocalProvisioner
from jupyter_client.session import Session
from jupyter_server.services.sessions.sessionmanager import SessionManager
from tornado.ioloop import IOLoop

from beaker_kernel.service.base import (
    BeakerServerApp, BaseBeakerServerApp, BeakerKernelMappingManager, BeakerKernelManager
)
from beaker_kernel.kernel import BeakerKernel

def _jupyter_server_extension_points():
    return [{"module": __package__, "app": TestApp}]


@pytest.fixture(scope="session")
def server():
    server_obj = TestServer()
    server_obj.start()
    yield server_obj
    server_obj.stop()

@pytest.fixture(scope="class")
async def kernel_connection(server):
    import uuid
    name = uuid.uuid4().hex
    conn = await TestKernelConnection.new(server, name)
    yield conn
    await conn.destroy()

@pytest.fixture(scope="class")
async def kernel():
    import uuid
    name = uuid.uuid4().hex
    conn = await TestKernelConnection.new(server, name)
    yield conn
    await conn.destroy()


class TestBeakerKernelProvisioner(LocalProvisioner):
    thread: threading.Thread
    io_loop: IOLoop
    kernel: BeakerKernel

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thread = None
        self.kernel = None

    def pre_launch(self, **kwargs):
        # kwargs.setdefault("cmd", "local")
        km = self.parent
        port_types = ["shell", "iopub", "stdin", "hb", "control"]
        lpc = LocalPortCache.instance()
        port_list = [lpc.find_available_port(km.ip) for _ in port_types]

        for port_type, port in zip(port_types, port_list):
            setattr(km, f"{port_type}_port", port)

        return super().pre_launch(**kwargs)

    @property
    def has_process(self):
        return self.thread is None or self.thread.is_alive()

    def start_kernel(self, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.io_loop = IOLoop.current()
        with open(self.parent.connection_file) as f:
            config = json.load(f)
        self.kernel = BeakerKernel(
            config, kernel_id=self.parent.kernel_id, connection_file=self.parent.connection_file
        )
        self.parent.kernel = self.kernel
        self.io_loop.start()


    async def poll(self):
        return self.has_process

    async def wait(self):
        self.thread.join()

    async def send_signal(self, signum):
        if signum == signal.SIGINT:
            self.kernel._interrupt()
        else:
            raise NotImplementedError

    async def kill(self, restart = False):
        pass

    async def terminate(self, restart = False):
        pass

    async def launch_kernel(self, cmd, **kwargs):
        self.thread = threading.Thread(target=self.start_kernel, kwargs=kwargs, daemon=False)
        self.thread.start()
        return self.parent.get_connection_info()

    async def cleanup(self, restart = False):
        if self.kernel and self.kernel.context:
            self.kernel.context.cleanup()


class TestKernelManager(BeakerKernelManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _async_pre_start_kernel(self, **kw):
        # self.provisioner = TestBeakerKernelProvisioner(kernel_id=self.kernel_id, kernel_spec=self.kernel_spec, parent=self)
        return super()._async_pre_start_kernel(**kw)


class TestKernelMappingManager(BeakerKernelMappingManager):
    kernel_manager_class = TestKernelManager

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def kernel_manager_factory(self, *args, **kwargs):
        return self.kernel_manager_class(*args, **kwargs)


class TestServer(BeakerServerApp):
    kernel_manager_class = TestKernelMappingManager
    ready: bool

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ready = False

    def init_ioloop(self):
        from tornado import ioloop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.io_loop = ioloop.IOLoop.current()

    async def _post_start(self):
        result = await super()._post_start()
        self.ready = True
        return result


class TestApp(BaseBeakerServerApp):
    serverapp_class = TestServer

    def start_test_server(self):
        self.serverapp.start()

    def stop_test_server(self):
        self.serverapp.stop()

class TestServer():
    def __init__(self):
        self.base_app: TestApp = None
        self.server_thread = None

    @property
    def app(self) -> BeakerServerApp:
        if self.base_app and self.base_app.serverapp:
            return self.base_app.serverapp
        else:
            return None

    def start(self):
        self.base_app = TestApp()
        self.base_app.initialize_server()
        self.server_thread = threading.Thread(target=self.base_app.start_test_server, daemon=False)
        self.server_thread.start()
        self.wait_until_ready()

    def stop(self):
        self.base_app.stop_test_server()
        # Wait for server thread to clean up, up to 5 seconds
        # self.server_thread.join(30)

    def wait_until_ready(self, timeout=15):
        limit = time.time() + timeout
        while not self.app.ready and time.time() < limit:
            time.sleep(0.1)
        if not self.app.ready:
            raise TimeoutError("Server took too long to come online")

    def url(self, path: str):
        url = urllib.parse.urljoin(self.app.public_url, path)
        return url


class TestKernelConnection():
    # session_manager: SessionManager
    kernel_manager: BeakerKernelMappingManager
    km: BeakerKernelManager
    session: Session
    client: AsyncKernelClient
    messages: list[dict]

    def in_server_thread(timeout=15):
        def inner(fn):
            def innercoro(self, *args, **kwargs):
                ioloop = self.server.app.io_loop.asyncio_loop
                coro = fn(self, *args, **kwargs)
                future = asyncio.run_coroutine_threadsafe(coro, ioloop)
                result = future.result(timeout)
                return result
            return innercoro
        return inner

    def __init__(self, server: TestServer):
        self.server = server
        self.messages = []
        self.client = None
        self.msg_thread = None
        self.msg_callbacks = defaultdict(list)

    def on(self, msg_type, callback):
        self.msg_callbacks[msg_type].append(callback)

    def recieved_msg(self, msg):
        msg_type = msg["header"]["msg_type"]
        all_callbacks = self.msg_callbacks[None]
        callbacks = all_callbacks + self.msg_callbacks[msg_type]
        for callback in callbacks:
            callback(msg)
        self.messages.append(msg)

    async def wait_on_msg(self, msg_type, timeout=10):
        future = asyncio.get_running_loop().create_future()
        async def timeout_failure():
            await asyncio.sleep(timeout)
            future.set_exception(TimeoutError)
        timeout_task = asyncio.create_task(timeout_failure())

        def callback(msg):
            timeout_task.cancel()
            future.set_result(msg)

        self.on(msg_type=msg_type, callback=callback)
        msg = await future

        return msg

    def capture_messages(self, channels=None):
        if channels is None:
            channels=["iopub", "shell"]

        ioloop = asyncio.new_event_loop()
        asyncio.set_event_loop(ioloop)

        async def capture():
            channel_cache = None
            while True:
                if self.client: #  and self.client.channels_running:
                    if not channel_cache:
                        channel_cache = [getattr(self.client, f"{channel_name}_channel") for channel_name in channels]
                    for channel in channel_cache:
                        if await channel.msg_ready():
                            msg = await channel.get_msg(timeout=1)
                            if msg:
                                self.recieved_msg(msg)
                await asyncio.sleep(0.1)

        ioloop.run_until_complete(capture())

    async def ready(self):
        return await self.km.ready

    @in_server_thread()
    async def create_session(self, name, context_slug=None):
        mapping_session_manager = await self.server.app.session_manager.create_session(path=name, kernel_name="beaker_kernel")
        return mapping_session_manager

    @classmethod
    async def new(cls, server: TestServer, name=None, context_slug=None):
        self = cls(server)
        self.session = self.create_session(name)
        kernel_id = self.session.get("kernel", {}).get("id", None)

        km = self.server.app.kernel_manager.get_kernel(kernel_id)
        await km.ready
        self.km = km
        self.client = self.km.client()
        self.msg_thread = threading.Thread(target=self.capture_messages, daemon=True)
        self.msg_thread.start()

        return self

    @in_server_thread
    def stop_server(self):
        self.server.stop()

    async def destroy(self):
        # await self.km.shutdown_kernel(now=True)
        self.stop_server()
        # del self.msg_thread
        # Sleep to allow shutdown to occur
        await asyncio.sleep(0.2)

    async def execute_code(self, code, timeout=15):
        msg = self.km.session.msg("execute_request", {
            "code": code,
            "silent": False,
            "store_history": True,
            "allow_stdin": True,
            "stop_on_error": True,
        })
        asyncio.get_event_loop().call_later(0.1, self.client.shell_channel.send, msg)
        msg = await self.wait_on_msg("execute_reply", timeout=timeout)
        return msg.content


    async def query_agent(self, query):
        pass


class TestBeakerKernel():
    pass
