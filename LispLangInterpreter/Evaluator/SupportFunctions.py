from ..Config.langConfig import SpecialForms
from ..DataStructures.Classes import sExpression, Reference, StackFrame, Value, List, QuotedName
from ..DataStructures.Kind import Kind


def toAST(LLQ):
    """
    Takes an LLQ and turns it into the interpreter representation of executable AST
    :param LLQ: List, Literal, Quoted names AST
    :return: The AST as s-expressions and unquoted names
    """
    if LLQ.kind == Kind.List:
        return sExpression([toAST(x) for x in LLQ.value])
    if LLQ.kind == Kind.QuotedName:
        return Reference(LLQ.value)
    return LLQ


def MustBeKind(containingStack: StackFrame, expression, message: str, *kinds: [Kind]):
    """
    Error check for all allowed types of an expression
    :param containingStack:
    :param expression:
    :param message:
    :param kinds:
    :return:
    """
    if expression.kind in kinds:
        return
    containingStack.throwError(message + "\nIt has type " + expression.kind.name)


def MustBeString(containingStack: StackFrame, expression, message: str):
    if expression.kind != Kind.List:
        containingStack.throwError(message + "\nIt has type " + expression.kind.name)
    for i in expression.value:
        if i.kind != Kind.Char:
            containingStack.throwError(message + "\nIt contains type " + i.kind.name)
    return


def QuoteCode(frame: StackFrame, expression):
    if expression.kind == Kind.sExpression:
        return List([QuoteCode(frame, x) for x in expression.value])
    if expression.kind == Kind.Reference:
        return QuotedName(expression.value)
    if expression.kind not in [Kind.Char, Kind.Number, Kind.Boolean]:
        frame.throwError("Engine error, cannot be quoted, in rewrite dont distinguish s expressions and lists")
    return expression


def SpecialFormSlicer(frame: StackFrame, formConfig: SpecialForms):
    length = formConfig.value.length
    if len(frame.executionState.value) < length:
        frame.throwError("Special form " + frame.executionState.value[0].value + " must have at least "
                         + str(length) + " items arguments, only has " + str(len(frame.executionState.value)))
    return [frame.executionState.value[:length], frame.executionState.value[length:]]


