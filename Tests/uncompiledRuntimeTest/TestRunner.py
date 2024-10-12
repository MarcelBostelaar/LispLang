import os

from termcolor import cprint

from LispLangInterpreter.Config import Singletons
from LispLangInterpreter.DataStructures.Classes import RuntimeEvaluationError, StackFrame
from LispLangInterpreter.Evaluator.EvaluatorCode import Eval
from LispLangInterpreter.Evaluator.SupportFunctions import toAST
from LispLangInterpreter.Evaluator.runFile import executeLeaf, start
from LispLangInterpreter.ImportHandlerSystem.LibraryClasses import Leaf
from Tests.ParseTests.TestRunner import tokenizeParse


def uncompiledRuntimeTest(catchErrors, config, folder, inputfile, expectedfile, testName):
    if catchErrors:
        try:
            runtimeTestInternal(config, folder, inputfile, expectedfile, testName)
        except:
            cprint("Exception while executing Tests '" + testName + "'", "red")
            print("")
    else:
        try:
            runtimeTestInternal(config, folder, inputfile, expectedfile, testName)
        except RuntimeEvaluationError:
            cprint("Runtime error while executing Tests '" + testName + "'", "red")
            print("")


def runtimeTestInternal(config, folder, inputfile, expectedfile, testName):
    config["path"] = folder
    config["mainFile"] = inputfile
    Singletons.runtimeConfig = config
    ranCode = start()
    config["mainFile"] = expectedfile
    Singletons.runtimeConfig = config
    evaluatedExpected = start()

    realSer = ranCode.serializeLLQ()
    expSer = evaluatedExpected.serializeLLQ()

    if realSer == expSer:
        cprint(testName + " passed", "green")
    else:
        cprint(testName + " failed, expected and actual executed code don't match", "red")
        cprint("Expected:" + expSer, "red")
        cprint("Actual  :" + realSer, "red")
        print("")
