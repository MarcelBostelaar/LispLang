from Evaluator.MacroExpand import DemacroTop
from main import tokenizeParse
from termcolor import cprint

from Config.standardLibrary import standardScope

catchErrors = False


def compileTest(inputfile, expectedfile, testName):
    if catchErrors:
        try:
            compileTestInternal(inputfile, expectedfile, testName)
        except:
            cprint("Exception while executing test '" + testName + "'", "red")
            print("")
    else:
        compileTestInternal(inputfile, expectedfile, testName)


def compileTestInternal(inputfile, expectedfile, testName):
    f = open(inputfile)
    inp = f.read()
    f.close()
    f = open(expectedfile)
    exp = f.read()
    f.close()
    parsedinp = tokenizeParse(inp).content
    parsedexp = tokenizeParse(exp).content


    demacroedCode = DemacroTop(parsedinp, standardScope)

    realSer = demacroedCode.serialize()
    expSer = parsedexp.serialize()

    if realSer == expSer:
        cprint(testName + " passed", "green")
    else:
        cprint(testName + "failed, expected and actual compiled code don't match", "red")
        cprint("Expected:" + expSer, "red")
        cprint("Actual  :" + realSer, "red")
        print("")


compileTest("CompileTests/macro identity.lisp", "CompileTests/macro identity.lisp", "Macro identity")
compileTest("CompileTests/simple macro real.lisp", "CompileTests/simple macro expected.lisp", "Simplest demacro test")
compileTest("CompileTests/macroTailReal.lisp", "CompileTests/macroTailExpected.lisp", "Macro tail test")
