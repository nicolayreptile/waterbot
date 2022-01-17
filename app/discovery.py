import logging
import os
from importlib import import_module
from pkgutil import iter_modules
from fnmatch import fnmatchcase


logger = logging.getLogger(__name__)

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


async def discovery(name_wildcard: str, *packages: str):
    packages = packages or [name for _, name, is_pkg in iter_modules([ROOT_DIR]) if is_pkg]
    for package in packages:
        path = os.path.join(ROOT_DIR, package.replace('.', '/'))
        for module_info, name, is_pkg in iter_modules([path]):
            module_path = f'{package}.{name}'
            if is_pkg:
                async for module in discovery(name_wildcard, module_path):
                    yield module
            elif fnmatchcase(name, name_wildcard):
                logger.info('Module %s imported from %s', name, package)
                yield module_path


async def import_modules(name_wildcard: str, *packages: str):
    return [import_module(module) async for module in discovery(name_wildcard, *packages)]