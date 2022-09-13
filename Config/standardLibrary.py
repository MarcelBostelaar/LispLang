from Evaluator.Evaluator import MustBeKind
from Evaluator.Classes import List, Kind, SystemFunction, Scope


def head(somelist: List):
    MustBeKind(somelist, "Head can only operate on lists", Kind.List)
    return somelist.value[0]


def tail(somelist: List):
    MustBeKind(somelist, "Head can only operate on lists", Kind.List)
    if len(somelist.value) == 0:
        raise "Cannot get tail of a zero with list"
    return List(somelist.value[1:])


standardLibrary = {
    "head": SystemFunction(head, 1),
    "tail": SystemFunction(tail, 1)
}


def makeStandardScope():
    scope = Scope()
    for funcname, func in standardLibrary.items():
        scope = scope.addValue(funcname, func)
    return scope


standardScope = makeStandardScope()
