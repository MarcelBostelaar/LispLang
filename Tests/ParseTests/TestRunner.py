from termcolor import cprint

from LispLangInterpreter.Parser.ParserCode import parseAll
from LispLangInterpreter.Parser.ParserCombinator import ParseError, SOF_value, EOF_value


def tokenizeParse(inp):
    return parseAll.parse([SOF_value] + list(inp) + [EOF_value])


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

def parseEqualityTest(file1, file2, testName):
    f = open(file1)
    a = f.read()
    f.close()
    f = open(file2)
    b = f.read()
    f.close()
    a = tokenizeParse(a)
    b = tokenizeParse(b)
    if not a.isSucces:
        cprint("Failure parsing file 1", "red")
        return
    if not b.isSucces:
        cprint("Failure parsing file 2", "red")
        return
    if a.content.equals(b.content):
        cprint(testName + " passed", "green")
    else:
        cprint(testName + "failed, files do not produce the same parsed result", "red")
        cprint("A:" + a.serializeLLQ(), "red")
        cprint("B:" + b.serializeLLQ(), "red")


def parseErrorTest(inputfile, errorExpected: ParseError, testName, expectedOutputFile=None):
    f = open(inputfile)
    inp = f.read()
    f.close()
    parsedinp = tokenizeParse(inp)
    if not parsedinp.isSucces:
        cprint("'" + testName + "' failed, parsing failed\n", "red")
        return

    if expectedOutputFile is not None:
        parseEqualityTest(inputfile, expectedOutputFile, testName + " - Parse result equality")

    if len(parsedinp.errors) == 1:
        err = parsedinp.errors[0]
        if err.message == errorExpected.message and err.lengthRemaining == errorExpected.lengthRemaining:
            cprint(testName + " passed", "green")
            return

    cprint("'" + testName + "' failed, errors do not match\n", "red")
    cprint(f"Expected error:", "red")
    cprint(f"{errorExpected.message} at {errorExpected.lengthRemaining}", "red")
    cprint(f"Actual error(s):", "red")
    if len(parsedinp.errors) == 0:
        cprint(f"No errors found", "red")
    for i in parsedinp.errors:
        cprint(f"{i.message} at {i.lengthRemaining}", "red")