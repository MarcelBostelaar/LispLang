import string
import uuid

from LispLangInterpreter.Evaluator.SupportFunctions import MustBeKind
from LispLangInterpreter.DataStructures.Classes import List, Kind, SystemFunction, Boolean, StackFrame, Number, ContinueStop, \
    UnfinishedHandlerInvocation, Unit, QuotedName


def headf(somelist: List, callingFrame: StackFrame):
    MustBeKind(callingFrame, somelist, "Head can only operate on lists", Kind.List)
    return somelist.value[0]
head = SystemFunction(headf, 1)


def tailf(somelist: List, callingFrame: StackFrame):
    MustBeKind(callingFrame, somelist, "Head can only operate on lists", Kind.List)
    if len(somelist.value) == 0:
        raise "Cannot get tail of a zero with list"
    return List(somelist.value[1:])
tail = SystemFunction(tailf, 1)

def concatf(listA, listB, callingFrame: StackFrame):
    MustBeKind(callingFrame, listA, "concat can only operate on lists", Kind.List)
    MustBeKind(callingFrame, listB, "concat can only operate on lists", Kind.List)
    return listA.concat(listB)
concat = SystemFunction(concatf, 2)


def equalsf(A, B, callingFrame: StackFrame):
    return Boolean(A.equals(B))
equals = SystemFunction(equalsf, 2)


def sumf(A, B, callingFrame: StackFrame):
    MustBeKind(callingFrame, A, "sum can only add numbers", Kind.Number)
    MustBeKind(callingFrame, B, "sum can only add numbers", Kind.Number)
    return Number(A.value + B.value)
sum = SystemFunction(sumf, 2)


def continueStop(isContinue):
    def internal(returnValue, newState, callingFrame: StackFrame):
        return ContinueStop(isContinue, returnValue, newState)
    return internal
continue_ = SystemFunction(continueStop(True), 2)
stop_ = SystemFunction(continueStop(False), 2)


def handlerInvocationDefinitionf(name, length, callingFrame: StackFrame):
    MustBeKind(callingFrame, name, "Handler invocation definition must give as the first argument, the handled name as a quoted name", Kind.QuotedName)
    MustBeKind(callingFrame, length, "Handler invocation definition must give as second argument, its length with a number", Kind.Number)
    if length.value < 1:
        callingFrame.throwError("Length of handler invocation definition must be 1 or higher")
    if not length.value.is_integer():
        callingFrame.throwError("Length of handler invocation definition must be a whole number")
    return UnfinishedHandlerInvocation(name.value, length.value)
handlerInvocationDefinition = SystemFunction(handlerInvocationDefinitionf, 2)

def isStringf(value):
    if value.kind is not Kind.List:
        return False
    for i in value.value:
        if i.Kind is not Kind.Char:
            return False
    return True
isString = SystemFunction(isStringf, 1)


def printFunctionf(value, callingFrame: StackFrame):
    if value.kind in [Kind.Number, Kind.Boolean]:
        print(value.value)
    elif isString(value):
        print("".join([x.value for x in value.value]))
    else:
        callingFrame.throwError("Unsupported type to print")
    return Unit()
printFunction = SystemFunction(printFunctionf, 1)


def symGenFunction(_, callingFrame):
    id = uuid.uuid4()
    id = id.__str__()
    return QuotedName("generatedSymbol_" + "".join([x for x in id if x in string.ascii_letters + "0123456789"]))
genSym = SystemFunction(symGenFunction, 1)