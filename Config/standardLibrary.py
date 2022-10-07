from Evaluator.SupportFunctions import MustBeKind
from Evaluator.Classes import List, Kind, SystemFunction, Boolean, StackFrame, StackReturnValue, Number


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



standardLibrary = {
    "head": SystemFunction(head, 1),
    "tail": SystemFunction(tail, 1),
    "concat": SystemFunction(concat, 2),
    "equals": SystemFunction(equals, 2),
    "sum": SystemFunction(sum, 2)
}


def makeStartingFrame():
    frame = StackFrame(StackReturnValue())
    for funcname, func in standardLibrary.items():
        frame = frame.addScopedRegularValue(funcname, func)
    return frame


outerDefaultRuntimeFrame = makeStartingFrame()
