import json
import os

from LispLangInterpreter.Config import Singletons
from LispLangInterpreter.DataStructures.Classes import StackFrame
from LispLangInterpreter.DataStructures.IErrorThrowable import ErrorCatcher
from LispLangInterpreter.ImportHandlerSystem.Handler import SystemHandlerImporter
from LispLangInterpreter.ImportHandlerSystem.PackageResolver import mapLibrary, makeAbs
from LispLangInterpreter.ImportHandlerSystem.placeholderConfigs import libraryFallbackWord, exampleConfig


def reloadConfig():
    """If is none added to allow mocking during unit tests"""
    if Singletons.runtimeConfig is None:
        Singletons.runtimeConfig = getConfig()

    Singletons.currentFileSystem = mapLibrary(Singletons.runtimeConfig)
    Singletons.MacroHandlerFrame = SystemHandlerImporter(Singletons.runtimeConfig["handledMacroEffects"])
    Singletons.MacroHandlerFrame = SystemHandlerImporter(Singletons.runtimeConfig["handledRuntimeEffects"])


def start():
    reloadConfig()
    errorHandler = ErrorCatcher()
    startFile = Singletons.currentFileSystem.find(errorHandler, [Singletons.runtimeConfig["mainFile"]])
    startFile.execute(errorHandler) #no error would be thrown in this initial state so no stackframe is neccecary
    return startFile.data #data is the return value


def executeLeaf(leaf):
    reloadConfig()
    errorhandler = ErrorCatcher()
    leaf.execute(errorhandler)  # no error would be thrown in this initial state so no stackframe is neccecary
    return leaf.data  # data is the return value


def getConfig():
    if not os.path.isfile(configPath):
        config = exampleConfig
        frozen = json.dumps(exampleConfig, indent=4)
        f = open(configPath, encoding="utf8", mode="w")
        f.write(frozen)
        f.close()
        raise Exception("Config wasn't found, fill config first")

    f = open(configPath, encoding="utf8")
    x = f.read()
    return json.loads(x)

configPath = "config.json"