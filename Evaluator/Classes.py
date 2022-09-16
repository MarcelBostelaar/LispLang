import functools
from enum import Enum

from Config.langConfig import currentScopeKeyword


class Kind(Enum):
    Lambda = 1
    Reference = 2
    QuotedName = 3
    List = 4
    sExpression = 5
    Char = 6
    Number = 7
    Boolean = 8
    Scope = 9


class Value:
    """Abstract class for any value, must be subtyped"""
    def __init__(self, value, kind: Kind):
        self.value = value
        self.kind = kind

    def serialize(self):
        raise Exception("Cannot serialise a " + self.kind.name)

    def isSerializable(self):
        return False

    def equals(self, other):
        raise NotImplementedError("Not implemented equality for this class")


class List(Value):
    """Represents a list of values"""
    def __init__(self, value):
        super().__init__(value, Kind.List)

    def serialize(self):
        for i in self.value:
            if i.kind != Kind.Char:
                # Not a list of chars, ie its not a string
                return "[ " + " ".join([x.serialize() for x in self.value]) + " ]"
        # Print a list of chars (ie a string) as a string
        return '"' + "".join([__escape_string__(x.value) for x in self.value]) + '"'

    def isSerializable(self):
        for i in self.value:
            if not i.isSerializable():
                return False
        return True

    def concat(self, other):
        if other.kind != Kind.List:
            raise Exception("Cant concat two lists")
        return List(self.value + other.value)

    def equals(self, other):
        if other.kind != self.kind:
            return False
        if len(other.value) != len(self.value):
            return False
        for i in range(len(self.value)):
            if not self.value[i].equals(other.value[i]):
                return False
        return True


class QuotedName(Value):
    """Represent a quoted name, an unevaluated reference name, for use mostly in macros"""
    def __init__(self, value):
        super().__init__(value, Kind.QuotedName)

    def serialize(self):
        return self.value

    def isSerializable(self):
        return True

    def equals(self, other):
        if other.kind != self.kind:
            return False
        return self.value == other.value


def __escape_string__(string):
    print("TODO implement string escaping")  # todo
    return string


class Char(Value):
    def __init__(self, value):
        super().__init__(value, Kind.Char)

    def serialize(self):
        return 'c"' + __escape_string__(self.value) + '"'

    def isSerializable(self):
        return True

    def equals(self, other):
        if other.kind != self.kind:
            return False
        return self.value == other.value


class Boolean(Value):
    def __init__(self, value):
        if value == "true":
            super().__init__(True, Kind.Boolean)
            return
        if value == "false":
            super().__init__(False, Kind.Boolean)
            return
        if value in [True, False]:
            super().__init__(value, Kind.Boolean)
            return
        raise Exception("Not a valid boolean value")

    def serialize(self):
        if self.value:
            return "true"
        return "false"

    def isSerializable(self):
        return True

    def equals(self, other):
        if other.kind != self.kind:
            return False
        return self.value == other.value


class Number(Value):
    def __init__(self, value):
        super().__init__(value, Kind.Number)
        if isinstance(value, float):
            self.value = value
            return
        raise "Cant save non float in number (engine bug)"

    def serialize(self):
        return str(self.value)

    def isSerializable(self):
        return True

    def equals(self, other):
        if other.kind != self.kind:
            return False
        return self.value == other.value

# classes above may be used inside the language as data
# beyond this are interpreter only types, such as lambda types, reference types, etc.


class sExpression(Value):
    """A piece of lisp code being evaluated"""
    def __init__(self, value):
        super().__init__(value, Kind.sExpression)

    def equals(self, other):
        # S expressions (which are different from lists) cannot be treated as data
        raise "Cannot call equals on an s expression (running code), engine error"


class Reference(Value):
    """Represents a named reference that needs to be evaluated"""
    def __init__(self, value):
        super().__init__(value, Kind.Reference)

    def equals(self, other):
        # References should be evaluated to their value when passed to a function
        raise "Cannot call equals on a reference value (running code), engine error"


class Lambda(Value):
    """In memory representation of a function"""
    def __init__(self):
        super().__init__(None, Kind.Lambda)

    def bind(self, argument):
        raise NotImplementedError("Abstract class")

    def run(self, runFunc):
        raise NotImplementedError("Abstract class")

    def equals(self, other):
        raise NotImplementedError("Equality between lambdas is not implemented in this engine due to implementation"
                                  " difficulties, it should be eventually")


class UserLambda(Lambda):
    """In memory representation of a function"""
    def __init__(self, bindings, body, currentScope, bindIndex=0):
        super().__init__()
        self.bindings = bindings  # function arguments
        self.body = body  # the code to execute
        # Contains its own scope, equal to the scope captured at creation
        self.boundScope = currentScope
        self.bindIndex = bindIndex  # index of the arg that will bind next

    def __bindIsFinished__(self):
        return self.bindIndex >= len(self.bindings)

    def bind(self, variable):
        if self.__bindIsFinished__():
            raise Exception("Binding fully bound lambda (engine error?)")
        newscope = self.boundScope.addValue(self.bindings[self.bindIndex], variable)
        return UserLambda(self.bindings, self.body, newscope, self.bindIndex + 1)

    def run(self, runFunc):
        """
        Returns an evaluated form of itself if its fully bound, return self if not fully bound
        :param runFunc: Eval func of (expression, scope) -> expression
        :return:
        """
        if self.__bindIsFinished__():
            return runFunc(self.body, self.boundScope)
        return self


class SystemFunction(Lambda):
    """In memory representation of a system function"""

    def __init__(self, function, bindingsLeft):
        super().__init__()
        self.function = function
        self.bindingsLeft = bindingsLeft

    def bind(self, argument):
        if self.bindingsLeft <= 0:
            raise Exception("Tried to bind to a fully bound system function")
        return SystemFunction(functools.partial(self.function, argument), self.bindingsLeft - 1)

    def run(self, runFunc):
        if self.bindingsLeft == 0:
            return self.function()
        return self


class VarType(Enum):
    Regular = 1
    Macro = 2


class ScopedVar:
    def __init__(self, value, vartype: VarType):
        self.value = value
        self.vartype = vartype


class Scope(Value):
    """A construct containing the currently accessible references"""
    def __init__(self, startValues=None):
        super(Scope, self).__init__(None, Kind.Scope)
        if startValues is None:
            startValues = {}
        # currently scoped variables
        self.values = startValues

    def addValue(self, name, value, varType=VarType.Regular):
        # if name in self.values.keys():
        #     raise Exception("Overwriting variables in the same scope is not allowed")
        copy = self.values.copy()
        copy[name] = ScopedVar(value, varType)
        return Scope(copy)

    def __retrieve__(self, name):
        if name in self.values.keys():
            return self.values[name]
        if name == currentScopeKeyword:
            return ScopedVar(self, VarType.Regular)
        raise Exception("Unknown variable")

    def retrieveValue(self, name):
        return self.__retrieve__(name).value

    def retrieveVartype(self, name):
        return self.__retrieve__(name).vartype

    def isVarType(self, name, vartype: VarType):
        value = self.__retrieve__(name)
        return value.vartype == vartype

    def hasValue(self, name):
        if name in self.values.keys():
            return True
        return False

    def equals(self, other):
        if other.kind != self.kind:
            return False
        return self.value == other.value