from enum import Enum


class specialFormConfig:
    def __init__(self, keyword, length):
        self.keyword = keyword
        self.length = length


def c(keyword, length):
    return specialFormConfig(keyword, length)


class SpecialForms(Enum):
    macro = c("macro", 4) #macro macroname input body
    let = c("let", 3) #let varname value
    quote = c("quote", 2) #quote value
    Lambda = c("lambda", 3) #lambda args body
    cond = c("cond", 4) #cond bool truepath falsepath


