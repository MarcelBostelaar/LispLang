from Config.langConfig import separateSymbols
from Evaluator.Classes import QuotedName, List, Char, Boolean, Number
from ParserCombinator import MS, Any, SOF, EOF, reduce, AnyOfMS, ConcatStrings, MC

linebreaks = MS("\n").OR(MS("\r"))
whitespace = linebreaks.OR(MS("\t")).OR(MS(" "))

inlineStart = MS("/").then(MS("*"))
inlineEnd = MS("*").then(MS("/"))

inlineComment = inlineStart\
    .then(
        inlineEnd.mustFailThenTry(Any).many(0)
    )\
    .then(inlineEnd)

endCommentStart = MS("/").then(MS("/"))
endComment = endCommentStart \
    .then(linebreaks.mustFailThenTry(Any).many(0)) \
    .then(linebreaks)

ignore = whitespace.OR(inlineComment).OR(endComment).many(0).ignore()


def escapedChar(char, becomes):
    return MS("\\").then(MS(char)).mapResult(lambda _: [becomes])


def escapedChars(*pairs):
    return reduce([escapedChar(x[0], x[1]) for x in pairs])


allEscapedChars = escapedChars(["n", "\n"], ["t", "\t"], ["r", "\r"], ['"', '"'], ["'", "'"])


def stringBase(min, max):
    """A standard string base matcher with a minimum and maximum length (inclusive)"""
    return MS("\"").ignore()\
        .then(
            allEscapedChars
            .OR(
                MS("\"").mustFailThenTry(Any)
            ).many(min, max)
        )\
        .then(MS("\"").ignore())\
        .mapResult(ConcatStrings)


string = stringBase(0, None)\
    .mapResult(lambda x: [Char(y) for y in list(x)])\
    .mapResult(List)

char = MC("c").ignore().then(stringBase(1, 1)).mapResult(Char)

stringChars = string.OR(char)

bools = MS("true").OR(MS("false")).mapResult(Boolean)

num0to9 = AnyOfMS(list("1234567890"))
num1to9 = AnyOfMS(list("123456789"))
positiveIntegers = num1to9.then(num0to9.many(0))
negativeIntegers = MC("-").then(positiveIntegers)
zero = MC("0")
positiveDecimals = zero.OR(positiveIntegers).then(MC(".")).then(num0to9.many(1))
negativeDecimals = MC("-").then(positiveDecimals)
allIntegers = positiveIntegers.OR(negativeIntegers).OR(zero)\
    .mapResult(ConcatStrings)\
    .mapResult(lambda x: x + ".0")
allDecimals = positiveDecimals.OR(negativeDecimals).mapResult(ConcatStrings)

allNumbers = allIntegers.OR(allDecimals).mapResult(float).mapResult(Number).wrap(ignore)

inlineValues = stringChars.OR(bools).OR(allNumbers)

separateItems = AnyOfMS(list(separateSymbols)).mapResult(lambda x: [QuotedName(x[0])])
atozAndUnder = AnyOfMS(list(string.ascii_lowercase + string.ascii_uppercase + "_"))
alphanumeric = num0to9.OR(atozAndUnder).many(1).mapResult(lambda x: [QuotedName(x[0])])
Atom = inlineValues.OR(alphanumeric).OR(separateItems).wrap(ignore)


def pureMS(specificString):
    return MS(specificString).wrap(ignore)


def ProgramContent():
    """A series of atoms and lists"""
    return Atom.OR(BracketedContent())\
        .wrap(ignore)\
        .many(1)


def BracketedContent():
    """Parses a series of atoms/lists inside brackets into a new list"""
    return pureMS("[") \
        .thenLazy(ProgramContent)\
        .then(pureMS("]")) \
        .mapResult(lambda x: x[1:-1]) \
        .mapResult(List) \
        .mapResult(lambda x: [x])


parseAll = SOF.then(ProgramContent()).then(EOF).mapResult(lambda x: List(x[1:-1]))
