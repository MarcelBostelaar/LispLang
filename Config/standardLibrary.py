import string
import uuid

from Config.langConfig import continueKeyword, stopKeyword
from Evaluator.SupportFunctions import MustBeKind
from Evaluator.Classes import List, Kind, SystemFunction, Boolean, StackFrame, StackReturnValue, Number, ContinueStop, \
    UnfinishedHandlerInvocation, Unit, SystemHandlerFrame, QuotedName, Reference, sExpression


def head(somelist: List, callingFrame: StackFrame):
    MustBeKind(callingFrame, somelist, "Head can only operate on lists", Kind.List)
    return somelist.value[0]


def tail(somelist: List, callingFrame: StackFrame):
    MustBeKind(callingFrame, somelist, "Head can only operate on lists", Kind.List)
    if len(somelist.value) == 0:
        raise "Cannot get tail of a zero with list"
    return List(somelist.value[1:])


def concat(listA, listB, callingFrame: StackFrame):
    MustBeKind(callingFrame, listA, "concat can only operate on lists", Kind.List)
    MustBeKind(callingFrame, listB, "concat can only operate on lists", Kind.List)
    return listA.concat(listB)


def equals(A, B, callingFrame: StackFrame):
    return Boolean(A.equals(B))


def sum(A, B, callingFrame: StackFrame):
    MustBeKind(callingFrame, A, "sum can only add numbers", Kind.Number)
    MustBeKind(callingFrame, B, "sum can only add numbers", Kind.Number)
    return Number(A.value + B.value)


def continueStop(isContinue):
    def internal(returnValue, newState, callingFrame: StackFrame):
        return ContinueStop(isContinue, returnValue, newState)
    return internal


def handlerInvocationDefinition(name, length, callingFrame: StackFrame):
    MustBeKind(callingFrame, name, "Handler invocation definition must give as the first argument, the handled name as a quoted name", Kind.QuotedName)
    MustBeKind(callingFrame, length, "Handler invocation definition must give as second argument, its length with a number", Kind.Number)
    if length.value < 1:
        callingFrame.throwError("Length of handler invocation definition must be 1 or higher")
    if not length.value.is_integer():
        callingFrame.throwError("Length of handler invocation definition must be a whole number")
    return UnfinishedHandlerInvocation(name.value, length.value)


def isString(value):
    if value.kind is not Kind.List:
        return False
    for i in value.value:
        if i.Kind is not Kind.Char:
            return False
    return True


def printFunction(value, callingFrame: StackFrame):
    if value.kind in [Kind.Number, Kind.Boolean]:
        print(value.value)
    elif isString(value):
        print("".join([x.value for x in value.value]))
    else:
        callingFrame.throwError("Unsupported type to print")
    return Unit()


def symGenFunction(_, callingFrame):
    id = uuid.uuid4()
    id = id.__str__()
    return QuotedName("generatedSymbol_" + "".join([x for x in id if x in string.ascii_letters + "0123456789"]))


implementedHandlers = {
    "print": SystemFunction("print", printFunction, 1),
    "gensym": SystemFunction("gensym", symGenFunction, 1)
}

standardLibrary = {
    "head": SystemFunction("head", head, 1),
    "tail": SystemFunction("tail", tail, 1),
    "concat": SystemFunction("concat", concat, 2),
    "equals": SystemFunction("equals", equals, 2),
    "sum": SystemFunction("sum", sum, 2),
    continueKeyword: SystemFunction(continueKeyword, continueStop(True), 2),
    stopKeyword: SystemFunction(stopKeyword, continueStop(False), 2),
    "declareEffectfulFunction": SystemFunction("declareEffectfulFunction", handlerInvocationDefinition, 2),
    "isString": SystemFunction("isString", lambda v, c: Boolean(isString(v)), 1)
}


def makeNormalStartingFrame():
    frame = StackFrame(StackReturnValue())
    for i in implementedHandlers.keys():
        frame = frame.addScopedRegularValue(i, handlerInvocationDefinition(
            QuotedName(i),
            Number(float(implementedHandlers[i].bindingsLeft)), frame)
        )
    for funcname, func in standardLibrary.items():
        frame = frame.addScopedRegularValue(funcname, func)
    handler = SystemHandlerFrame()
    for i in implementedHandlers.keys():
        handler = handler.addHandler(i, implementedHandlers[i])
    return frame.withHandlerFrame(handler)


def makeDemacroStartingFrame():
    frame = StackFrame(StackReturnValue())
    for funcname, func in standardLibrary.items():
        frame = frame.addScopedRegularValue(funcname, func)
    return frame


outerDefaultRuntimeFrame = makeNormalStartingFrame()

demacroOuterDefaultRuntimeFrame = makeDemacroStartingFrame()