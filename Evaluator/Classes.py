from __future__ import annotations

import functools
from abc import ABC
from enum import Enum

from termcolor import cprint

import Config.langConfig
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
    StackReturnValue = 10


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
        raise Exception("Cant save non float in number (engine bug)")

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
    def __init__(self, value: list):
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


class StackReturnValue(Value):
    def __init__(self):
        super().__init__(None, Kind.StackReturnValue)

    def equals(self, other):
        raise "Cannot call equals on a stack return value (running code), engine error"



class Lambda(Value):
    """In memory representation of a function"""
    def __init__(self):
        super().__init__(None, Kind.Lambda)

    def bind(self, argument) -> Lambda:
        raise NotImplementedError("Abstract class")

    def equals(self, other):
        raise NotImplementedError("Equality between lambdas is not implemented in this engine due to implementation"
                                  " difficulties, it should be eventually")

    def canRun(self) -> bool:
        raise NotImplementedError("Abstract class")

    def createFrame(self, parentFrame) -> StackFrame:
        raise NotImplementedError("Abstract class")


class UserLambda(Lambda):
    """In memory representation of a function"""

    def canRun(self) -> bool:
        return self.__bindIsFinished__()

    def createFrame(self, parentFrame) -> StackFrame:
        raise NotImplementedError("")

    def equals(self, other):
        return super(UserLambda, self).equals(other)

    #TODO fix current scope usage
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
        raise NotImplementedError("")


class SystemFunction(Lambda):
    """In memory representation of a system function"""

    def equals(self, other):
        super(SystemFunction, self).equals(other)

    def canRun(self) -> bool:
        return self.bindingsLeft == 0

    def createFrame(self, parentFrame: StackFrame) -> StackFrame:
        return parentFrame.child(self)

    def __init__(self, function, bindingsLeft):
        super().__init__()
        self.function = function
        self.bindingsLeft = bindingsLeft

    def bind(self, argument):
        if self.bindingsLeft <= 0:
            raise Exception("Tried to bind to a fully bound system function")
        return SystemFunction(functools.partial(self.function, argument), self.bindingsLeft - 1)


class VarType(Enum):
    Regular = 1
    Macro = 2


class StackFrame(Value):
    """A frame in the stack that contains the scoped names, values and handlers, as well as a link to its parent"""
    def __init__(self, executionState):
        super().__init__(None, Kind.Scope)
        self.executionState = executionState
        """Read only. Current code being operated on in this frame."""
        self.parent = None
        """Read only. Parent stack frame of this stack."""
        self.__scopedNames__ = {}
        self.__scopedValues__ = {}
        self.__scopedMacros__ = {}
        self.__handlerSet__ = {}
        """The handlers in this stack frame, not those of parents"""
        self.__childReturnValue__ = None

    def child(self, executionState: Value) -> StackFrame:
        old = self
        newchild = self.withExecutionState(executionState)
        newchild.parent = old
        return newchild

    def hasScopedRegularValue(self, name):
        if name == Config.langConfig.currentScopeKeyword:
            return True
        if name in self.__scopedNames__.keys():
            return self.__scopedNames__[name] == VarType.Regular
        return False

    def retrieveScopedRegularValue(self, name):
        if name == Config.langConfig.currentScopeKeyword:
            return self
        if not self.hasScopedRegularValue(name):
            if name not in self.__scopedNames__.keys():
                self.throwError("Tried to retrieve regular value " + name + ". Value was not found in scope.")
            else:
                self.throwError("Tried to retrieve regular value " + name +
                                ". This value is a " + self.__scopedNames__[name].name + " value, not a regular value.")
        return self.__scopedValues__[name]

    def withExecutionState(self, executionState) -> StackFrame:
        copy = self.__copy__()
        copy.executionState = executionState
        return copy

    def __stackTrace__(self):
        cprint("\tat: " + self.executionState.serialize(), color="red")
        if self.parent is not None:
            self.parent.__stackTrace__()

    def throwError(self, errorMessage):
        cprint("Error while evaluating code.", color="red")
        cprint(errorMessage, color="red")
        self.__stackTrace__()
        raise Exception("Runtime error")

    def captured(self) -> StackFrame:
        """Returns a new stack that contains all capturable data, so no captured handlers.
        This is then used to execute user created functions, or closures, later on"""
        cprint("Function Captured on the stackframe isn't implemented, returns unaltered frame.", color="red")
        #TODO implement
        return self

    def __copy__(self) -> StackFrame:
        newcopy = StackFrame(self.executionState)
        newcopy.__scopedNames__ = self.__scopedNames__.copy()
        newcopy.__scopedValues__ = self.__scopedValues__.copy()
        newcopy.__scopedMacros__ = self.__scopedMacros__
        newcopy.__handlerSet__ = self.__handlerSet__.copy()
        newcopy.childReturnValue = self.__childReturnValue__
        newcopy.parent = self.parent
        return newcopy

    def getChildReturnValue(self):
        if self.__childReturnValue__ is None:
            self.throwError("No child to return found. Engine bug")
        return self.__childReturnValue__

    def withChildReturnValue(self, value):
        copy = self.__copy__()
        copy.__childReturnValue__ = value
        return copy

    def hasScopedMacroValue(self, name):
        if name in self.__scopedNames__.keys():
            if self.__scopedNames__[name] == VarType.Macro:
                return True
        return False

    def retrieveScopedMacroValue(self, name):
        if not self.hasScopedMacroValue(name):
            self.throwError("Tried to retrieve macro '" + name + "'. Macro not found in scope.")
        return self.__scopedMacros__[name]

    def checkReservedKeyword(self, name):
        if name in Config.langConfig.reservedWords:
            self.throwError("Tried to override the reserved keyword '" + name + "'. Now allowed.")

    def addScopedMacroValue(self, name, value):
        self.checkReservedKeyword(name)
        self.checkReservedKeyword(name)
        copy = self.__copy__()
        copy.__scopedNames__[name] = VarType.Macro
        copy.__scopedMacros__[name] = value
        return copy

    def addScopedRegularValue(self, name, value) -> StackFrame:
        self.checkReservedKeyword(name)
        copy = self.__copy__()
        copy.__scopedNames__[name] = VarType.Regular
        copy.__scopedValues__[name] = value
        return copy
