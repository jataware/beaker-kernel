import abc
import hashlib
import shutil
from os import makedirs
from typing import Any


Checkpoint = dict[str, str]

class CheckpointError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Checkpointer(abc.ABC):
    SERIALIZATION_EXTENSION: str = "storage"

    def __init__(self, session_id: str):
        self.active = True
        self.checkpoints = list[Checkpoint]
        self.storage_prefix = f"/tmp/{self.session_id}"
        makedirs(self.storage_prefix, exist_ok=True)

    def generate_handle(self, identifier) -> str:
        return f"/tmp/{self.session_id}/{identifier}.{self.SERIALIZATION_EXTENSION}"

    def store_serialization(cls, varname: str, filename: str) -> str:
        with open(filename, "rb") as file:
            chunksize = 4 * 1024 * 1024
            hash = hashlib.new("sha256")
            while chunk := file.read(chunksize):
                hash.update(chunk)
            new_filename = cls.generate_handle(hash.hexdigest())
        shutil.copy(filename, new_filename)
        return new_filename

    @abc.abstractmethod
    def get_current_checkpoint(self) -> Checkpoint:
        ...
        
    @abc.abstractmethod
    def load_checkpoint(self, checkpoint: Checkpoint):
        ...

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

    def cleanup(self):
        self.active = False 
        shutil.rmtree(f"/tmp/{self.session_id}", ignore_errors=True)
        self.checkpoints = []
