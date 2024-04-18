import abc
import subprocess
from typing import Any


Checkpoint = dict[str, str]


class Checkpointer(abc.ABC):
    SERIALIZATION_EXTENSION: str = "storage"

    def __init__(self):
        checkpoints = list[Checkpoint]

    @classmethod
    def generate_handle(cls, varname: str, identifier: str = "current") -> str:
        return f"/tmp/{varname}-{identifier}.{cls.SERIALIZATION_EXTENSION}"

    @classmethod
    def store_serialization(cls, varname: str, filename: str) -> str:
        hash = subprocess.run(f"cat {filename} | sha256sum")
        new_filename = cls.generate_handle(varname, hash)
        subprocess.run(["mv", filename, new_filename])
        return new_filename

    @abc.abstractmethod
    def get_current_checkpoint(self) -> Checkpoint:
        ...
        
    @abc.abstractmethod
    def load_checkpoint(self, checkpoint: Checkpoint):
        ...

    def add_checkpoint(self):
        current_checkpoint = self.get_current_checkpoint()

        checkpoint = {
            varname: self.__class__.store_serialization(varname, filename) for
            varname, filename in current_checkpoint.items()
        }
        self.checkpoints.append(checkpoint)
