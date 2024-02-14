import inspect
import importlib
import logging
import os
import os.path
import subprocess
import sys

from watchdog.observers import Observer
from watchdog import events as watchdog_events

import beaker_kernel
from beaker_kernel.server.main import BeakerJupyterApp
from beaker_kernel.lib.autodiscovery import autodiscover


# Global notebook storage for notebook that lives for lifetime of service
notebook_content = None
logger = logging.getLogger(__file__)

app_subprocess = None


def _jupyter_server_extension_points():
    return [{"module": "beaker_kernel.server.main", "app": DevBeakerJupyterApp}]


class DevBeakerJupyterApp(BeakerJupyterApp):
    pass

class BeakerHandler(watchdog_events.FileSystemEventHandler):
    def __init__(self, observer, modules) -> None:
        super().__init__()
        self.observer = observer
        self.modules = modules

    def on_any_event(self, event):
        global app_subprocess
        # Only restart based on specific message types below
        if not isinstance(
            event,
            (
                watchdog_events.FileModifiedEvent,
                watchdog_events.FileMovedEvent,
                watchdog_events.FileDeletedEvent,
                watchdog_events.FileCreatedEvent
            )
        ) or event.src_path == __file__:
            return super().on_any_event(event)

        # Only restart for changes to python files or procedure files
        if event.src_path.endswith(".py") or "procedures" in event.src_path:

            # Drain the queue:
            while not observer.event_queue.empty():
                observer.event_queue.get_nowait()

            # Try to reimport all the modules as a way to check if we will crash
            # if we restart.
            try:
                for mod in self.modules:
                    importlib.reload(mod)
            except ImportError:
                logger.error("Error reloading")

            if app_subprocess:
                app_subprocess.kill()


def create_observer():
    contexts = autodiscover("contexts")
    subkernels = autodiscover("subkernels")
    modules = set([inspect.getmodule(beaker_kernel)])
    modules.update([inspect.getmodule(cls) for _, cls in contexts.items()])
    modules.update([inspect.getmodule(cls) for _, cls in subkernels.items()])
    all_paths = sorted([os.path.dirname(inspect.getabsfile(mod)) for mod in modules], key=lambda f: len(f))
    paths = set()
    for path in all_paths:
        is_subpath = False
        for saved_path in paths:
            if path.startswith(saved_path):
                is_subpath = True
                break
        if not is_subpath:
            paths.add(path)

    observer = Observer()
    handler = BeakerHandler(observer, modules)

    for path in paths:
        observer.schedule(event_handler=handler, path=path, recursive=True)
    observer.start()
    return observer

def main():
    serverapp = DevBeakerJupyterApp.initialize_server(argv=["--ip", "0.0.0.0"])
    serverapp.start()


if __name__ == "__main__":
    if "watch" in sys.argv:
        observer = create_observer()
        try:
            while True:
                app_subprocess = subprocess.Popen([
                    sys.executable,
                    sys.argv[0]],
                    env=os.environ
                )
                app_subprocess.wait()
        finally:
            if app_subprocess:
                logger.error("Shutting down subprocess...")
                app_subprocess.kill()
    else:
        main()
