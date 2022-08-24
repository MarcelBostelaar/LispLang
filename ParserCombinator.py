class parseResult:
    def __init__(self, isSucces, content, remaining):
        self.isSucces = isSucces
        self.content = content # a list of tokens
        self.remaining = remaining

    def map(self, f):
        if self.isSucces:
            self.content = f(self.content)



class Combinator:
    # f takes a function that accepts a list of tokens and returns a parseResult
    def __init__(self, f, debugMessage = None):
        self.f = f
        self.debugMessage = debugMessage

    def parse(self, tokens):
        result = self.f(tokens)
        if self.debugMessage is not None:
            print(self.debugMessage)
            if(result.isSucces):
                print("success, parsed:")
                print(result.content)
                print("remainder:")
                print(result.remaining)
                print("")
            else:
                print("failed, input:")
                print(tokens)
                print("")
        return result

    def addDebugMessage(self, message):
        return Combinator(self.f, message)

    def thenLazy(self, otherCombinator):
        def internal(tokens):
            result1 = self.parse(tokens)
            if result1.isSucces:
                combinator2 = otherCombinator()
                result2 = combinator2.parse(result1.remaining)
                if result2.isSucces:
                    return parseResult(True,
                                       result1.content + result2.content,
                                       result2.remaining)
                return result2
            return result1
        return Combinator(internal)

    def then(self, combinator):
        return self.thenLazy(lambda: combinator)

    def OR(self, otherCombinator):
        def internal(tokens):
            result1 = self.parse(tokens)
            if result1.isSucces:
                return result1

            result2 = otherCombinator.parse(tokens)
            return result2
        return Combinator(internal)

    #matched 0 or more of itself
    def many(self):
        def internal(tokens):
            accumulate = parseResult(True, [], tokens)
            result = parseResult(True, [], tokens)
            while result.isSucces:
                accumulate = parseResult(True,
                                         accumulate.content + result.content,
                                         result.remaining)
                result = self.parse(accumulate.remaining)

            return accumulate
        return Combinator(internal)

    def ignore(self):
        return self.mapResult(lambda _: [])

    def wrap(self, otherCombinator):
        return otherCombinator.then(self).then(otherCombinator)

    def mustFailThenTry(self, otherCombinator):
        def internal(tokens):
            result = self.parse(tokens)
            if result.isSucces:
                return parseResult(False, result.content, result.remaining)
            return otherCombinator.parse(tokens)
        return Combinator(internal)

    def mapResult(self, g):
        def internal(tokens):
            result = self.parse(tokens)
            result.map(g)
            return result
        return Combinator(internal)



# matchstring
def MS(specificString):
    def internal(tokens):
        if(len(tokens) > 0):
            if(tokens[0] == specificString):
                return parseResult(True, [tokens[0]], tokens[1:])
        return parseResult(False, None, tokens)
    return Combinator(internal)


def AnyFunc(tokens):
    if(len(tokens) > 0):
        return parseResult(True, [tokens[0]], tokens[1:])
    print("EOF")
    return parseResult(False, None, tokens)


Any = Combinator(AnyFunc)

SOF_value = 985743587435
EOF_value = 874595340400
SOF = MS(SOF_value)
EOF = MS(EOF_value)