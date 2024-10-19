from functools import partial
import json
import os

from LispLangInterpreter.Evaluator.runFile import getConfig
print("Current Working Directory:", os.getcwd())
from LispLangInterpreter.Config import Singletons, errorMessages
from LispLangInterpreter.ImportHandlerSystem.placeholderConfigs import exampleConfig
from LispLangInterpreter.Parser.ParserCombinator import ParseError
# from Tests.CompileTests.TestRunner import compileTest
from Tests.ParseTests.TestRunner import parseTest, parseErrorTest
#
from Tests.ParseTests import test1Expected, EOFCommentExpected
from Tests.runtimeTests.TestRunner import runtimeTest
import os

testConfig = json.loads(open("Tests/testconfig.json", encoding="utf8").read())

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

runtimeTest(False, testConfig, "Tests/runtimeTests", "sumtest1real", "sumtest1expected", "Sum test 1")
runtimeTest(False, testConfig, "Tests/runtimeTests", "sumtest2real", "sumtest2expected", "Sum test 2")
runtimeTest(False, testConfig, "Tests/runtimeTests", "listEvaluationReal", "listEvaluationExpected", "List evaluation test")
runtimeTest(False, testConfig, "Tests/runtimeTests", "handleTest1Real", "handleTest1Expected", "Handle test")

Singletons.debug = True
runtimeTest(False, testConfig, "Tests/runtimeTests", "macroIdentityReal", "macroIdentityExpected", "Identity macro test")
# runtimeTest(False, testConfig, "Tests/runtimeTests", "handleTest1Real", "handleTest1Expected", "Handle test")

# compileTest("CompileTests/simple macro real.lisp", "CompileTests/simple macro expected.lisp", "Simplest demacro Tests")
# compileTest("CompileTests/macroTailReal.lisp", "CompileTests/macroTailExpected.lisp", "Macro tail Tests")
