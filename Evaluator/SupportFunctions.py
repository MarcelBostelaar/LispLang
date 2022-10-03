from Config.langConfig import SpecialForms
from Evaluator.Classes import Kind, sExpression, Reference, StackFrame, Value, List, QuotedName


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


def dereference(currentFrame: StackFrame) -> Value:
    """Retrieves the real value, resolving any indirection"""
    item = currentFrame.executionState
    if item.kind == Kind.Reference:
        if currentFrame.hasScopedRegularValue(item.value):
            return currentFrame.retrieveScopedRegularValue(item.value)
        # TODO check for handlers here
        if isSpecialFormKeyword(item.value):
            currentFrame.throwError("Tried to execute special form, but item is a singular reference, "
                                    "not in an s expression or on its own.")
        currentFrame.throwError("Reference not found in scope")
    if item.kind == Kind.StackReturnValue:
        return currentFrame.getChildReturnValue()
    #All other cases, return value as is.
    return item


def isSpecialFormKeyword(name) -> bool:
    return name in [e.value.keyword for e in SpecialForms]


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


def QuoteCode(frame: StackFrame, expression):
    if expression.kind == Kind.sExpression:
        return List([QuoteCode(frame, x) for x in expression.value])
    if expression.kind == Kind.Reference:
        return QuotedName(expression.value)
    if expression.kind in [Kind.List, Kind.Lambda, Kind.Scope]:
        frame.throwError("Engine error, cannot be quoted, in rewrite dont distinguish s expressions and lists")
    return expression


def SpecialFormSlicer(frame: StackFrame, formConfig: SpecialForms):
    length = formConfig.value.length
    if len(frame.executionState.value) < length:
        frame.throwError("Special form " + frame.executionState.value[0].value + " must have at least "
                         + str(length) + " items arguments, only has " + str(len(frame.executionState.value)))
    return [frame.executionState.value[:length], frame.executionState.value[length:]]
