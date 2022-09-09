from enum import Enum

from langConfig import currentScopeKeyword


class Kind(Enum):
    Lambda = 1
    Reference = 2
    QuotedName = 3
    List = 4
    sExpression = 5
    String = 6
    IgnoredValue = 7
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


class List(Value):
    """Represents a list of values"""
    def __init__(self, value):
        super().__init__(value, Kind.List)

    def serialize(self):
        return "[ " + " ".join([x.serialize() for x in self.value]) + " ]"

    def isSerializable(self):
        for i in self.value:
            if not i.isSerializable():
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


def __escape_string__(string):
    print("TODO implement string escaping")  # todo
    return string


class String(Value):
    def __init__(self, value):
        super().__init__(value, Kind.String)

    def serialize(self):
        return '"' + __escape_string__(self.value) + '"'

    def isSerializable(self):
        return True


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

# classes above may be used inside the language as data
# beyond this are interpreter only types, such as lambda types, reference types, etc.


class sExpression(Value):
    """A piece of lisp code being evaluated"""
    def __init__(self, value):
        super().__init__(value, Kind.sExpression)


class IgnoredValueClass(Value):
    """A class to represent a value that was ignored. Ignored values at the start of an s expression are removed."""
    def __init__(self):
        super().__init__(None, Kind.IgnoredValue)


IgnoredValue = IgnoredValueClass()


class Reference(Value):
    """Represents a named reference that needs to be evaluated"""
    def __init__(self, value):
        super().__init__(value, Kind.Reference)


# class SpecialFunc(Value):
#     """Handles the application of the build in functions which may have special properties"""
#     def __init__(self, value):
#         super().__init__(value, Kind.SpecialFunc)


class Lambda(Value):
    """In memory representation of a function"""
    def __init__(self, bindings, body, currentScope, bindIndex=0):
        super().__init__(None, Kind.Lambda)
        self.issExpression = False

        self.bindings = bindings  # function arguments
        self.body = body  # the code to execute
        # Contains its own scope, equal to the scope captured at creation
        self.boundScope = currentScope
        self.bindIndex = bindIndex  # index of the arg that will bind next

    def bindIsFinished(self):
        return self.boundScope.countFirstLevelValues() == len(self.bindings)

    def bind(self, variable):
        if self.bindIsFinished():
            raise Exception("Binding fully bound lambda (engine error?)")
        newscope = self.boundScope.addValue(self.bindings[self.bindIndex], variable)
        return Lambda(self.bindings, self.body, newscope, self.bindIndex + 1)

    def bindingsLeft(self):
        return len(self.bindings) - self.boundScope.countFirstLevelValues()

    def run(self, runFunc):
        """
        Returns an evaluated form of itself if its fully bound, return self if not fully bound
        :param runFunc: Eval func of (expression, scope) -> expression
        :return:
        """
        if self.bindIsFinished():
            return runFunc(self.body, self.boundScope)
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
    def __init__(self, parent, startValues=None):
        super(Scope, self).__init__(None, Kind.Scope)
        if startValues is None:
            startValues = {}
        # currently scoped variables
        self.values = startValues
        self.parent = parent  # the scope in which this scope is located, and thus is also accessible

    def addValue(self, name, value, varType=VarType.Regular):
        if name in self.values.keys():
            raise Exception("Overwriting variables in the same scope is not allowed")
        copy = self.values.copy()
        copy[name] = ScopedVar(value, varType)
        return Scope(self.parent, copy)

    def __retrieve__(self, name):
        if name in self.values.keys():
            return self.values[name]
        if self.parent is not None:
            if self.parent.hasValue(name):
                return self.parent.retrieveValue(name)
        if name == currentScopeKeyword:
            return ScopedVar(self, VarType.Regular)
        raise Exception("Unknown variable")

    def retrieveValue(self, name):
        value = self.__retrieve__(name)
        if value.vartype == VarType.Macro:
            raise Exception("Tried to use macro as regular value, not allowed")
        return self.__retrieve__(name).value

    def retrieveVartype(self, name):
        return self.__retrieve__(name).vartype

    def isVarType(self, name, vartype: VarType):
        value = self.__retrieve__(name)
        return value.vartype == vartype

    def hasValue(self, name):
        if name in self.values.keys():
            return True
        if self.parent is not None:
            return self.parent.hasValue(name)
        return False

    def countFirstLevelValues(self):
        return len(self.values)

    def newChild(self):
        return Scope(self)

    # def __repr__(self) -> str:
    #     return f"Scope({self.__values__}, {self.__parent__})"
