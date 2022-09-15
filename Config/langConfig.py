from enum import Enum


class specialFormConfig:
    def __init__(self, keyword, length):
        self.keyword = keyword
        self.length = length


def c(keyword, length):
    return specialFormConfig(keyword, length)


currentScopeKeyword = "currentScope"

class SpecialForms(Enum):
                            #callingScope is the scope from the place in which the macro was invoked to expand,
                            # so that you can call macro expand on specific code with outside scope, and macro expand
                            # on specific code with the internal macro scope, to aid in writing more hygenic macros
    macro = c("macro", 5)   #macro macroname input callingScope body
    let = c("let", 3) #let varname value
    quote = c("quote", 2) #quote value
    list = c("list", 2) #list (a b c)
    Lambda = c("lambda", 3) #lambda args body
    cond = c("cond", 4) #cond bool truepath falsepath
    ignore = c("ignore", 1) #ignore (somevalue or function)


