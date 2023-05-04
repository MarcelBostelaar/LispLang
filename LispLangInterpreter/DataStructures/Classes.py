from __future__ import annotations

import functools
from enum import Enum
from typing import TYPE_CHECKING

from termcolor import cprint

from .Kind import Kind
from ..Config import langConfig
from .HandlerStateRegistry import HandlerStateSingleton
from .SupportFunctions import escape_string, checkReservedKeyword, isIndirectionValue, \
    dereference
if TYPE_CHECKING:
    from ..ImportHandlerSystem.LibraryClasses import Searchable


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

#Code literals


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
        return '"' + "".join([escape_string(x.value) for x in self.value]) + '"'

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


class Char(Value):
    def __init__(self, value):
        super().__init__(value, Kind.Char)

    def serializeLLQ(self):
        return 'c"' + escape_string(self.value) + '"'

    def errorDumpSerialize(self):
        return self.serializeLLQ()

    def isSerializable(self):
        return True

    def equals(self, other):
        if other.kind != self.kind:
            return False
        return self.value == other.value


class ContinueStop(Value):
    def __init__(self, isContinue: bool, returnValue: Value, newState: Value):
        super().__init__(None, Kind.ContinueStop)
        self.isContinue = isContinue
        self.returnValue = returnValue
        self.newState = newState

    def __unRun__(self) -> Value:
        keyword = langConfig.continueKeyword if self.isContinue else langConfig.stopKeyword
        return List([Reference(keyword), self.returnValue, self.newState])

    def isSerializable(self):
        return self.value.isSerializable()

    def serializeLLQ(self):
        self.__unRun__().serializeLLQ()

    def errorDumpSerialize(self):
        self.__unRun__().errorDumpSerialize()

    def equals(self, other):
        if other.kind == self.kind:
            if other.isContinue == self.isContinue:
                return other.value.equals(self.value)
        return False


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


class Unit(Value):
    def __init__(self):
        super().__init__(None, Kind.Unit)

    def serializeLLQ(self):
        return langConfig.unitKeyword

    def errorDumpSerialize(self):
        return self.serializeLLQ()

    def isSerializable(self):
        return True

    def equals(self, other):
        return other.kind == self.kind


## Interpreter types
#Interpreter code classes

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

#function representations


class Lambda(Value):
    """In memory representation of a function"""

    def errorDumpSerialize(self):
        raise NotImplementedError("Abstract class")

    def __init__(self):
        super().__init__(None, Kind.Lambda)

    def bind(self, argument, callingFrame: StackFrame) -> Lambda:
        raise NotImplementedError("Abstract class")

    def equals(self, other):
        raise NotImplementedError("Equality between lambdas is not implemented in this engine due to implementation"
                                  " difficulties, it should be eventually")

    def canRun(self) -> bool:
        raise NotImplementedError("Abstract class")

    def createEvaluationFrame(self, callingFrame) -> StackFrame:
        raise NotImplementedError("Abstract class")


class UserLambda(Lambda):
    """In memory representation of a function"""

    def __init__(self, bindings, body, boundScope: Scope, bindIndex=0):
        super().__init__()
        self.__bindings__ = bindings  # function arguments
        self.__body__ = body  # the code to execute
        # Contains its own scope, equal to the scope captured at creation
        self.__boundScope__ = boundScope
        self.__bindIndex__ = bindIndex  # index of the arg that will bind next

    def __bindIsFinished__(self):
        return self.__bindIndex__ >= len(self.__bindings__)

    def bind(self, variable, callingFrame: StackFrame) -> UserLambda:
        if self.__bindIsFinished__():
            callingFrame.throwError("Tried to bind fully bound lambda. Engine error.")
        bound = self.__boundScope__.addScopedRegularValue(callingFrame, self.__bindings__[self.__bindIndex__], variable)
        return UserLambda(self.__bindings__, self.__body__, bound, bindIndex=self.__bindIndex__ + 1)

    def canRun(self) -> bool:
        return self.__bindIsFinished__()

    def createEvaluationFrame(self, callingFrame) -> StackFrame:
        if not self.canRun():
            callingFrame.throwError("Tried to run a lambda that still needs arguments bound. Engine error.")
        newFrame = callingFrame.createChild(self.__body__)
        newFrame.currentScope = self.__boundScope__
        return newFrame

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

    def createEvaluationFrame(self, callingFrame: StackFrame) -> StackFrame:
        if not self.canRun():
            callingFrame.throwError("Tried to run a lambda that still needs arguments bound. Engine error.")
        return callingFrame.createChild(self.function(callingFrame))

    def bind(self, argument, callingFrame):
        if self.bindingsLeft <= 0:
            callingFrame.throwError("Tried to bind to a fully bound system function")
        return SystemFunction(functools.partial(self.function, argument), self.bindingsLeft - 1)

    def errorDumpSerialize(self):
        return f"SystemFunction"


