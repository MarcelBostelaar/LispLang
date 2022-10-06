from Evaluator.Classes import RuntimeEvaluationError
from Evaluator.MacroExpand import DemacroTop
from main import tokenizeParse
from termcolor import cprint

from Config.standardLibrary import outerDefaultRuntimeFrame
from Tests.ParseTests import test1Expected

catchErrors = False


def compileTest(inputfile, expectedfile, testName):
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


    demacroedCode = DemacroTop(outerDefaultRuntimeFrame.child(parsedinp))

    realSer = demacroedCode.serializeLLQ()
    expSer = parsedexp.serializeLLQ()

    if realSer == expSer:
        cprint(testName + " passed", "green")
    else:
        cprint(testName + "failed, expected and actual compiled code don't match", "red")
        cprint("Expected:" + expSer, "red")
        cprint("Actual  :" + realSer, "red")
        print("")


def parseTest(inputfile, outputExpected, testName):
    f = open(inputfile)
    inp = f.read()
    f.close()
    parsedinp = tokenizeParse(inp)
    if not parsedinp.isSucces:
        cprint("'" + testName + "' failed, parsing failed\n", "red")
        return
    if not parsedinp.content.equals(outputExpected):
        cprint(testName + "failed, expected and parsed value dont match", "red")
        cprint("Expected:" + outputExpected.serializeLLQ(), "red")
        cprint("Actual  :" + parsedinp.content.serializeLLQ(), "red")
        print("")
    else:
        cprint(testName + " passed", "green")


parseTest("ParseTests/test1.lisp", test1Expected.expected, "Parse Tests 1")

compileTest("CompileTests/macro identity.lisp", "CompileTests/macro identity.lisp", "Macro identity")
compileTest("CompileTests/simple macro real.lisp", "CompileTests/simple macro expected.lisp", "Simplest demacro Tests")
compileTest("CompileTests/macroTailReal.lisp", "CompileTests/macroTailExpected.lisp", "Macro tail Tests")
