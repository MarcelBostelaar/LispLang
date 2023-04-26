import importlib
from ..DataStructures.Classes import *

modules = {}

def validatePathForm(path):
    if path[0] == ".":
        raise Exception(f"Path for the to import package must be absolute, found {path} instead")


def SystemDataImporter(importData: PythonImportData, callingFrame: StackFrame):
    """
    Loads values directly from a python file or module.
    :param importData:
    :param callingFrame:
    :return:
    """
    #TODO make this into an effect handler with a macro, remove python import data and use list forms instead
    validatePathForm(importData.libraryPath)
    if importData.libraryPath in modules.keys():
        #Already imported
        pass
    else:
        importedModule = importlib.import_module(importData.libraryPath)
        modules[importData.libraryPath] = importedModule

    module = modules[importData.libraryPath]
    for x in importData.importValues:
        item = getattr(module, x[0])
        if not issubclass(Value, item):
            callingFrame.throwError(f"Imported item '{x[0]}' from library file '{importData.libraryPath}' is not an interpreter Value type.")
        callingFrame = callingFrame.addScopedRegularValue(x[1], item)
    return callingFrame

def placeholderImportFunc(pathSteps, saveAs):
    """
    Tries to load a value from a library
    :param pathSteps: List of path elements
    :param saveAs: New name to save it as
    :return:
    """
    pass


def placeholderMacroImportFunc(pathSteps, saveAs):
    """
    Tries to load a value from a library
    :param pathSteps: List of path elements
    :param saveAs: New name to save it as
    :return:
    """
    pass


def makeNormalStartingFrame():
    frame = StackFrame(StackReturnValue())
    handler = SystemHandlerFrame().addHandler("__import", SystemFunction(placeholderImportFunc, 2))
    return frame.withHandlerFrame(handler)


def makeDemacroStartingFrame():
    frame = StackFrame(StackReturnValue())
    handler = SystemHandlerFrame()\
        .addHandler("__import", SystemFunction(placeholderImportFunc, 2))\
        .addHandler("__importMacro", SystemFunction(placeholderMacroImportFunc, 2))
    return frame.withHandlerFrame(handler)
