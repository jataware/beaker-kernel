from beaker_kernel.lib.autodiscovery import autodiscover
from .base import BeakerSubkernel

def autodiscover_subkernels():
    return autodiscover("subkernels")
