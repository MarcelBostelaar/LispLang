from functools import partial

from Config import errorMessages
from Parser.ParserCombinator import ParseError
from Tests.CompileTests.TestRunner import compileTest
from Tests.ParseTests.TestRunner import parseTest, parseErrorTest

from Tests.ParseTests import test1Expected
from Tests.RuntimeTests.TestRunner import runtimeTest

catchErrors = False

compileTest = partial(compileTest, catchErrors)
runtimeTest = partial(runtimeTest, catchErrors)

########################################################

parseTest("ParseTests/test1.lisp", test1Expected.expected, "Parse Tests 1")
parseErrorTest("ParseTests/unclosedStringTest.lisp", ParseError(1, errorMessages.unclosedString), "Unclosed string test")
parseErrorTest("ParseTests/unmatchedBracketTest.lisp", ParseError(1, errorMessages.unclosedBracket), "Unmatched Bracket Test", "ParseTests/unmatchedBracketTestCorrect.lisp")

runtimeTest("RuntimeTests/sumtest1real.lisp", "RuntimeTests/sumtest1expected.lisp", "Sum test 1")
runtimeTest("RuntimeTests/sumtest2real.lisp", "RuntimeTests/sumtest2expected.lisp", "Sum test 2")
runtimeTest("RuntimeTests/listEvaluationReal.lisp", "RuntimeTests/listEvaluationExpected.lisp", "List evaluation test")
runtimeTest("RuntimeTests/handleTest1Real.lisp", "RuntimeTests/handleTest1Expected.lisp", "Handle test")
#TODO rewrite parser combinator to allow error paths

compileTest("CompileTests/macro identity.lisp", "CompileTests/macro identity.lisp", "Macro identity")
compileTest("CompileTests/simple macro real.lisp", "CompileTests/simple macro expected.lisp", "Simplest demacro Tests")
compileTest("CompileTests/macroTailReal.lisp", "CompileTests/macroTailExpected.lisp", "Macro tail Tests")
