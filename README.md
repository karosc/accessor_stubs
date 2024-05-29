# accessor_stubs

This package addresses a problem that's bothered me for a while a now. The pandas
and xarray packages both discourage subclassing their datastructures, and recommend instead to
use composition or [accessor methods](https://docs.xarray.dev/en/stable/internals/extending-xarray.html).

I really wanted to use accessor methods to add my domain specific functionality to the
xarray ecosystem, but I really really like having IDE autocomplete that works. Unfortunately the dynamic nature of accessor methods makes them incompatible with the current [language server static analysis methods](https://github.com/microsoft/pylance-release/discussions/4564).

To solve this autocomplete problem, I've created this package to create xarray type-stubs
on the fly that follow [PEP 561](https://peps.python.org/pep-0561/#partial-stub-packages). By
using the `register_dataarray_accessor()` and `register_dataset_accessor()` methods from
this package instead of xarray, your accessors will be registered with `accessor_stubs` as well as
`xarray`. Then, when you call `accessor_stubs.stubgen()`, new xarray type-stubs will be generated that
have your accessor methods listed as properties in `DataArray` and `Dataset` type stubs.

This package tracks the version of xarray that is installed and will regenerate type stubs if you
upgrade or downgrade your xarray version.

Right now, only xarray is supported, but maybe I'll add pandas in the future...

## Usage

In your python module/package, register your accessor using accessor_stubs as:

```python
# accessor.py
import xarray as xr
from accessor_stubs import register_dataset_accessor

@register_dataset_accessor("sneaky")
class SneakyAccessor:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        self._sneaky_msg = None

    @property
    def sneak(self):
        """Return a sneaky message"""
        if self._sneaky_msg is None:
            self._sneaky_msg = "👟"
        return self._sneaky_msg

```

In the top level **init**.py module of your package from where all your accessors are initialized,
run the `stubgen()` method in accessor_stubs. This will run mypy stubgen on the xarray dataset.py
and dataarray.py files in your xarray installation, then add your registered accessors to the
stub files. It's very important that you run `stubgen()` after all your accessors have been registered.

```python
# __init__.py
import accessor # the module where my accessor is created and registered
from accessor_stubs import stubgen
stubgen()

```

Now after you import your package, new xarray stubs will be generated with your accessors, and your
IDE should be able to recognize your accessors as properties of the xarray datastructure classes:

![vscode_screenshot](./doc/vscode_screenshot.png)

The generated `dataset.pyi` type-stub looks something like this:

```python
from accessor import SneakyAccessor
import datetime
import numpy as np
import pandas as pd
...

class Dataset(DataWithCoords, DatasetAggregations, DatasetArithmetic, Mapping[Hashable, 'DataArray']):
    sneaky: SneakyAccessor
    def __init__(self, data_vars: DataVars | None = None, coords: Mapping[Any, Any] | None = None, attrs: Mapping[Any, Any] | None = None) -> None: ...
    def __eq__(self, other: DsCompatible) -> Self: ...
    @classmethod
    def load_store(cls, store, decoder: Incomplete | None = None) -> Self: ...
    @property
    def variables(self) -> Frozen[Hashable, Variable]: ...
    ...
```
