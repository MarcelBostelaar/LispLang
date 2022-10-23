import importlib

from .Importer import modules
from ..DataStructures.Classes import SystemFunction, SystemHandlerFrame


def validatePathForm(path):
    if path[0] == ".":
        raise Exception(f"Path for the to import package must be absolute, found {path} instead")


def SystemHandlerImporter(config) -> SystemHandlerFrame:
    """
    Creates a system handler frame from a specified config.
    :param config:
    :return:
    """
    frame = SystemHandlerFrame()
    for fileImport in config:
        path = fileImport["path"]
        items = fileImport["handlers"]
        validatePathForm(path)
        if path in modules.keys():
            # Already imported
            pass
        else:
            importedModule = importlib.import_module(path)
            modules[path] = importedModule
        module = modules[path]
        for itemDescription in items:
            nameInFile = itemDescription["nameInFile"]
            exportName = itemDescription["handlesFunction"]
            value = getattr(module, nameInFile)
            if not isinstance(value, SystemFunction):
                raise Exception(f"Tried to import system function '{nameInFile}' "
                                f"for system handling, but its not a system function.")
            frame = frame.addHandler(exportName, value)
    return frame
