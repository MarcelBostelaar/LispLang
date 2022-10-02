from Evaluator.Classes import sExpression, Kind, Reference, List, QuotedName, UserLambda, StackFrame, Value, \
    StackReturnValue
from Config.langConfig import *

"""Only operates on demacroed code"""


def stringify(sExpression):
    return "Error stringification not implemented"


# def ThrowAnError(message, currentExpression=None):
#     if currentExpression is None:
#         raise Exception(message)
#     raise Exception(message + "\nLine: " + stringify(currentExpression))


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

# TODO creates new stack frame
def EvalLambda(expression, currentScope):
    head = expression.value[0]
    tail = expression.value[1:]
    #   apply Eval(second arg) to it,
    #   check if its fully bound,
    #       eval and replace if so,
    #   restart loop
    tailhead = tail[0]
    truetail = tail[1:]
    evaluated = Eval(tailhead, currentScope)
    applied = head \
        .bind(evaluated) \
        .run(Eval)
    expression = sExpression([applied] + truetail)
    return [expression, currentScope]


def Dereference(currentFrame: StackFrame) -> StackFrame:
    head = currentFrame.executionState.value[0]
    tail = currentFrame.executionState.value[1:]

    if currentFrame.hasScopedRegularValue(head.value):
        head = currentFrame.retrieveScopedRegularValue(head.value)
        expression = sExpression([head] + tail)
        return currentFrame.withExecutionState(expression)
    #TODO check for handlers here
    if isSpecialFormKeyword(head.value):
        return ExecuteSpecialForm(currentFrame)

    currentFrame.throwError("Could not find reference " + head.value + ".")



def isSpecialFormKeyword(name) -> bool:
    return name in [e.value.keyword for e in SpecialForms]


def MustHaveLength(expression, N):
    if len(expression.value) < N:
        ThrowAnError("Special form " + expression.value[0].value + " must have at least "
                     + str(N) + " items arguments, only has " + str(len(expression.value)))


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


def QuoteCode(expression):
    if expression.kind == Kind.sExpression:
        return List([QuoteCode(x) for x in expression.value])
    if expression.kind == Kind.Reference:
        return QuotedName(expression.value)
    if expression.kind in [Kind.List, Kind.Lambda, Kind.Scope]:
        ThrowAnError("Engine error, cannot be quoted, in rewrite dont distinguish s expressions and lists", expression)
    return expression


def SpecialFormSlicer(expression, formConfig: SpecialForms):
    length = formConfig.value.length
    MustHaveLength(expression, length)
    return [expression.value[:length], expression.value[length:]]


