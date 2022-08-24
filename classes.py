from enum import Enum


class Kind(Enum):
    Lambda = 1
    Reference = 2
    QuotedName = 3
    List = 4
    sExpression = 5
    String = 6


class Value:
    """Abstract class for any value, must be subtyped"""
    def __init__(self, value, kind: Kind):
        self.__value__ = value
        self.kind = kind

    def serialize(self):
        raise Exception("Cannot serialise a " + self.kind.name)

    def isSerializable(self):
        return False


class List(Value):
    """Represents a list of values"""
    def __init__(self, value):
        super().__init__(value, Kind.List)

    def serialize(self):
        return "[ " + " ".join([x.serialize() for x in self.__value__]) + " ]"

    def isSerializable(self):
        for i in self.__value__:
            if not i.isSerializable():
                return False
        return True


class QuotedName(Value):
    """Represent a quoted name, an unevaluated reference name, for use mostly in macros"""
    def __init__(self, value):
        super().__init__(value, Kind.QuotedName)

    def serialize(self):
        return self.__value__

    def isSerializable(self):
        return True


def __escape_string__(string):
    print("TODO implement string escaping")  # todo
    return string


class String(Value):
    def __init__(self, value, kind):
        super().__init__(value, kind)

    def serialize(self):
        return '"' + __escape_string__(self.__value__) + '"'

    def isSerializable(self):
        return True


# classes above may be used inside the language as data
# beyond this are interpreter only types, such as lambda types, reference types, etc.


class sExpression(Value):
    """A piece of lisp code being evaluated"""
    def __init__(self, value):
        super().__init__(value, Kind.sExpression)


class Reference(Value):
    """Represents a named reference that needs to be evaluated"""
    def __init__(self, value):
        super().__init__(value, Kind.Reference)


class Lambda(Value):
    """In memory representation of a function"""
    def __init__(self, bindings, body, currentScope, currentMacroScope, bindIndex=0):
        super().__init__(None, Kind.Lambda)
        self.issExpression = False

        self.bindings = bindings  # function arguments
        self.body = body  # the code to execute
        # Contains its own scope, equal to the scope captured at creation
        self.boundScope = currentScope.newChild()
        self.boundMacroScope = currentMacroScope.newChild()
        self.bindIndex = bindIndex  # index of the arg that will bind next

    def bindIsFinished(self):
        return self.boundScope.countValues() == self.bindIndex

    def bind(self, variable):
        if self.bindIsFinished():
            raise Exception("Binding fully bound lambda (engine error?)")
        newscope = self.boundScope.addValue(self.bindings[self.bindIndex], variable)
        return Lambda(self.bindings, self.body, newscope, self.boundMacroScope, self.bindIndex + 1)

    def bindingsLeft(self):
        return len(self.bindings) - self.boundScope.countValues()


class Scope:
    """A construct containing the currently accessible references"""
    def __init__(self, parent, startValues=None):
        if startValues is None:
            startValues = {}
        # currently scoped variables
        self.__values__ = startValues
        self.__parent__ = parent  # the scope in which this scope is located, and thus is also accessible

    def addValue(self, name, value):
        if name in self.__values__.keys():
            raise Exception("Overwriting variables in the same scope is not allowed")
        copy = self.__values__.copy()
        copy[name] = value
        return Scope(self.__parent__, copy)

    def retrieveValue(self, name):
        if name in self.__values__.keys():
            return self.__values__[name]
        if self.__parent__ is not None:
            return self.__parent__.retrieveValue(name)
        raise Exception("Unknown variable")

    def countValues(self):
        if self.__parent__ is not None:
            return len(self.__values__) + self.__parent__.countValues()
        return len(self.__values__)

    def newChild(self):
        return Scope(self)
