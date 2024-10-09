from functools import partial
import os
print("Current Working Directory:", os.getcwd())
from LispLangInterpreter.Config import errorMessages
from LispLangInterpreter.ImportHandlerSystem.placeholderConfigs import exampleConfig
from LispLangInterpreter.Parser.ParserCombinator import ParseError
# from Tests.CompileTests.TestRunner import compileTest
from Tests.ParseTests.TestRunner import parseTest, parseErrorTest
#
from Tests.ParseTests import test1Expected, EOFCommentExpected
from Tests.uncompiledRuntimeTest.TestRunner import uncompiledRuntimeTest
import os

# from Tests.uncompiledRuntimeTest.TestRunner import uncompiledRuntimeTest
#
# catchErrors = False
#
# compileTest = partial(compileTest, catchErrors)
# uncompiledRuntimeTest = partial(uncompiledRuntimeTest, catchErrors)

########################################################

parseTest("Tests/ParseTests/test1.lisp", test1Expected.expected, "Parse Tests 1")
parseTest("Tests/ParseTests/EOFComment.lisp", EOFCommentExpected.expected, "EOF comment")
parseErrorTest("Tests/ParseTests/unclosedStringTest.lisp", ParseError(1, errorMessages.unclosedString), "Unclosed string test")
parseErrorTest("Tests/ParseTests/unmatchedBracketTest.lisp", ParseError(1, errorMessages.unclosedBracket), "Unmatched Bracket Test", "Tests/ParseTests/unmatchedBracketTestCorrect.lisp")

uncompiledRuntimeTest(False, exampleConfig, "Tests/uncompiledRuntimeTest/sumtest1real.lisp", "Tests/uncompiledRuntimeTest/sumtest1expected.lisp", "Sum test 1")
# uncompiledRuntimeTest("uncompiledRuntimeTest/sumtest2real.lisp", "uncompiledRuntimeTest/sumtest2expected.lisp", "Sum test 2")
# uncompiledRuntimeTest("uncompiledRuntimeTest/listEvaluationReal.lisp", "uncompiledRuntimeTest/listEvaluationExpected.lisp", "List evaluation test")
# uncompiledRuntimeTest("uncompiledRuntimeTest/handleTest1Real.lisp", "uncompiledRuntimeTest/handleTest1Expected.lisp", "Handle test")
#
# compileTest("CompileTests/macro identity.lisp", "CompileTests/macro identity.lisp", "Macro identity")
# compileTest("CompileTests/simple macro real.lisp", "CompileTests/simple macro expected.lisp", "Simplest demacro Tests")
# compileTest("CompileTests/macroTailReal.lisp", "CompileTests/macroTailExpected.lisp", "Macro tail Tests")
