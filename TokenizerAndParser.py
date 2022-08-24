from Tokenizer import tokenizeFull
from classes import sExpression, Name, Value
from ParserCombinator import MS, Any, SOF, EOF

linebreaks = MS("\n").OR(MS("\r"))
whitespace = linebreaks.OR(MS("\t")).OR(MS(" "))

inlineStart = MS("/").then(MS("*"))
inlineEnd = MS("*").then(MS("/"))

inlineComment = inlineStart\
    .then(
        inlineEnd.mustFailThenTry(Any).many()
    )\
    .then(inlineEnd)

endCommentStart = MS("/").then(MS("/"))
endComment = endCommentStart \
    .then(linebreaks.mustFailThenTry(Any).many()) \
    .then(linebreaks)

ignore = whitespace.OR(inlineComment).OR(endComment).many().ignore()

def escapedChar(char, becomes):
    return MS("\\").then(MS(char)).mapResult(lambda _: [becomes])

allEscapedChars = escapedChar("n", "\n")

string = MS("\"").ignore()\
    .then(
        allEscapedChars
        .OR(
            MS("\"").mustFailThenTry(Any)
        ).many()
    )\
    .then(MS("\"").ignore())\
    .mapResult(lambda x: [Value("".join(x))])

inlineValues = string

Atom = MS("[").OR(MS("]"))\
    .mustFailThenTry(
        inlineValues.OR(
            Any
            .mapResult(lambda x: Name(x[0]))
            .mapResult(lambda x: [x]))
    ).wrap(ignore)


def pureMS(specificString):
    return MS(specificString).wrap(ignore)


def SExpressionCombinator():
    return pureMS("[") \
        .thenLazy(lambda:
                  SExpressionCombinator()
                  .OR(Atom)
                  .many()) \
        .then(pureMS("]")) \
        .mapResult(lambda x: x[1:-1])\
        .mapResult(sExpression)\
        .mapResult(lambda x: [x])


parseAll = SOF.then(SExpressionCombinator().many()).then(EOF)


def tokenizeParse(text):
    tokenized = tokenizeFull(text, [*"/[]`,;()*<>\\ \"\t\r\n"])
    return parseAll.parse(tokenized)
