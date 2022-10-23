from termcolor import cprint

from Config.standardLibraryBuilder import outerDefaultRuntimeFrame
from Evaluator.Classes import RuntimeEvaluationError
from Evaluator.EvaluatorCode import Eval
from Evaluator.SupportFunctions import toAST
from main import tokenizeParse


def uncompiledRuntimeTest(catchErrors, inputfile, expectedfile, testName):
    if catchErrors:
        try:
            runtimeTestInternal(inputfile, expectedfile, testName)
        except:
            cprint("Exception while executing Tests '" + testName + "'", "red")
            print("")
    else:
        try:
            runtimeTestInternal(inputfile, expectedfile, testName)
        except RuntimeEvaluationError:
            cprint("Runtime error while executing Tests '" + testName + "'", "red")
            print("")


def runtimeTestInternal(inputfile, expectedfile, testName):
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


    ranCode = Eval(outerDefaultRuntimeFrame.createChild(toAST(parsedinp.content)))
    evaluatedExpected = Eval(outerDefaultRuntimeFrame.createChild(toAST(parsedexp.content)))

    realSer = ranCode.serializeLLQ()
    expSer = evaluatedExpected.serializeLLQ()

    if realSer == expSer:
        cprint(testName + " passed", "green")
    else:
        cprint(testName + " failed, expected and actual executed code don't match", "red")
        cprint("Expected:" + expSer, "red")
        cprint("Actual  :" + realSer, "red")
        print("")