class UnfinishedHandlerInvocation(Lambda):
    """In memory representation of an unfinished handler invocation,
    acts akin to a type definition for an effectfull function."""
    def __init__(self, name: str, argAmount: int):
        super().__init__()
        self.name = name
        """The handler name it references"""
        self.argAmount = argAmount
        """Total amount of args needed for invocation"""
        self.args = []

    def bind(self, argument, callingFrame: StackFrame) -> UnfinishedHandlerInvocation:
        if self.canRun():
            callingFrame.throwError(f"Too many arguments added to the unfinished handler invocation '{self.name}'")
        copy = UnfinishedHandlerInvocation(self.name, self.argAmount)
        copy.args.append(argument)
        return copy

    def canRun(self) -> bool:
        realLength = len(self.args)
        return realLength >= self.argAmount

    def createEvaluationFrame(self, callingFrame: StackFrame) -> StackFrame:
        """Returns a new stack in which to run the function code, with the calling frame as parent"""
        if not self.canRun():
            callingFrame.throwError(f"Not enough arguments added for invocation of '{self.name}'.")
        if not callingFrame.hasHandler(self.name):
            callingFrame.throwError(f"Tried to handle effectfull function '{self.name}'"
                                    f", but no handler for it was found.")
        return callingFrame.invokeHandler(self.name, self.args)

    def errorDumpSerialize(self):
        return f"UnfinishedHandlerInvocation<{self.name}, with: {', '.join([x.errorDumpSerialize() for x in self.args])}>"

    def equals(self, other):
        raise NotImplementedError("")


#Stack and control flow classes


class HandleReturnValue(Value):
    def __init__(self, handlerID):
        super().__init__(None, Kind.HandleReturnValue)
        self.handlerID = handlerID

    def errorDumpSerialize(self):
        return f"HandleReturnValue<{self.handlerID}>"

    def equals(self, other):
        raise NotImplementedError("")


class HandleBranchPoint(Value):
    def __init__(self, handlerID: int, continueBranch=None):
        super().__init__(None, Kind.HandleBranchPoint)
        self.continueBranch = continueBranch
        self.handlerID = handlerID

    def errorDumpSerialize(self):
        if self.continueBranch is not None:
            return f"\n" \
                   f"HandleBranchPoint with continue branch. Continue branch:" +\
                   self.continueBranch.errorDumpSerialize() +\
                   f"\n"
        else:
            return f"\n" \
                   f"HandleBranchPoint without continue branch." \
                   f"\n"


    def equals(self, other):
        raise NotImplementedError("")


class VarType(Enum):
    Regular = 1
    Macro = 2