def ExecuteSpecialForm(currentFrame: StackFrame) -> StackFrame:
    name = currentFrame.executionState.value[0].value
    if name == SpecialForms.Lambda.value.keyword:
        [[_, args, body], rest] = SpecialFormSlicer(currentFrame.executionState, SpecialForms.Lambda)
        lambdaerr = "First arg after lambda must be a flat list/s expression of names"
        MustBeKind(currentFrame, args, lambdaerr, Kind.sExpression, )
        [MustBeKind(currentFrame, x, lambdaerr, Kind.Reference) for x in args.value]
        MustBeKind(currentFrame, body, "Body of a lambda must be an s expression or a single name",
                   Kind.sExpression, Kind.Reference)
        return currentFrame.withExecutionState(
            sExpression([UserLambda([z.value for z in args.value], body, currentFrame.captured())] + rest)
        )

    if name == SpecialForms.macro.value.keyword:
        #ignore for this implementation, interpreter doesn't support eval yet
        [_, rest] = SpecialFormSlicer(currentFrame.executionState, SpecialForms.macro)
        return currentFrame.withExecutionState(rest)

    if name == SpecialForms.let.value.keyword:
        [[let, name, value], tail] = SpecialFormSlicer(currentFrame.executionState, SpecialForms.let)
        MustBeKind(currentFrame, name, "The first arg after a let must be a name", Kind.Reference)

        if value.kind == Kind.sExpression:
            # Item needs to be further evaluated
            x = sExpression([let, name, StackReturnValue()] + tail.value)
            updatedParent = currentFrame.withExecutionState(x)  # replace item with return value placeholder
            newFrame = StackFrame(value, parent=updatedParent)  # create child stack to calculate result
            return newFrame
        else:
            value = Eval(currentFrame.withExecutionState(value))  # retrieve the raw value
        return currentFrame.addScopedRegularValue(name.value, value).withExecutionState(tail)

    if name == SpecialForms.quote.value.keyword:
        #quotes item directly after it
        [[_, snd], tail] = SpecialFormSlicer(currentFrame.executionState, SpecialForms.quote)
        newSnd = QuoteCode(snd)
        return currentFrame.executionState(sExpression([newSnd] + tail))

    if name == SpecialForms.list.value.keyword:
        #treats the list behind it as a list rather than an s expression
        [[_, snd], tail] = SpecialFormSlicer(expression, SpecialForms.quote)
        MustBeKind(snd, "Item after list must be a list", Kind.sExpression)
        newSnd = List([Eval(x, currentScope) for x in snd.value])
        return [sExpression([newSnd] + tail), currentScope]

    if name == SpecialForms.cond.value.keyword:
        #eval condition, if true, return true unevaluated, else return falsepath unevaluated
        [[_, condition, truePath, falsePath], tail] = SpecialFormSlicer(expression, SpecialForms.cond)
        evaluated = Eval(condition, currentScope)
        MustBeKind(evaluated, "Tried to evaluate an conditional, value to evaluate not a boolean", Kind.Boolean)
        if evaluated.value:
            return [sExpression([truePath] + tail), currentScope]
        return [sExpression([falsePath] + tail), currentScope]

    ThrowAnError("Unknown special form (engine bug)", expression)


# TODO creates new stack frame
def Eval(currentFrame: StackFrame) -> Value:
    """
    Evaluates a piece of interpreter representational code
    :param expression: s Expression and/or value
    :param currentStack: Current stack of execution
    :return: Return value of the calculation
    """
    # continue statements used to achieve tail call optimisation, and to keep stack usage to a minimum
    while True:
        if currentFrame.executionState.kind != Kind.sExpression:
            if currentFrame.executionState.kind == Kind.Reference:
                currentFrame = Dereference(currentFrame)
                continue
            if currentFrame.executionState.kind == Kind.StackReturnValue:
                currentFrame = currentFrame.withExecutionState(currentFrame.getChildReturnValue())
                continue
            return currentFrame.executionState

        ##its an s expression
        # if 0 children, error, cant execute
        # if 1 child, extract child, restart loop
        if len(expression.value) == 0:
            ThrowAnError("Cant evaluate an s expression with 0 items in it")
        if len(expression.value) == 1:
            expression = expression.value[0]
            currentScope = currentScope
            continue

        ## two or more
        # if head if reference (a name)
        # if head is reference in scope, replace with its value from scope
        # (dereferencing is done before special forms to allow scoped overrides of special forms.
        # This makes special forms undistinct from macro forms from a user perspective,
        # which can also be scoped overridden)
        # if head is reference of special form, execute it via special form execution, continue
        # if head is ignoredValue, restart eval with tail
        # if head is s expression, replace head with Eval(head), restart loop
        # if head is lambda,
        #   apply Eval(second arg) to it,
        #   check if its fully bound,
        #       eval and replace if so,
        #   restart loop
        # if head is anything else, cant be applied, error

        head = expression.value[0]
        tail = expression.value[1:]

        if head.kind == Kind.Reference:
            [expression, currentScope] = Dereference(expression, currentScope)
            continue

        # if head.kind == Kind.IgnoredValue:
        #     expression = sExpression(tail)
        #     continue

        if head.kind == Kind.sExpression:
            expression = sExpression([Eval(head.value, currentScope.newChild())] + tail)
            continue

        if head.kind == Kind.Lambda:
            [expression, currentScope] = EvalLambda(expression, currentScope)
            continue

        # All other options are wrong
        currentFrame.throwError("Cant apply arguments to type at head")

