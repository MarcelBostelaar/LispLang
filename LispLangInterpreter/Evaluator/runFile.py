import json
import os

from LispLangInterpreter.Config import Singletons
from LispLangInterpreter.DataStructures.Classes import StackFrame
from LispLangInterpreter.ImportHandlerSystem.Handler import SystemHandlerImporter
from LispLangInterpreter.ImportHandlerSystem.PackageResolver import mapLibrary, makeAbs
from LispLangInterpreter.ImportHandlerSystem.placeholderConfigs import libraryFallbackWord, exampleConfig, \
    sourceFolderWord


def start():
    Singletons.runtimeConfig = getConfig()

    Singletons.currentFileSystem = mapLibrary(makeAbs(Singletons.runtimeConfig[sourceFolderWord]), Singletons.runtimeConfig[libraryFallbackWord])
    startFile= Singletons.currentFileSystem.getSearchable([Singletons.runtimeConfig["mainFile"]])

    Singletons.MacroHandlerFrame = SystemHandlerImporter(Singletons.runtimeConfig["handledMacroEffects"])
    Singletons.MacroHandlerFrame = SystemHandlerImporter(Singletons.runtimeConfig["handledRuntimeEffects"])
    startFile.execute(None) #no error would be thrown in this initial state so no stackframe is neccecary
    print(startFile.data.serializeLLQ()) #data is the return value


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