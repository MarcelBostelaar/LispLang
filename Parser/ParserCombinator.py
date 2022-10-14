from __future__ import annotations

class parseResult:
    def __init__(self, isSucces, content, remaining, errors):
        self.isSucces = isSucces
        self.content = content # a list of tokens
        self.remaining = remaining
        self.errors = errors

    def map(self, f):
        if self.isSucces:
            return parseResult(True, f(self.content), self.remaining, self.errors)
        return self


class ParseError:
    def __init__(self, lengthRemaining: int, errorMessage):
        self.lengthRemaining = lengthRemaining
        self.message = errorMessage


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
                    print("Success, parsed:")
                    print(result.content)
                    if len(result.errors) > 0:
                        print("Errors:")
                        print("\n".join([x.message for x in result.errors]))
                    print("Remainder:")
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

    def addDebugMessage(self, message) -> Combinator:
        return Combinator(self.f, message)

    def thenLazy(self, otherCombinator) -> Combinator:
        def internal(tokens):
            result1 = self.parse(tokens)
            if result1.isSucces:
                combinator2 = otherCombinator()
                result2 = combinator2.parse(result1.remaining)
                if result2.isSucces:
                    return parseResult(True,
                                       result1.content + result2.content,
                                       result2.remaining, result1.errors + result2.errors)
                return result2
            return result1
        return Combinator(internal)

    def then(self, combinator) -> Combinator:
        return self.thenLazy(lambda: combinator)

    def OR(self, otherCombinator) -> Combinator:
        def internal(tokens):
            result1 = self.parse(tokens)
            if result1.isSucces:
                return result1

            result2 = otherCombinator.parse(tokens)
            return result2
        return Combinator(internal)

    def many(self, minimum, maximum=None) -> Combinator:
        """Makes the parser combinator match N or more of itself"""
        def internal(tokens):
            accumulate = parseResult(True, [], tokens, [])
            result = parseResult(True, [], tokens, [])
            totalMatched = -1
            while result.isSucces:
                totalMatched += 1
                accumulate = parseResult(True,
                                         accumulate.content + result.content,
                                         result.remaining, accumulate.errors + result.errors)
                result = self.parse(accumulate.remaining)
                if maximum is not None:
                    if totalMatched >= maximum:
                        return accumulate
            if totalMatched >= minimum:
                return accumulate
            else:
                return parseResult(False, accumulate.content, accumulate.remaining, [])
        return Combinator(internal)

    def ignore(self) -> Combinator:
        return self.mapResult(lambda _: [])

    def wrap(self, otherCombinator) -> Combinator:
        return otherCombinator.then(self).then(otherCombinator)

    def mustFailThenTry(self, otherCombinator) -> Combinator:
        """Executes otherCombinator if this combinator fails to parse"""
        def internal(tokens):
            result = self.parse(tokens)
            if result.isSucces:
                return parseResult(False, result.content, result.remaining, [])
            return otherCombinator.parse(tokens)
        return Combinator(internal)

    def mapResult(self, g) -> Combinator:
        def internal(tokens):
            result = self.parse(tokens)
            return result.map(g)
        return Combinator(internal)

    def mapSingle(self, g) -> Combinator:
        return self.mapResult(lambda x: x[0]).mapResult(g).mapResult(lambda x: [x])

    def failRecovery(self, errorMessage: str, substitutionValue: list = None) -> Combinator:
        """
        Changes the combinator to recover from a parse failure, and always succeed.
        :param errorMessage: The error message to show
        :param substitutionValue: The value to return if the original failed.
        :return: New combinator
        """
        if substitutionValue is None:
            substitutionValue = []

        def internal(tokens):
            result = self.f(tokens)
            if result.isSucces:
                return result
            return parseResult(True, substitutionValue, tokens, [ParseError(len(tokens), errorMessage)])
        return Combinator(internal)

    def errorIfSucceeds(self, errorMessage: str, substitutionValue: list = None) -> Combinator:
        """
        Changes the combinator to Substitute a given value instaed, if the original succeeds.
        This undoes consumption of the token stream.
        If original fails, still fails.
        Useful for EOF recovery, for example
        :param errorMessage: The error message to show
        :param substitutionValue: The substitution value to return instead if the original succeeded. Fails if original fails.
        :return: New combinator
        """
        if substitutionValue is None:
            substitutionValue = []

        def internal(tokens):
            if self.f(tokens).isSucces:
                return parseResult(True, substitutionValue, tokens, [ParseError(len(tokens), errorMessage)])
            else:
                return parseResult(False, None, tokens, [])
        return Combinator(internal)


def reduceOR(combinators) -> Combinator:
    reduced = combinators[0]
    combinators = combinators[1:]
    while len(combinators) != 0:
        reduced = reduced.OR(combinators[0])
        combinators = combinators[1:]
    return reduced


def reduceTHEN(combinators) -> Combinator:
    reduced = combinators[0]
    combinators = combinators[1:]
    while len(combinators) != 0:
        reduced = reduced.then(combinators[0])
        combinators = combinators[1:]
    return reduced


def MC(char) -> Combinator:
    """Match char"""
    def internal(tokens):
        if len(tokens) > 0:
            if tokens[0] == char:
                return parseResult(True, [tokens[0]], tokens[1:], [])
        return parseResult(False, None, tokens, [])
    comb = Combinator(internal)
    return comb


def ConcatStrings(items):
    return ["".join(items)]


def listEquals(a, b):
    """Shallow compare equal length lists"""
    if len(a) is not len(b):
        raise Exception("Bug")
    zipped = zip(a, b)
    for (x, y) in zipped:
        if x != y:
            return False
    return True


def MS(specificString) -> Combinator:
    def internal(tokens):
        length = len(specificString)
        if len(tokens) >= length:
            if listEquals(tokens[:length], specificString):
                return parseResult(True, ["".join(tokens[:length])], tokens[length:], [])
        return parseResult(False, None, tokens, [])
    comb = Combinator(internal)
    return comb


def AnyOfMS(*specificStrings) -> Combinator:
    return reduceOR([MS(x) for x in specificStrings])


def AnyFunc(tokens):
    if len(tokens) > 0:
        return parseResult(True, [tokens[0]], tokens[1:], [])
    # EOF
    return parseResult(False, None, tokens, [])


Any = Combinator(AnyFunc)

SOF_value = 985743587435
EOF_value = 874595340400
SOF = MC(SOF_value)
EOF = MC(EOF_value)
