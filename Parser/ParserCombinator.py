class parseResult:
    def __init__(self, isSucces, content, remaining):
        self.isSucces = isSucces
        self.content = content # a list of tokens
        self.remaining = remaining

    def map(self, f):
        if self.isSucces:
            return parseResult(True, f(self.content), self.remaining)
        return self


class Combinator:
    """f takes a function that accepts a list of tokens and returns a parseResult"""
    def __init__(self, f, debugMessage=None):
        self.f = f
        self.debugMessage = debugMessage

    def parse(self, tokens):
        if self.debugMessage is None:
            return self.f(tokens)
        else:
            try:
                breakpoint = 10
                result = self.f(tokens)
                print(self.debugMessage)
                if result.isSucces:
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
            except Exception as e:
                print("Exception while parsing")
                print(self.debugMessage)
                raise e

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

    def many(self, minimum, maximum=None):
        """Makes the parser combinator match N or more of itself"""
        def internal(tokens):
            accumulate = parseResult(True, [], tokens)
            result = parseResult(True, [], tokens)
            totalMatched = -1
            while result.isSucces:
                totalMatched += 1
                accumulate = parseResult(True,
                                         accumulate.content + result.content,
                                         result.remaining)
                result = self.parse(accumulate.remaining)
                if maximum is not None:
                    if totalMatched >= maximum:
                        return accumulate
            if totalMatched >= minimum:
                return accumulate
            else:
                return parseResult(False, accumulate.content, accumulate.remaining)
        return Combinator(internal)

    def ignore(self):
        return self.mapResult(lambda _: [])

    def wrap(self, otherCombinator):
        return otherCombinator.then(self).then(otherCombinator)

    def mustFailThenTry(self, otherCombinator):
        """Executes otherCombinator if this combinator fails to parse"""
        def internal(tokens):
            result = self.parse(tokens)
            if result.isSucces:
                return parseResult(False, result.content, result.remaining)
            return otherCombinator.parse(tokens)
        return Combinator(internal)

    def mapResult(self, g):
        def internal(tokens):
            result = self.parse(tokens)
            return result.map(g)
        return Combinator(internal)


def reduceOR(combinators):
    reduced = combinators[0]
    combinators = combinators[1:]
    while len(combinators) != 0:
        reduced = reduced.OR(combinators[0])
        combinators = combinators[1:]
    return reduced


def reduceTHEN(combinators):
    reduced = combinators[0]
    combinators = combinators[1:]
    while len(combinators) != 0:
        reduced = reduced.then(combinators[0])
        combinators = combinators[1:]
    return reduced


def MC(char):
    """Match char"""
    def internal(tokens):
        if len(tokens) > 0:
            if tokens[0] == char:
                return parseResult(True, [tokens[0]], tokens[1:])
        return parseResult(False, None, tokens)
    comb = Combinator(internal)
    return comb


def ConcatStrings(items):
    return "".join(items)


def MS(specificString):
    """Match string"""
    return reduceTHEN([MC(x) for x in list(specificString)]).mapResult(ConcatStrings)


def AnyOfMS(*specificStrings):
    return reduceOR([MS(x) for x in specificStrings])


def AnyFunc(tokens):
    if len(tokens) > 0:
        return parseResult(True, [tokens[0]], tokens[1:])
    # EOF
    return parseResult(False, None, tokens)


Any = Combinator(AnyFunc)

SOF_value = 985743587435
EOF_value = 874595340400
SOF = MC(SOF_value)
EOF = MC(EOF_value)
