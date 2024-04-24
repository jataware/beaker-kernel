import abc
import json
from typing import Any, Callable
import hashlib
import shutil
from tempfile import mkdtemp
from os import makedirs, environ
import requests

from ..utils import server_url, server_token, action
from ..jupyter_kernel_proxy import ProxyKernelClient

Checkpoint = dict[str, str]

class JsonStateEncoder(json.JSONEncoder):
    pass

class BaseSubkernel(abc.ABC):
    DISPLAY_NAME: str
    SLUG: str
    KERNEL_NAME: str

    WEIGHT: int = 50  # Used for auto-sorting in drop-downs, etc. Lower weights are listed earlier.


    FETCH_STATE_CODE: str = ""

    @classmethod
    @abc.abstractmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        ...

    def __init__(self, jupyter_id: str, subkernel_configuration: dict, context):
        self.jupyter_id = jupyter_id
        self.connected_kernel = ProxyKernelClient(subkernel_configuration)
        self.context = context
    
    def send_response(self, stream, msg_or_type, content=None, channel=None, parent_header={}, parent_identities=None):
        return self.context.send_response(stream, msg_or_type, content, channel, parent_header, parent_identities)

    async def execute(self, command, response_handler=None, parent_header={}):
        return await self.context.execute(command, response_handler, parent_header)

    async def evaluate(self, expression, parent_header={}):
        return await self.context.evaluate(expression, parent_header)


    def cleanup(self):
        if self.jupyter_id is not None:
            try:
                print(f"Shutting down connected subkernel {self.jupyter_id}")
                res = requests.delete(
                    f"{server_url}/api/kernels/{self.jupyter_id}",
                    headers={"Authorization": f"token {server_token}"},
                )
                if res.status_code == 204:
                    self.jupyter_id = None
            except requests.exceptions.HTTPError as err:
                print(err)


class BaseCheckpointableSubkernel(BaseSubkernel):
    SERIALIZATION_EXTENSION: str = "storage"

    def __init__(self, jupyter_id: str, subkernel_configuration: dict, context):
        super().__init__(jupyter_id, subkernel_configuration, context)
        if self.checkpoints_enabled:
            self.checkpoints : list[Checkpoint] = []
            self.storage_prefix = mkdtemp()
            makedirs(self.storage_prefix, exist_ok=True)

    @property
    def checkpoints_enabled(self):
        return environ.get("ENABLE_CHECKPOINTS", "false").lower() == "true"

    def store_serialization(self, filename: str) -> str:
        with open(filename, "rb") as file:
            chunksize = 4 * 1024 * 1024
            hash = hashlib.new("sha256")
            while chunk := file.read(chunksize):
                hash.update(chunk)
            identifier = hash.hexdigest()
            new_filename = f"{self.storage_prefix}/{identifier}.{self.SERIALIZATION_EXTENSION}"

        shutil.move(filename, new_filename)
        return new_filename

    @abc.abstractmethod
    async def generate_checkpoint_from_state(self) -> Checkpoint:
        ...

    @abc.abstractmethod
    async def load_checkpoint(self, checkpoint: Checkpoint):
        ...

    async def add_checkpoint(self) :
        if not self.checkpoints_enabled:
            raise RuntimeError("Checkpoints are not enabled")
        fetched_checkpoint = await self.generate_checkpoint_from_state()
        checkpoint = {
            varname: self.store_serialization(filename) for
            varname, filename in fetched_checkpoint.items()
        }
        self.checkpoints.append(checkpoint)
        return len(self.checkpoints)

   
    async def rollback(self, checkpoint_index: int):
        if not self.checkpoints_enabled:
            raise RuntimeError("Checkpoints are not enabled")
        if checkpoint_index >= len(self.checkpoints):
            raise IndexError(f"Checkpoint at index {checkpoint_index} does not exist")
        checkpoint = self.checkpoints[checkpoint_index]
        await self.load_checkpoint(checkpoint)
        self.checkpoints = self.checkpoints[:checkpoint_index + 1]
    
    @action()
    async def undo(self, message):
        checkpoint_index = message.content.get("checkpoint_index", None)
        await self.rollback(checkpoint_index)
    undo._default_payload = "{\n\t\"checkpoint_index\": 0\n}"

    @action()
    async def save(self, message):
        return await self.add_checkpoint()
    save._default_payload = "{}"


    def cleanup(self):
        super().cleanup()
        if self.checkpoints_enabled:
            shutil.rmtree(self.storage_prefix, ignore_errors=True)
            self.checkpoints = []
