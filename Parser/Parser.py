from Evaluator.Classes import QuotedName, List, Char, Boolean
from ParserCombinator import MS, Any, SOF, EOF

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


allEscapedChars = escapedChar("n", "\n")  # todo complete

stringBare = MS("\"").ignore()\
    .then(
        allEscapedChars
        .OR(
            MS("\"").mustFailThenTry(Any)
        ).many(0)
    )\
    .then(MS("\"").ignore())\
    .mapResult(lambda x: [Char("".join(x))])

string = stringBare\
    .mapResult(lambda x: [Char(y) for y in list(x)])\
    .mapResult(List)


def processChar(x):
    if len(x) == 0:
        raise "Char cant have length 0"
    if len(x) == 1:
        raise "Char must have length 1"
    return Char(x)


char = MS("c").ignore().then(stringBare)\
    .mapResult(processChar)

stringChars = string.OR(char)

bools = MS("true").OR(MS("false")).mapResult(Boolean)

inlineValues = stringChars.OR(bools)  # todo numbers and other literals

"""Any non-ignorable item that isn't an opening or closing bracket"""
Atom = MS("[").OR(MS("]")).OR(SOF).OR(EOF)\
    .mustFailThenTry(
        inlineValues  # inline literals such as strings and numbers
        .OR(  # everything else that has been tokenized
            Any
            .mapResult(lambda x: [QuotedName(x[0])])
        )
    ).wrap(ignore)


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
