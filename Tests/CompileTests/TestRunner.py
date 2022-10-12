from termcolor import cprint

from Config.standardLibrary import outerDefaultRuntimeFrame
from Evaluator.Classes import RuntimeEvaluationError
from Evaluator.MacroExpand import DemacroTop
from main import tokenizeParse


def compileTest(catchErrors, inputfile, expectedfile, testName):
    if catchErrors:
        try:
            compileTestInternal(inputfile, expectedfile, testName)
        except:
            cprint("Exception while executing Tests '" + testName + "'", "red")
            print("")
    else:
        try:
            compileTestInternal(inputfile, expectedfile, testName)
        except RuntimeEvaluationError:
            cprint("Runtime error while executing Tests '" + testName + "'", "red")
            print("")


def compileTestInternal(inputfile, expectedfile, testName):
    f = open(inputfile)
    inp = f.read()
    f.close()
    f = open(expectedfile)
    exp = f.read()
    f.close()
    parsedinp = tokenizeParse(inp).content
    parsedexp = tokenizeParse(exp).content


    demacroedCode = DemacroTop(outerDefaultRuntimeFrame.createChild(parsedinp))

    realSer = demacroedCode.serializeLLQ()
    expSer = parsedexp.serializeLLQ()

    if realSer == expSer:
        cprint(testName + " passed", "green")
    else:
        cprint(testName + "failed, expected and actual compiled code don't match", "red")
        cprint("Expected:" + expSer, "red")
        cprint("Actual  :" + realSer, "red")
        print("")
