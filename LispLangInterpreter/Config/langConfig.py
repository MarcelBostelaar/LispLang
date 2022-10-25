from enum import Enum


class specialFormConfig:
    def __init__(self, keyword, length):
        self.keyword = keyword
        self.length = length


def c(keyword, length):
    return specialFormConfig(keyword, length)


extension = "lisp"
lispPackageFile = "package"

currentScopeKeyword = "currentScope"
continueKeyword = "continue"
stopKeyword = "stop"
unitKeyword = "unit"

reservedWords = [currentScopeKeyword, "true", "false", unitKeyword]

# all the symbols parsed individually as atom names for enable more specialized syntax

separateSymbols = "`,;(){}*/<>@~+-%\\"

class SpecialForms(Enum):
                            #callingScope is the scope from the place in which the macro was invoked to expand,
                            # so that you can call macro expand on specific code with outside scope, and macro expand
                            # on specific code with the internal macro scope, to aid in writing more hygenic macros
    macro = c("macro", 5)   #macro macroname callingScope input body
    let = c("let", 3) #let varname value
    quote = c("quote", 2) #quote value
    list = c("list", 2) #list (a b c)
    Lambda = c("lambda", 3) #lambda args body
    cond = c("cond", 4) #cond bool truepath falsepath
    ignore = c("ignore", 2) #ignore (somevalue or function)
    handle = c("handle", 4) #handle effectfullCode '[[handlername @handler1] [handlername2 @handler2] etc]] stateSeed

