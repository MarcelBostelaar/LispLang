from __future__ import annotations

from copy import copy as makeCopy
import functools
from enum import Enum
from typing import TYPE_CHECKING

from termcolor import cprint

from LispLangInterpreter.DataStructures.ClassesSupportFunctions import checkReservedKeyword, escape_string

from .IErrorThrowable import IErrorThrowable
from .Kind import Kind
from ..Config import langConfig
from .HandlerStateRegistry import HandlerStateSingleton
from .SupportFunctions import isIndirectionValue, isSpecialFormKeyword
if TYPE_CHECKING:
    from ..ImportHandlerSystem.LibraryClasses import Searchable


#Put this here because of circular imports, python is shit
def dereference(currentFrame: StackFrame) -> Value:
    """Retrieves the real value, resolving any indirection"""
    if not isIndirectionValue(currentFrame.executionState):
        currentFrame.throwError("Cannot dereference this value, its not an indirected value.")
    item = currentFrame.executionState
    if item.kind == Kind.Reference:
        if currentFrame.hasScopedRegularValue(item.value):
            return [currentFrame.retrieveScopedRegularValue(item.value)]
        if currentFrame.hasScopedMacroValue(item.value):
            return [MacroReference(item.value)]
        if isSpecialFormKeyword(item.value):
            currentFrame.throwError("Tried to execute special form, but item is a singular reference, "
                                    "not in an s expression or on its own.")
        currentFrame.throwError("Reference not found in scope")
    if item.kind == Kind.StackReturnValue:
        return [currentFrame.getChildReturnValue()]
    if item.kind == Kind.MacroReturnValue:
        #macros are expanded in place, and must always be a list
        childreturn = currentFrame.getChildReturnValue()
        if childreturn.kind != Kind.List:
            raise Exception("Macros must always return a list! Returned a " + childreturn.kind + " instead.")
        return childreturn.value
    if item.kind == Kind.HandleReturnValue:
        stateValue = HandlerStateSingleton.retrieveState(item.handlerID)
        childReturnValue = currentFrame.getChildReturnValue()
        if childReturnValue is None:
            raise NotImplementedError("Return unit or none")
        returnValue = List([childReturnValue, stateValue])
        HandlerStateSingleton.unregisterHandlerFrame(item.handlerID)
        return [returnValue]
    #All other cases, return value as is (with extra list wrap to fascilitate macro unboxing).
    return [item]


class Value:
    """Abstract class for any value, must be subtyped"""

    def __init__(self, value, kind: Kind):
        self.value = value
        self.kind = kind
        self.dereferencedName = ""

    def serializeLLQ(self):
        raise Exception("Cannot serialise a " + self.kind.name)

    def errorDumpSerialize(self):
        if self.dereferencedName == "":
            return self.serializeLLQ()
        return self.serializeLLQ() + "<" + self.dereferencedName + ">"

    def isSerializable(self):
        return False

    def equals(self, other):
        raise NotImplementedError("Not implemented equality for this class")
    
    """Sets a name for debugging purposes, sets it when value is retrieved"""
    def setDereferencedName(self, newName):
        copy = makeCopy(self)
        copy.dereferencedName = newName
        return copy


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
        raise "Cannot call equals on a reference value (running code), engine error"  #TODO why?

    def errorDumpSerialize(self):
        return "*" + self.value

class MacroReference(Value):
    """Represents a named reference that needs to be evaluated"""

    def __init__(self, value):
        super().__init__(value, Kind.MacroReference)

    def equals(self, other):
        # References should be evaluated to their value when passed to a function
        raise "Cannot call equals on a reference value (running code), engine error" #TODO why?

    def errorDumpSerialize(self):
        if self.dereferencedName == "":
            return "*M*" + self.value
        return "*M*" + self.value + "<" + self.dereferencedName + ">"

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

    def __init__(self, bindings, body, boundScope: Scope, bindIndex=0, dereferencedName = ""):
        super().__init__()
        self.bindingNames = bindings  # function arguments
        self.body = body  # the code to execute
        # Contains its own scope, equal to the scope captured at creation
        self.boundScope = boundScope
        self.bindIndex = bindIndex  # index of the arg that will bind next
        self.dereferencedName = dereferencedName

    def __bindIsFinished__(self):
        return self.bindIndex >= len(self.bindingNames)

    def bind(self, valueToBind, callingFrame: StackFrame) -> UserLambda:
        if self.__bindIsFinished__():
            callingFrame.throwError("Tried to bind fully bound lambda. Engine error.")
        bound = self.boundScope.addScopedRegularValue(callingFrame, self.bindingNames[self.bindIndex], valueToBind)
        return UserLambda(self.bindingNames, self.body, bound, bindIndex=self.bindIndex + 1, dereferencedName=self.dereferencedName)

    def canRun(self) -> bool:
        return self.__bindIsFinished__()

    def createEvaluationFrame(self, callingFrame) -> StackFrame:
        if not self.canRun():
            callingFrame.throwError("Tried to run a lambda that still needs arguments bound. Engine error.")
        newFrame = callingFrame.createChild(self.body)
        newFrame.currentScope = self.boundScope
        return newFrame

    def equals(self, other):
        return super(UserLambda, self).equals(other)

    def errorDumpSerialize(self):
        i = "UserLambda"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"


