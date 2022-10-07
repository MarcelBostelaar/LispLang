from termcolor import cprint

from Config.standardLibrary import outerDefaultRuntimeFrame
from Evaluator.Classes import RuntimeEvaluationError
from Evaluator.EvaluatorCode import Eval
from Evaluator.SupportFunctions import toAST
from main import tokenizeParse


def runtimeTest(catchErrors, inputfile, expectedfile, testName):
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
    parsedinp = tokenizeParse(inp).content
    parsedexp = tokenizeParse(exp).content


    ranCode = Eval(outerDefaultRuntimeFrame.child(toAST(parsedinp)))
    evaluatedExpected = Eval(outerDefaultRuntimeFrame.child(toAST(parsedexp)))

    realSer = ranCode.serializeLLQ()
    expSer = evaluatedExpected.serializeLLQ()

    if realSer == expSer:
        cprint(testName + " passed", "green")
    else:
        cprint(testName + " failed, expected and actual executed code don't match", "red")
        cprint("Expected:" + expSer, "red")
        cprint("Actual  :" + realSer, "red")
        print("")