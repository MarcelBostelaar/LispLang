from Parser.ParserCombinator import SOF_value, EOF_value

def flatten(list_):
    return [item for sublist in list_ for item in sublist]

def removeItem(list_of_stuff, item):
    return [x for x in list_of_stuff if x is not item]


def tokenizeSingle(text, on):
    splitted = text.split(on)
    splitted = splitted
    splitted = [[on, x] for x in splitted]
    splitted = flatten(splitted)
    splitted.pop(0)
    splitted = removeItem(splitted, "")
    return splitted


def tokenize(textArray, on):
    tokenized = [tokenizeSingle(x, on) for x in textArray]
    return flatten(tokenized)


def map(f, args):
    def subFunc(value):
        for i in args:
            value = f(value, i)
        return value
    return subFunc

def tokenizeFull(text, keywordList):
    tokenized = map(tokenize, keywordList)([text])
    tokenized = [SOF_value] + tokenized + [EOF_value]
    return tokenized