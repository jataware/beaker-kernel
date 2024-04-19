import abc
import json
from typing import Any
import hashlib
import shutil
import uuid
from os import makedirs

from ..jupyter_kernel_proxy import ProxyKernelClient

Checkpoint = dict[str, str]

class CheckpointError(Exception):
    def __init__(self, message):
        super().__init__(message)

class JsonStateEncoder(json.JSONEncoder):
    pass

class BaseSubkernel(ProxyKernelClient, abc.ABC):
    DISPLAY_NAME: str
    SLUG: str
    KERNEL_NAME: str

    WEIGHT: int = 50  # Used for auto-sorting in drop-downs, etc. Lower weights are listed earlier.

    SERIALIZATION_EXTENSION: str = "storage"

    FETCH_STATE_CODE: str = ""

    @classmethod
    @abc.abstractmethod
    def parse_subkernel_return(cls, execution_result) -> Any:
        ...

    def __init__(self, subkernel_configuration: dict, session_id: str = None):
        self.active = True
        self.checkpoints = list[Checkpoint]
        self.storage_prefix = f"/tmp/{session_id if session_id else uuid.uuid4()}"
        makedirs(self.storage_prefix, exist_ok=True)
        super().__init__(subkernel_configuration)
    
    def update_storage_prefix(self, session_id: str):
        previous_prefix = self.storage_prefix
        self.storage_prefix = f"/tmp/{session_id}"
        shutil.move(previous_prefix, self.storage_prefix)

    def generate_handle(self, identifier: str) -> str:
        return f"{self.storage_prefix}/{identifier}.{self.SERIALIZATION_EXTENSION}"

    def store_serialization(cls, varname: str, filename: str) -> str:
        with open(filename, "rb") as file:
            chunksize = 4 * 1024 * 1024
            hash = hashlib.new("sha256")
            while chunk := file.read(chunksize):
                hash.update(chunk)
            new_filename = cls.generate_handle(hash.hexdigest())
        shutil.move(filename, new_filename)
        return new_filename

    def get_current_checkpoint(self) -> Checkpoint:
        raise NotImplementedError
        
    def load_checkpoint(self, checkpoint: Checkpoint):
        raise NotImplementedError

    def add_checkpoint(self):
        if not self.active:
            raise CheckpointError("Checkpointer is not active")
        current_checkpoint = self.get_current_checkpoint()

        checkpoint = {
            varname: self.store_serialization(filename) for
            varname, filename in current_checkpoint.items()
        }
        self.checkpoints.append(checkpoint)
    
    def rollback(self, checkpoint_index: int):
        if not self.active:
            raise CheckpointError("Checkpointer is not active")
        self.load_checkpoint(self.checkpoints[checkpoint_index])
        self.checkpoints = self.checkpoints[:checkpoint_index]

    def cleanup(self):
        self.active = False 
        shutil.rmtree(self.storage_prefix, ignore_errors=True)
        self.checkpoints = []