class Scope(Value):
    """
    Represents the current scope of values
    """
    def __init__(self, currentFile: Searchable):
        super().__init__(None, Kind.Scope)
        self.__scopedNames__ = {}
        self.__scopedValues__ = {}
        self.currentFile = currentFile

    def hasScopedRegularValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        if name == langConfig.currentScopeKeyword:
            return True
        if name in self.__scopedNames__.keys():
            return self.__scopedNames__[name] == VarType.Regular
        return False

    def retrieveScopedRegularValue(self, callingFrame: StackFrame, name: str) -> Value:
        # Do not check parents, because parent can be a non-captured outer scope
        if name == langConfig.currentScopeKeyword:
            return self
        if not self.hasScopedRegularValue(name):
            if name not in self.__scopedNames__.keys():
                callingFrame.throwError("Tried to retrieve regular value " + name + ". Value was not found in scope.")
            else:
                callingFrame.throwError("Tried to retrieve regular value " + name +
                                        ". This value is a " + self.__scopedNames__[
                                            name].name + " value, not a regular value.")
        return self.__scopedValues__[name]

    def hasScopedMacroValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        if name in self.__scopedNames__.keys():
            if self.__scopedNames__[name] == VarType.Macro:
                return True
        return False

    def retrieveScopedMacroValue(self, callingFrame: StackFrame, name) -> Value:
        # Do not check parents, because parent can be a non-captured outer scope
        if not self.hasScopedMacroValue(name):
            callingFrame.throwError("Tried to retrieve macro '" + name + "'. Macro not found in scope.")
        return self.__scopedValues__[name]

    def addScopedMacroValue(self, callingFrame: StackFrame, name, value) -> Scope:
        checkReservedKeyword(callingFrame, name)
        copy = self.__copy__()
        copy.__scopedNames__[name] = VarType.Macro
        copy.__scopedValues__[name] = value
        return copy

    def addScopedRegularValue(self, callingFrame: StackFrame, name, value) -> Scope:
        checkReservedKeyword(callingFrame, name)
        copy = self.__copy__()
        copy.__scopedNames__[name] = VarType.Regular
        copy.__scopedValues__[name] = value
        return copy

    def __copy__(self) -> Scope:
        copy = Scope(self.currentFile)
        copy.__scopedNames__ = self.__scopedNames__
        copy.__scopedValues__ = self.__scopedValues__
        return copy

    def errorDumpSerialize(self):
        return "<Captured scope>"

    def equals(self, other):
        raise NotImplementedError("")


class HandlerFrame(Value):
    def __init__(self):
        super().__init__(None, Kind.HandlerFrame)

    def hasHandler(self, name):
        raise NotImplementedError("Abstract class")

    def invokeHandler(self, callingFrame: StackFrame, name: str, values: list) -> StackFrame:
        raise NotImplementedError("Abstract class")

    def errorDumpSerialize(self):
        raise NotImplementedError("Abstract class")

    def equals(self, other):
        raise NotImplementedError()

    def __copy__(self):
        raise NotImplementedError("Abstract class")


class SystemHandlerFrame(HandlerFrame):
    def __init__(self):
        super().__init__()
        self.handlerFunctions = {}

    def addHandler(self, name, function: SystemFunction):
        copy = self.__copy__()
        copy.handlerFunctions[name] = function
        return copy

    def hasHandler(self, name):
        return name in self.handlerFunctions.keys()

    def invokeHandler(self, callingFrame: StackFrame, name: str, values: list) -> StackFrame:
        if not self.hasHandler(name):
            callingFrame.throwError(f"Handler for function '{name}' not found.")
        boundFunc: Lambda = self.handlerFunctions[name]
        for i in values:
            boundFunc = boundFunc.bind(i, callingFrame)
        return boundFunc.createEvaluationFrame(callingFrame)

    def errorDumpSerialize(self):
        return f"SystemHandlerFrame<{', '.join(self.handlerFunctions.keys())}>"

    def equals(self, other):
        raise NotImplementedError()

    def __copy__(self):
        theCopy = SystemHandlerFrame()
        theCopy.handlerFunctions = self.handlerFunctions.copy()
        return theCopy