class SystemFunction(Lambda):
    """In memory representation of a system function"""

    def __init__(self, function, bindingsLeft, dereferencedName = ""):
        super().__init__()
        self.function = function
        self.bindingsLeft = bindingsLeft
        self.dereferencedName = dereferencedName

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
        return SystemFunction(functools.partial(self.function, argument), self.bindingsLeft - 1, self.dereferencedName)

    def errorDumpSerialize(self):
        i = "SystemFunction"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"


class UnfinishedHandlerInvocation(Lambda):
    """In memory representation of an unfinished handler invocation,
    acts akin to a type definition for an effectfull function."""
    def __init__(self, name: str, argAmount: int, dereferencedName = ""):
        super().__init__()
        self.name = name
        """The handler name it references"""
        self.argAmount = argAmount
        """Total amount of args needed for invocation"""
        self.args = []
        self.dereferencedName

    def bind(self, argument, callingFrame: StackFrame) -> UnfinishedHandlerInvocation:
        if self.canRun():
            callingFrame.throwError(f"Too many arguments added to the unfinished handler invocation '{self.name}'")
        copy = UnfinishedHandlerInvocation(self.name, self.argAmount, self.dereferencedName)
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
        i = f"UnfinishedHandlerInvocation<{self.name}, with: {', '.join([x.errorDumpSerialize() for x in self.args])}>"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"

    def equals(self, other):
        raise NotImplementedError("")


#Stack and control flow classes


class HandleReturnValue(Value):
    def __init__(self, handlerID):
        super().__init__(None, Kind.HandleReturnValue)
        self.handlerID = handlerID

    def errorDumpSerialize(self):
        i = f"HandleReturnValue<{self.handlerID}>"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"

    def equals(self, other):
        raise NotImplementedError("")


class HandleBranchPoint(Value):
    def __init__(self, handlerID: int, continueBranch=None):
        super().__init__(None, Kind.HandleBranchPoint)
        self.continueBranch = continueBranch
        self.handlerID = handlerID

    def errorDumpSerialize(self):
        addon = ""
        if self.dereferencedName != "":
            addon = "<" + self.dereferencedName + ">"
        if self.continueBranch is not None:
            return f"\n" \
                   f"HandleBranchPoint with continue branch. Continue branch:" +\
                   self.continueBranch.errorDumpSerialize() + addon +\
                   f"\n"
        else:
            return f"\n" \
                   f"HandleBranchPoint without continue branch." + addon +\
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
        self.scopedNames = {}
        self.scopedValues = {}
        self.currentFile = currentFile

    def hasScopedRegularValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        if name == langConfig.currentScopeKeyword:
            return True
        if name in self.scopedNames.keys():
            return self.scopedNames[name] == VarType.Regular
        return False

    def retrieveScopedRegularValue(self, callingFrame: StackFrame, name: str) -> Value:
        # Do not check parents, because parent can be a non-captured outer scope
        if name == langConfig.currentScopeKeyword:
            return self
        if not self.hasScopedRegularValue(name):
            if name not in self.scopedNames.keys():
                callingFrame.throwError("Tried to retrieve regular value " + name + ". Value was not found in scope.")
            else:
                callingFrame.throwError("Tried to retrieve regular value " + name +
                                        ". This value is a " + self.scopedNames[
                                            name].name + " value, not a regular value.")
        return self.scopedValues[name].setDereferencedName(name)

    def hasScopedMacroValue(self, name):
        # Do not check parents, because parent can be a non-captured outer scope
        if name in self.scopedNames.keys():
            if self.scopedNames[name] == VarType.Macro:
                return True
        return False

    def retrieveScopedMacroValue(self, callingFrame: StackFrame, name) -> Value:
        # Do not check parents, because parent can be a non-captured outer scope
        if not self.hasScopedMacroValue(name):
            callingFrame.throwError("Tried to retrieve macro '" + name + "'. Macro not found in scope.")
        return self.scopedValues[name].setDereferencedName(name)

    def addScopedMacroValue(self, callingFrame: StackFrame, name, value) -> Scope:
        checkReservedKeyword(callingFrame, name)
        copy = self.__copy__()
        copy.scopedNames[name] = VarType.Macro
        copy.scopedValues[name] = value
        return copy

    def addScopedRegularValue(self, callingFrame: StackFrame, name, value) -> Scope:
        checkReservedKeyword(callingFrame, name)
        copy = self.__copy__()
        copy.scopedNames[name] = VarType.Regular
        copy.scopedValues[name] = value
        return copy

    def __copy__(self) -> Scope:
        copy = Scope(self.currentFile)
        copy.scopedNames = self.scopedNames
        copy.scopedValues = self.scopedValues
        return copy

    def errorDumpSerialize(self):
        i = "[Captured scope]"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"

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
        i = f"SystemHandlerFrame[<]{', '.join(self.handlerFunctions.keys())}]"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"

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
        i = "[Captured handler frame]"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"

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
        i = "StackReturnValue"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"

