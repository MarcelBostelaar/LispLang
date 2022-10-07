from termcolor import cprint

from main import tokenizeParse


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
