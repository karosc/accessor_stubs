__version__ = "0.0.1"

from accessor_stubs._registrar import (
    register_dataarray_accessor,
    register_dataset_accessor,
    stubgen,
    clean,
)

__all__ = ["register_dataarray_accessor", "register_dataset_accessor", "stubgen"]