class MacroReturnValue(Value):
    def __init__(self):
        super().__init__(None, Kind.MacroReturnValue)

    def equals(self, other):
        raise "Cannot call equals on a stack return value (running code), engine error"

    def errorDumpSerialize(self):
        i = "MacroReturnValue"
        if self.dereferencedName == "":
            return i
        return i + "<" + self.dereferencedName + ">"


def subevaluateMacro(currentFrame: StackFrame, itemIndex):
    item = currentFrame.executionState.value[itemIndex]
    #subevaluate macro with all the code from itemindex forward
    #retrieving lambda
    macroLambda = currentFrame.retrieveScopedMacroValue(item.value)
    #binding current scope and ast available to macro to the body of the macro
    macroLambda = macroLambda\
        .bind(currentFrame.currentScope, currentFrame)\
        .bind(List(currentFrame.executionState.value[itemIndex + 1:]), currentFrame)
    #add macro return value, then append macro lambda as child
    oldFrame = currentFrame.withExecutionState(sExpression(
        currentFrame.executionState.value[:itemIndex] + [MacroReturnValue()]
    ))
    return macroLambda.createEvaluationFrame(oldFrame)

class StackFrame(IErrorThrowable):
    """A frame in the stack that contains the scoped names, values and handlers, as well as a link to its parent"""

    def __init__(self, executionState, currentFile: Searchable):
        self.executionState = executionState
        """Read only. Current code being operated on in this frame."""
        self.parent = None
        """Read only. Parent stack frame of this stack."""
        self.closestHandlerFrame = None
        """Handler stack is seperate, code stack only keeps track of which stack is reachable to it. 
        Other interactions are done through the evaluator code."""
        self.childReturnValue = None
        self.currentScope = Scope(currentFile)

    def __copy__(self) -> StackFrame:
        newcopy = StackFrame(self.executionState, self.currentScope.currentFile)
        newcopy.currentScope = self.currentScope.__copy__()
        newcopy.closestHandlerFrame = self.closestHandlerFrame
        newcopy.childReturnValue = self.childReturnValue
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

        if item.kind == Kind.MacroReference:
            return subevaluateMacro(self, itemIndex)
            
        # its indirection
        trueValue = dereference(self.withExecutionState(item))
        return self.withExecutionState(sExpression(
            self.executionState.value[:itemIndex] + trueValue + self.executionState.value[itemIndex + 1:]
        ))

    #Scope logic

    def getChildReturnValue(self):
        if self.childReturnValue is None:
            self.throwError("No child to return found. Engine bug")
        return self.childReturnValue

    def withChildReturnValue(self, value):
        copy = self.__copy__()
        copy.childReturnValue = value
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

    def retrieveScopedMacroValue(self, name) -> UserLambda:
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

