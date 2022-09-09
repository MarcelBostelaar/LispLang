import Evaluator
from MacroExpand import DemacroTop
from Parser import parseAll
from Tokenizer import flatten, tokenizeFull
import sys

from classes import Scope


def tokenizeParse(text):
    tokenized = tokenizeFull(text, [*"/[]`,;()*<>\\ \"\t\r\n"])
    return parseAll.parse(tokenized)


def main(argv):
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
        print(parsed.content.serialize())

    if command in ["eval", "evaluate"]:
        ast = Evaluator.toAST(parsed.content)
        demacroedCode = DemacroTop(ast, Scope(None))
        result = Evaluator.Eval(demacroedCode, Scope(None))
        print(result.serialize())

    if command in ["compile", "c"]:
        ast = Evaluator.toAST(parsed.content)
        demacroedCode = DemacroTop(ast, Scope(None))
        targetFile = next(args)
        serialized = demacroedCode.serialize()
        f = open(targetFile, "w")
        f.write(serialized)
        f.close()

    # if command in ["runCompiled", "rc"]:
    #     ast = Evaluator.toAST(parsed.content)
    #     result = Evaluator.Eval(ast, Scope(None))
    #     print(result.serialize())

    if command in ["step"]:
        print("Will not be implemented via python, can be easily implemented using "
              "algebraic effects in the self hosted compiler")

main(["", "eval", "testcode.lisp"])

if __name__ == '__main__':
    #main(sys.argv)
    pass

    #read
    #parse
    #eval


    # result = tokenizeParse(open("code2.lisp").read())
    # if(result.isSucces and len(result.remaining) == 0):
    #     items = printSExpressions(result.content[1:-1])
    #     print(" ".join(items))
    # else:
    #     print("error. Remaining:\n")
    #     print(result.remaining)


