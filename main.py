from Parser import parseAll
from Tokenizer import flatten, tokenizeFull

##if else is lazy
#macro is lazy
#rest is not lazy

from TokenizerAndParser import *
from classes import Scope, Lambda, sExpression


def tokenizeParse(text):
    tokenized = tokenizeFull(text, [*"/[]`,;()*<>\\ \"\t\r\n"])
    return parseAll.parse(tokenized)

def printSExpressions(expressions):
    if type(expressions) is list:
        return flatten(flatten([[printSExpressions(x), "\n"] for x in expressions]))
    elif expressions.issExpression:
        return ["("] + flatten([printSExpressions(x) for x in expressions.children]) + [")"]
    else:
        return [expressions.toString()]

if __name__ == '__main__':
    result = tokenizeParse(open("code2.lisp").read())
    if(result.isSucces and len(result.remaining) == 0):
        items = printSExpressions(result.content[1:-1])
        print(" ".join(items))
    else:
        print("error. Remaining:\n")
        print(result.remaining)


