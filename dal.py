#!/usr/bin/env python3
'''
A helper script to provide backwards compatibility for pre-PIP package structure. Eventually will be removed altogether.
'''

from pathlib import Path
src = Path(__file__).absolute().parent / 'src'
NAME = min(src.glob('*/*.py')).parent.name # package name (e.g. rexport/hypexport etc)


import warnings
warnings.warn(f'This script is DEPRECATED. Please install the package directly (see https://github.com/karlicoss/{NAME}#setting-up)')


import sys
sys.path.insert(0, str(src))


module_name = Path(__file__).stem # export/dal
mod = f'{NAME}.{module_name}'

# unload previously loaded DAL module (i.e. this file)
if NAME in sys.modules: del sys.modules[NAME]
if mod  in sys.modules: del sys.modules[mod ]

from contextlib import contextmanager
@contextmanager
def handle_submodule_error():
    # todo this might also be useful in the actual dal/export files.. not sure
    try:
        yield
    except ImportError as e:
        import logging
        logging.critical(f"[{__file__}]: Error while importing {mod}. Make sure you've used 'git clone --recursive' or 'git pull && git submodule update --init'.")
        raise e

# see https://stackoverflow.com/questions/43059267/how-to-do-from-module-import-using-importlib
from importlib import import_module
with handle_submodule_error():
    dal = import_module(mod)
names = [x for x in dal.__dict__ if not x.startswith("_")]
globals().update({k: getattr(dal, k) for k in names})


if __name__ == '__main__':
    with handle_submodule_error():
        main() # type: ignore