class UserHandlerFrame(HandlerFrame):
    def __init__(self, handlerID, branchPointFrame: StackFrame):
        super().__init__()
        self.__handlerSet__ = {}
        self.parent = None
        self.handlerID = handlerID
        self.branchPointFrame = branchPointFrame

    def addHandler(self, callingFrame: StackFrame, name, value) -> HandlerFrame:
        checkReservedKeyword(callingFrame, name)
        copy = self.__copy__()
        copy.__handlerSet__[name] = value
        return copy

    def hasHandler(self, name):
        if name in self.__handlerSet__.keys():
            return True
        if self.parent is not None:
            return self.parent.hasHandler(name)
        return False

    def invokeHandler(self, callingFrame: StackFrame, name: str, values: list) -> StackFrame:
        if name not in self.__handlerSet__.keys():
            if self.parent is None:
                callingFrame.throwError(f"Handler for '{name}' doesnt exist.")
            return self.parent.invokeHandler(callingFrame, name, values)

        handlerFunc: Lambda = self.__handlerSet__[name]
        handlerFunc = handlerFunc.bind(
            HandlerStateSingleton.retrieveState(self.handlerID),
            callingFrame
        )
        for arg in values:
            if handlerFunc.canRun():
                callingFrame.throwError(f"Too many arguments exist in the handler '{name}' invocation.")
            handlerFunc = handlerFunc.bind(arg, callingFrame)

        if not handlerFunc.canRun():
            callingFrame.throwError(f"Too few arguments for handler '{name}' invocation")

        branchPointFrame = self.branchPointFrame

        # The created continue value should be added like a lambda return below the calling frame, if its continued.
        newBranchpointFrame = branchPointFrame.withExecutionState(
            HandleBranchPoint(self.handlerID, continueBranch=callingFrame))

        # The handle branch point frame is used as the parent of the new branch, to make sure the returned value
        # returns to the branch value. Branch value frame doesn't have the handler set being used here.
        handleFuncRunningFrame = handlerFunc.createEvaluationFrame(newBranchpointFrame)

        return handleFuncRunningFrame

    def errorDumpSerialize(self):
        return "<Captured handler frame>"

    def equals(self, other):
        raise NotImplementedError()

    def __copy__(self):
        theCopy = UserHandlerFrame(self.handlerID, self.branchPointFrame)
        theCopy.__handlerSet__ = self.__handlerSet__.copy()
        return theCopy


class StackReturnValue(Value):
    def __init__(self):
        super().__init__(None, Kind.StackReturnValue)

    def equals(self, other):
        raise "Cannot call equals on a stack return value (running code), engine error"

    def errorDumpSerialize(self):
        return "StackReturnValue"


