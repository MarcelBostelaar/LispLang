from Evaluator.SupportFunctions import MustBeKind
from Evaluator.Classes import List, Kind, SystemFunction, Boolean, StackFrame, StackReturnValue


def head(somelist: List):
    MustBeKind(somelist, "Head can only operate on lists", Kind.List)
    return somelist.value[0]


def tail(somelist: List):
    MustBeKind(somelist, "Head can only operate on lists", Kind.List)
    if len(somelist.value) == 0:
        raise "Cannot get tail of a zero with list"
    return List(somelist.value[1:])


def concat(listA, listB):
    MustBeKind(listA, "concat can only operate on lists", Kind.List)
    MustBeKind(listB, "concat can only operate on lists", Kind.List)
    return listA.concat(listB)


def equals(A, B):
    return Boolean(A.equals(B))


standardLibrary = {
    "head": SystemFunction(head, 1),
    "tail": SystemFunction(tail, 1),
    "concat": SystemFunction(concat, 2),
    "equals": SystemFunction(equals, 2)
}


def makeStartingFrame():
    frame = StackFrame(StackReturnValue())
    for funcname, func in standardLibrary.items():
        frame = frame.addScopedRegularValue(funcname, func)
    return frame


outerDefaultRuntimeFrame = makeStartingFrame()
