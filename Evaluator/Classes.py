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

    def serializeLLQ(self):
        raise Exception("Cannot serialise a " + self.kind.name)

    def errorDumpSerialize(self):
        raise NotImplementedError("Not implemented equality for this class")

    def isSerializable(self):
        return False

    def equals(self, other):
        raise NotImplementedError("Not implemented equality for this class")


class List(Value):
    """Represents a list of values"""

    def __init__(self, value):
        super().__init__(value, Kind.List)

    def __abstractSerialize__(self, serializeInvocation):
        isString = True
        for i in self.value:
            if i.kind != Kind.Char:
                isString = False
        if not isString:
            # Not a list of chars, ie its not a string
            return "[ " + " ".join([serializeInvocation(x) for x in self.value]) + " ]"
        # Print a list of chars (ie a string) as a string
        return '"' + "".join([__escape_string__(x.value) for x in self.value]) + '"'

    def serializeLLQ(self):
        return self.__abstractSerialize__(lambda x: x.serializeLLQ())

    def errorDumpSerialize(self):
        return self.__abstractSerialize__(lambda x: x.errorDumpSerialize())

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

    def serializeLLQ(self):
        return self.value

    def errorDumpSerialize(self):
        return self.serializeLLQ()

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

    def serializeLLQ(self):
        return 'c"' + __escape_string__(self.value) + '"'

    def errorDumpSerialize(self):
        return self.serializeLLQ()

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

    def serializeLLQ(self):
        if self.value:
            return "true"
        return "false"

    def errorDumpSerialize(self):
        return self.serializeLLQ()

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

    def serializeLLQ(self):
        return str(self.value)

    def errorDumpSerialize(self):
        return self.serializeLLQ()

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

    def errorDumpSerialize(self):
        return "( " + " ".join([x.errorDumpSerialize() for x in self.value]) + " )"


class Reference(Value):
    """Represents a named reference that needs to be evaluated"""
    def __init__(self, value):
        super().__init__(value, Kind.Reference)

    def equals(self, other):
        # References should be evaluated to their value when passed to a function
        raise "Cannot call equals on a reference value (running code), engine error"

    def errorDumpSerialize(self):
        return "*" + self.value


class StackReturnValue(Value):
    def __init__(self):
        super().__init__(None, Kind.StackReturnValue)

    def equals(self, other):
        raise "Cannot call equals on a stack return value (running code), engine error"

    def errorDumpSerialize(self):
        return "StackReturnValue"



class Lambda(Value):
    """In memory representation of a function"""
    def __init__(self):
        super().__init__(None, Kind.Lambda)

    def bind(self, argument, callingFrame: StackFrame) -> Lambda:
        raise NotImplementedError("Abstract class")

    def equals(self, other):
        raise NotImplementedError("Equality between lambdas is not implemented in this engine due to implementation"
                                  " difficulties, it should be eventually")

    def canRun(self) -> bool:
        raise NotImplementedError("Abstract class")

    def createFrame(self, callingFrame) -> StackFrame:
        raise NotImplementedError("Abstract class")


class UserLambda(Lambda):
    """In memory representation of a function"""
    #TODO fix current scope usage
    def __init__(self, bindings, body, boundFrame: StackFrame, bindIndex=0):
        super().__init__()
        self.__bindings__ = bindings  # function arguments
        self.__body__ = body  # the code to execute
        # Contains its own scope, equal to the scope captured at creation
        self.__boundFrame__ = boundFrame.captured()
        self.__bindIndex__ = bindIndex  # index of the arg that will bind next

    def __bindIsFinished__(self):
        return self.__bindIndex__ >= len(self.__bindings__)

    def bind(self, variable, callingFrame: StackFrame) -> UserLambda:
        if self.__bindIsFinished__():
            callingFrame.throwError("Tried to bind fully bound lambda. Engine error.")
        bound = self.__boundFrame__.addScopedRegularValue(self.__bindings__[self.__bindIndex__], variable)
        return UserLambda(self.__bindings__, self.__body__, bound, bindIndex=self.__bindIndex__+1)

    def canRun(self) -> bool:
        return self.__bindIsFinished__()

    def createFrame(self, callingFrame) -> StackFrame:
        if not self.canRun():
            callingFrame.throwError("Tried to run a lambda that still needs arguments bound. Engine error.")
        #Break readonly rule for once, to enable captured scope to work.
        newFrame = self.__boundFrame__.__copy__()
        newFrame.parent = callingFrame
        return newFrame.withExecutionState(self.__body__)

    def equals(self, other):
        return super(UserLambda, self).equals(other)

    def errorDumpSerialize(self):
        return "UserLambda"


