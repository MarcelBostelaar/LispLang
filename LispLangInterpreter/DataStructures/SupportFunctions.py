from __future__ import annotations

from .Classes import *
from .Kind import Kind
from ..Config import langConfig
from ..Config.Singletons import writeLineLog
from ..Config.langConfig import SpecialForms


def checkReservedKeyword(callingFrame: StackFrame, name):
    if name in langConfig.reservedWords:
        callingFrame.throwError("Tried to override the reserved keyword '" + name + "'. Now allowed.")


def escape_string(string):
    writeLineLog("TODO implement string escaping")  # todo
    return string


def isSpecialFormKeyword(name) -> bool:
    return name in [e.value.keyword for e in SpecialForms]


def isIndirectionValue(someValue: Value):
    return someValue.kind in [Kind.Reference, Kind.StackReturnValue, Kind.HandleReturnValue]


def dereference(currentFrame: StackFrame) -> Value:
    """Retrieves the real value, resolving any indirection"""
    if not isIndirectionValue(currentFrame.executionState):
        currentFrame.throwError("Cannot dereference this value, its not an indirected value.")
    item = currentFrame.executionState
    if item.kind == Kind.Reference:
        if currentFrame.hasScopedRegularValue(item.value):
            return currentFrame.retrieveScopedRegularValue(item.value)
        if isSpecialFormKeyword(item.value):
            currentFrame.throwError("Tried to execute special form, but item is a singular reference, "
                                    "not in an s expression or on its own.")
        currentFrame.throwError("Reference not found in scope")
    if item.kind == Kind.StackReturnValue:
        return currentFrame.getChildReturnValue()
    if item.kind == Kind.HandleReturnValue:
        stateValue = HandlerStateSingleton.retrieveState(item.handlerID)
        childReturnValue = currentFrame.getChildReturnValue()
        if childReturnValue is None:
            raise NotImplementedError("Return unit or none")
        returnValue = List([childReturnValue, stateValue])
        HandlerStateSingleton.unregisterHandlerFrame(item.handlerID)
        return returnValue
    #All other cases, return value as is.
    return item