from LispLangInterpreter.Evaluator.runFile import getConfig, start
from LispLangInterpreter.ImportHandlerSystem.Handler import SystemHandlerImporter
from LispLangInterpreter.ImportHandlerSystem.PackageResolver import mapLibrary, makeAbs
from LispLangInterpreter.ImportHandlerSystem.placeholderConfigs import libraryFallbackWord
from LispLangInterpreter.DataStructures.Classes import StackFrame
from LispLangInterpreter.Evaluator.EvaluatorCode import Eval
from LispLangInterpreter.Evaluator.MacroExpand import DemacroTop
from LispLangInterpreter.Evaluator.SupportFunctions import toAST


def main(*argv):
    config = getConfig()

    structure = mapLibrary(makeAbs(config["sourceFolder"]), config[libraryFallbackWord])

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

    parsed = None#tokenizeParse(open(next(args)).read())
    raise NotImplementedError()
    if not parsed.isSucces:
        print("Could not parse: ")
        print(parsed.remaining)
        exit(1)
    if not len(parsed.remaining) == 0:
        print("Unparsable remainder:")
        print(parsed.remaining)
        exit(1)

    if command in ["parse"]:
        # print(parsed.content.serializeLLQ())
        pass

    if command in ["eval", "evaluate"]:
        ast = toAST(parsed.content)
        #load source tree
        #put source tree into stackframe
        demacroedCode = DemacroTop(StackFrame(ast).withHandlerFrame(SystemHandlerImporter(config["handledMacroEffects"])))
        result = Eval(StackFrame(demacroedCode).withHandlerFrame(SystemHandlerImporter(config["handledRuntimeEffects"])))
        print(result.serializeLLQ())

    if command in ["compile", "c"]:
        # ast = toAST(parsed.content)
        # demacroedCode = DemacroTop(StackFrame(ast).withHandlerFrame(SystemHandlerImporter(config["handledMacroEffects"])))
        # targetFile = next(args)
        # serialized = demacroedCode.serializeLLQ()
        # f = open(targetFile, "w")
        # f.write(serialized)
        # f.close()
        pass


if __name__ == '__main__':
    # main("", "eval", "testcode.lisp")
    #main(*sys.argv)
    data = start()
    print(data.serializeLLQ())
    pass