class SystemFunction(Lambda):
    """In memory representation of a system function"""
    def __init__(self, function, bindingsLeft):
        super().__init__()
        self.function = function
        self.bindingsLeft = bindingsLeft

    def equals(self, other):
        super(SystemFunction, self).equals(other)

    def canRun(self) -> bool:
        return self.bindingsLeft == 0

    def createFrame(self, callingFrame: StackFrame) -> StackFrame:
        if not self.canRun():
            callingFrame.throwError("Tried to run a lambda that still needs arguments bound. Engine error.")
        return callingFrame.child(self.function(callingFrame))

    def bind(self, argument, callingFrame):
        if self.bindingsLeft <= 0:
            callingFrame.throwError("Tried to bind to a fully bound system function")
        return SystemFunction(functools.partial(self.function, argument), self.bindingsLeft - 1)

    def errorDumpSerialize(self):
        return "SystemFunction"


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
        # explicitly take over the full scoped names, values, macros from the parents. Stacks exist only for return
        # values and for handlers. So we don't have to check higher up and/or flatten for capture.
        old = self
        newchild = self.withExecutionState(executionState)
        newchild.parent = old
        return newchild

    def hasScopedRegularValue(self, name):
        #Do not check parents, because parent can be a non-captured outer scope
        if name == Config.langConfig.currentScopeKeyword:
            return True
        if name in self.__scopedNames__.keys():
            return self.__scopedNames__[name] == VarType.Regular
        return False

    def retrieveScopedRegularValue(self, name):
        #Do not check parents, because parent can be a non-captured outer scope
        if name == Config.langConfig.currentScopeKeyword:
            return self.captured()
        if not self.hasScopedRegularValue(name):
            if name not in self.__scopedNames__.keys():
                self.throwError("Tried to retrieve regular value " + name + ". Value was not found in scope.")
            else:
                self.throwError("Tried to retrieve regular value " + name +
                                ". This value is a " + self.__scopedNames__[name].name + " value, not a regular value.")
        return self.__scopedValues__[name]

    def withExecutionState(self, executionState: Value) -> StackFrame:
        copy = self.__copy__()
        copy.executionState = executionState
        return copy

    def __stackTrace__(self):
        if self.parent is not None:
            self.parent.__stackTrace__()
        cprint("\tat: " + self.executionState.errorDumpSerialize(), color="red")

    def throwError(self, errorMessage):
        cprint("Error while evaluating code.", color="red")
        cprint(errorMessage, color="red")
        self.__stackTrace__()
        raise RuntimeEvaluationError("Runtime error")

    def captured(self) -> StackFrame:
        """Returns a new stack that contains all capturable data, flattened into a single dimension (no parent), so no captured handlers.
        This is then used to execute user created functions, or closures, later on"""
        cprint("Warning: Function Captured on the stackframe doesnt do handler removal yet.", color="cyan")
        #TODO implement
        copied = self.__copy__()
        copied.parent = None
        return copied

    def __copy__(self) -> StackFrame:
        newcopy = StackFrame(self.executionState)
        newcopy.__scopedNames__ = self.__scopedNames__.copy()
        newcopy.__scopedValues__ = self.__scopedValues__.copy()
        newcopy.__scopedMacros__ = self.__scopedMacros__
        newcopy.__handlerSet__ = self.__handlerSet__.copy()
        newcopy.__childReturnValue__ = self.__childReturnValue__
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
        #Do not check parents, because parent can be a non-captured outer scope
        if name in self.__scopedNames__.keys():
            if self.__scopedNames__[name] == VarType.Macro:
                return True
        return False

    def retrieveScopedMacroValue(self, name):
        #Do not check parents, because parent can be a non-captured outer scope
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

    def errorDumpSerialize(self):
        return Config.langConfig.currentScopeKeyword

    def debugStateToString(self):
        return self.executionState.errorDumpSerialize()


class RuntimeEvaluationError(Exception):
    pass