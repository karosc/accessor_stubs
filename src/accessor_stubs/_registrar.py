from __future__ import annotations

import importlib
import os
import pathlib
import tempfile
from textwrap import dedent, indent
from typing import Callable, Type, Any, TypeVar
import xarray as _xr
import subprocess
import json

_xstubs = importlib.import_module("xarray-stubs")
T = TypeVar("T", bound=Type)

__HERE__ = pathlib.Path(__file__).parent
_VERSION_FILE = __HERE__ / "versions.json"

__XARRAY__ = pathlib.Path(_xr.__file__).parent
_DATAARRAY_PATH = __XARRAY__ / "core" / "dataarray.py"
_DATASET_PATH = __XARRAY__ / "core" / "dataset.py"

_DATAARRAY_IMPORTS: dict[str, Type] = {}
_DATASET_IMPORTS: dict[str, Type] = {}


_XR_STUBS_DIR = pathlib.Path(_xstubs.__path__[0])
_DATAARRAY_STUB_PATH = _XR_STUBS_DIR / "core" / "dataarray.pyi"
_DATASET_STUB_PATH = _XR_STUBS_DIR / "core" / "dataset.pyi"


# Custom alias decorator
def register_dataarray_accessor(name: str) -> Callable[[T], T]:
    """Register a custom accessor on xarray.DataArray objects.

    Parameters
    ----------
    name : str
        Name under which the accessor should be registered. A warning is issued
        if this name conflicts with a preexisting attribute.

    See Also
    --------
    register_dataset_accessor
    """

    def custom_da_decorator(accessor: T) -> T:
        #####
        _DATAARRAY_IMPORTS[name] = accessor
        #####
        # Call the original decorator
        original_decorator = _xr.register_dataarray_accessor(name)
        return original_decorator(accessor)

    return custom_da_decorator


def register_dataset_accessor(name: str) -> Callable[[T], T]:
    """Register a custom property on xarray.Dataset objects.

    Parameters
    ----------
    name : str
        Name under which the accessor should be registered. A warning is issued
        if this name conflicts with a preexisting attribute.

    Examples
    --------
    In your library code:

    >>> @xr.register_dataset_accessor("geo")
    ... class GeoAccessor:
    ...     def __init__(self, xarray_obj):
    ...         self._obj = xarray_obj
    ...
    ...     @property
    ...     def center(self):
    ...         # return the geographic center point of this dataset
    ...         lon = self._obj.latitude
    ...         lat = self._obj.longitude
    ...         return (float(lon.mean()), float(lat.mean()))
    ...
    ...     def plot(self):
    ...         # plot this array's data on a map, e.g., using Cartopy
    ...         pass
    ...

    Back in an interactive IPython session:

    >>> ds = xr.Dataset(
    ...     {"longitude": np.linspace(0, 10), "latitude": np.linspace(0, 20)}
    ... )
    >>> ds.geo.center
    (10.0, 5.0)
    >>> ds.geo.plot()  # plots data on a map

    See Also
    --------
    register_dataarray_accessor
    """

    def custom_ds_decorator(accessor: T) -> T:
        #####
        # do stuff here
        _DATASET_IMPORTS[name] = accessor

        #####
        # Call the original decorator
        original_decorator = _xr.register_dataset_accessor(name)
        return original_decorator(accessor)

    return custom_ds_decorator


def _generate_xr_stub_code() -> None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = pathlib.Path(tmpdirname)
        cmd = f"stubgen {_DATAARRAY_PATH} {_DATASET_PATH} --no-analysis -o {str(tmpdirname)}"
        _ = subprocess.run(cmd.split(), capture_output=True)

        # mutate da
        imports, hints = _get_accessor_stub_code(_DATAARRAY_IMPORTS)
        stub = tmpdir / "xarray" / "core" / "dataarray.pyi"
        da_stub = _update_stub(imports, hints, stub, "class DataArray")
        with open(_DATAARRAY_STUB_PATH, "w") as f:
            f.write(da_stub)

        # mutate ds
        imports, hints = _get_accessor_stub_code(_DATASET_IMPORTS)
        stub = tmpdir / "xarray" / "core" / "dataset.pyi"
        ds_stub = _update_stub(imports, hints, stub, "class Dataset")
        with open(_DATASET_STUB_PATH, "w") as f:
            f.write(ds_stub)


def _get_accessor_stub_code(imports: dict) -> tuple[str, str]:
    """Based on registered accessors, create the text additons to the stubfiles"""
    import_str = ""
    typehints = ""

    for name, accessor in imports.items():
        if accessor.__module__ == "__main__":
            raise ValueError(
                "accessor_stubs is not meant to be used from a `__main__` module. "
                f"The {accessor.__qualname__} accessor was created in the __main__ module"
                "Move your accessor methods into a module in your python path and rerun"
            )
        import_str += f"from {accessor.__module__} import {accessor.__qualname__}\n"
        typehints += f"{name}: {accessor.__qualname__}\n"
    return import_str, typehints


def _update_stub(imports: str, hints: str, stub: pathlib.Path, search_string: str) -> str:
    outstr = imports
    inclass = False
    with open(stub, "r") as f:
        for line in f.readlines():
            if inclass:
                outstr += indent(hints, "    ")
                inclass = False
            outstr += line
            if search_string in line:
                inclass = True
    return outstr


def clean() -> None:
    for file in [_DATAARRAY_STUB_PATH, _DATASET_STUB_PATH]:
        if file.exists():
            os.remove(file)
    _update_version(
        {
            "xarray": "0.0.0",
            # "pandas": "0.0.0",
        }
    )


def stubs_up_to_date(package_name: str, expected_version: str):
    try:
        version = importlib.metadata.version(package_name)
        if version == expected_version:
            return True
        else:
            return version
    except importlib.metadata.PackageNotFoundError:
        return None


def _update_version(version_dict) -> None:
    with open(_VERSION_FILE, "w") as f:
        json.dump(
            version_dict,
            f,
        )


def stubgen() -> None:
    _stubgen_funcs = {"xarray": _generate_xr_stub_code}
    with open(_VERSION_FILE, "r") as f:
        vers = json.load(f)

    for package in ["xarray"]:
        if (version := stubs_up_to_date(package, vers[package])) is True:
            break
        else:
            _stubgen_funcs[package]()
            vers[package] = version
            _update_version(vers)