class StackFrame:
    """A frame in the stack that contains the scoped names, values and handlers, as well as a link to its parent"""

    def __init__(self, executionState, currentFile: Searchable):
        self.executionState = executionState
        """Read only. Current code being operated on in this frame."""
        self.parent = None
        """Read only. Parent stack frame of this stack."""
        self.closestHandlerFrame = None
        """Handler stack is seperate, code stack only keeps track of which stack is reachable to it. 
        Other interactions are done through the evaluator code."""
        self.__childReturnValue__ = None
        self.currentScope = Scope(currentFile)

    def __copy__(self) -> StackFrame:
        newcopy = StackFrame(self.executionState, self.currentScope.currentFile)
        newcopy.currentScope = self.currentScope.__copy__()
        newcopy.closestHandlerFrame = self.closestHandlerFrame
        newcopy.__childReturnValue__ = self.__childReturnValue__
        newcopy.parent = self.parent
        return newcopy

    def createChild(self, executionState: Value) -> StackFrame:
        # explicitly take over the full scoped names, values, macros from the parents. Stacks exist only for return
        # values and for handlers. So we don't have to check higher up and/or flatten for capture.
        old = self
        newchild = self.withExecutionState(executionState)
        newchild.parent = old
        return newchild

    def withExecutionState(self, executionState: Value) -> StackFrame:
        copy = self.__copy__()
        copy.executionState = executionState
        return copy

    #Subevaluation logic

    def isFullyEvaluated(self, itemIndex) -> bool:
        """
        Returns a boolean indicating whether an item at a given index is fully evaluated
        :param itemIndex: Zero based index of the item
        :return: Boolean
        """
        if self.executionState.kind != Kind.sExpression:
            self.throwError("Tried to evaluate a subitem of a value that isnt an s expression. Engine error.")
        if itemIndex >= len(self.executionState.value):
            self.throwError("Tried to evaluate a subitem that is out of range. Engine error.")
        item = self.executionState.value[itemIndex]
        return item.kind is not Kind.sExpression and not isIndirectionValue(item)

    def SubEvaluate(self, itemIndex) -> StackFrame:
        """
        Evaluates an item in a given location via a new stackframe, and dereferences any indirection.
        For use in special forms
        :param itemIndex:
        :return:
        """
        if self.isFullyEvaluated(itemIndex):
            self.throwError("Item is already fully evaluated. Engine error.")
        item = self.executionState.value[itemIndex]
        if item.kind == Kind.sExpression:
            oldFrame = self.withExecutionState(sExpression(
                self.executionState.value[:itemIndex] + [StackReturnValue()] + self.executionState.value[itemIndex + 1:]
            ))
            newStack = oldFrame.createChild(item)
            return newStack

        # its indirection
        trueValue = dereference(self.withExecutionState(item))
        return self.withExecutionState(sExpression(
            self.executionState.value[:itemIndex] + [trueValue] + self.executionState.value[itemIndex + 1:]
        ))

    #Scope logic

    def getChildReturnValue(self):
        if self.__childReturnValue__ is None:
            self.throwError("No child to return found. Engine bug")
        return self.__childReturnValue__

    def withChildReturnValue(self, value):
        copy = self.__copy__()
        copy.__childReturnValue__ = value
        return copy

    def hasScopedRegularValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        return self.currentScope.hasScopedRegularValue(name)

    def retrieveScopedRegularValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        return self.currentScope.retrieveScopedRegularValue(self, name)

    def hasScopedMacroValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        return self.currentScope.hasScopedMacroValue(name)

    def retrieveScopedMacroValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        return self.currentScope.retrieveScopedMacroValue(self, name)

    def addScopedMacroValue(self, name, value) -> StackFrame:
        copy = self.__copy__()
        copy.currentScope = self.currentScope.addScopedMacroValue(self, name, value)
        return copy

    def addScopedRegularValue(self, name, value) -> StackFrame:
        copy = self.__copy__()
        copy.currentScope = self.currentScope.addScopedRegularValue(self, name, value)
        return copy

    #Handler logic

    def withHandlerFrame(self, handlerFrame: HandlerFrame) -> StackFrame:
        copy = self.__copy__()
        copy.closestHandlerFrame = handlerFrame
        return copy

    def hasHandler(self, name):
        if self.closestHandlerFrame is not None:
            return self.closestHandlerFrame.hasHandler(name)
        return False

    def invokeHandler(self, name, args) -> StackFrame:
        return self.closestHandlerFrame.invokeHandler(self, name, args)

    #Utility logic

    def errorDumpSerialize(self):
        return langConfig.currentScopeKeyword

    def debugStateToString(self):
        return self.executionState.errorDumpSerialize()

    def __stackTrace__(self):
        if self.parent is not None:
            self.parent.__stackTrace__()
        if isinstance(self.executionState, list):
            i=10
        cprint("\tat: " + self.executionState.errorDumpSerialize(), color="red")

    def throwError(self, errorMessage):
        cprint("Error while evaluating code.", color="red")
        cprint(errorMessage, color="red")
        self.__stackTrace__()
        raise RuntimeEvaluationError("Runtime error")

    def equals(self, other):
        self.throwError("Cannot equality compare stackframes (yet)")


#Exception class


class RuntimeEvaluationError(Exception):
    pass

#Import classes


class PythonImportData:
    def __init__(self, libraryPath: str, values: [(str, str)]):
        """
        Data to import regular values from a python file
        :param libraryPath: Absolute path to the library file from the root of the interpreter
        :param values: A string tuple, indicating the original name and the name to import it as
        """
        self.libraryPath = libraryPath
        self.importValues = values

