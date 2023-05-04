from termcolor import cprint

from LispLangInterpreter.Config.standardLibraryBuilder import outerDefaultRuntimeFrame
from LispLangInterpreter.Evaluator.Classes import RuntimeEvaluationError
from LispLangInterpreter.Evaluator.MacroExpand import DemacroTop
from LispLangInterpreter.Evaluator.runFile import tokenizeParse


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
    parsedinp = tokenizeParse(inp)
    parsedexp = tokenizeParse(exp)

    if len(parsedinp.errors) != 0:
        cprint(testName + " failed, parsing error in input", "red")
        for i in parsedinp.errors:
            cprint(f"{i.message} at {i.lengthRemaining}", "red")
        return
    if len(parsedexp.errors) != 0:
        cprint(testName + " failed, parsing error in expected output", "red")
        for i in parsedexp.errors:
            cprint(f"{i.message} at {i.lengthRemaining}", "red")
        return

    demacroedCode = DemacroTop(outerDefaultRuntimeFrame.createChild(parsedinp.content))

    realSer = demacroedCode.serializeLLQ()
    expSer = parsedexp.content.serializeLLQ()

    if realSer == expSer:
        cprint(testName + " passed", "green")
    else:
        cprint(testName + "failed, expected and actual compiled code don't match", "red")
        cprint("Expected:" + expSer, "red")
        cprint("Actual  :" + realSer, "red")
        print("")
