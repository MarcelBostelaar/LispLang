import Evaluator.SupportFunctions
from Evaluator.EvaluatorCode import Eval
from Evaluator.MacroExpand import DemacroTop
from Parser.ParserCode import parseAll
from Parser.ParserCombinator import SOF_value, EOF_value
from Config.standardLibrary import outerDefaultRuntimeFrame, demacroOuterDefaultRuntimeFrame


def tokenizeParse(text):
    return parseAll.parse([SOF_value] + list(text) + [EOF_value])


def main(*argv):
    args = iter(argv)
    _ = next(args)
    command = next(args)
    if command == "help":
        print("The usage is as follows:")
        print("main.py <operation> sourceFile [targetFile]")
        print("")
        print("The following operations are available:")
        print("evaluate / eval - compiles and runs the code directly, displays the result")
        print("debug - starts the rudimentary debugger")
        print("parse - shows the parsed AST")
        print("compile / c <targetFile> - compiles the code to the specified file (currently de-macros)")
        exit(0)

    parsed = tokenizeParse(open(next(args)).read())
    if not parsed.isSucces:
        print("Could not parse: ")
        print(parsed.remaining)
        exit(1)
    if not len(parsed.remaining) == 0:
        print("Unparsable remainder:")
        print(parsed.remaining)
        exit(1)

    if command in ["parse"]:
        print(parsed.content.serializeLLQ())

    if command in ["eval", "evaluate"]:
        ast = Evaluator.SupportFunctions.toAST(parsed.content)
        demacroedCode = DemacroTop(demacroOuterDefaultRuntimeFrame.createChild(ast))
        result = Eval(outerDefaultRuntimeFrame.createChild(demacroedCode))
        print(result.serializeLLQ())

    if command in ["compile", "c"]:
        demacroedCode = DemacroTop(demacroOuterDefaultRuntimeFrame.createChild(parsed.content))
        targetFile = next(args)
        serialized = demacroedCode.serializeLLQ()
        f = open(targetFile, "w")
        f.write(serialized)
        f.close()


if __name__ == '__main__':
    main("", "eval", "testcode.lisp")
    #main(*sys.argv)
    pass


