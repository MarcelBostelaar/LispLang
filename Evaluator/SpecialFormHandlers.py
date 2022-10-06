from Config.langConfig import SpecialForms
from Evaluator.Classes import StackFrame, Kind, sExpression, StackReturnValue, UserLambda, List
from Evaluator.SupportFunctions import dereference, MustBeKind, SpecialFormSlicer, QuoteCode


def handleSpecialFormCond(currentFrame: StackFrame):
    # eval condition, if true, return true unevaluated, else return falsepath unevaluated
    [[condAtom, condition, truePath, falsePath], tail] = \
        SpecialFormSlicer(currentFrame, SpecialForms.cond)
    if condition.kind == Kind.sExpression:
        x = sExpression([condAtom, StackReturnValue(), truePath, falsePath] + tail)
        currentFrame = currentFrame.withExecutionState(x)
        newFrame = currentFrame.child(condition)
        return newFrame
    evaluated = dereference(currentFrame.withExecutionState(condition))
    MustBeKind(currentFrame, evaluated, "Tried to evaluate an conditional, value to evaluate not a boolean",
               Kind.Boolean)
    if evaluated.value:
        return currentFrame.withExecutionState(truePath)
    return currentFrame.withExecutionState(falsePath)


def handleSpecialFormLambda(currentFrame: StackFrame):
    [[_, args, body], rest] = SpecialFormSlicer(currentFrame, SpecialForms.Lambda)
    lambdaerr = "First arg after lambda must be a flat list/s expression of names"
    MustBeKind(currentFrame, args, lambdaerr, Kind.sExpression, )
    [MustBeKind(currentFrame, x, lambdaerr, Kind.Reference) for x in args.value]
    MustBeKind(currentFrame, body, "Body of a lambda must be an s expression or a single name",
               Kind.sExpression, Kind.Reference)
    return currentFrame.withExecutionState(
        sExpression([UserLambda([z.value for z in args.value], body, currentFrame)] + rest)
    )


def handleSpecialFormLet(currentFrame: StackFrame):
    [[let, name, value], tail] = SpecialFormSlicer(currentFrame, SpecialForms.let)
    MustBeKind(currentFrame, name, "The first arg after a let must be a name", Kind.Reference)
    if value.kind == Kind.sExpression:
        # Item needs to be further evaluated
        x = sExpression([let, name, StackReturnValue()] + tail.value)
        updatedParent = currentFrame.withExecutionState(x)  # replace item with return value placeholder
        newFrame = updatedParent.child(value)  # create child stack to calculate result
        return newFrame
    else:
        value = dereference(currentFrame.withExecutionState(value))  # retrieve the raw value
    return currentFrame.addScopedRegularValue(name.value, value).withExecutionState(tail)


def handleSpecialFormList(currentFrame: StackFrame):
    # treats the list behind it as a list rather than an s expression
    [[listAtom, snd], tail] = SpecialFormSlicer(currentFrame, SpecialForms.list)
    MustBeKind(currentFrame, snd, "Item after list must be a list", Kind.sExpression)
    listMapped, newStackExpression = handleSpecialFormListStep(currentFrame, snd)
    if newStackExpression is not None:
        currentFrame = currentFrame.withExecutionState(sExpression([listAtom, sExpression(listMapped)] + tail))
        newStack = currentFrame.child(newStackExpression)
        return newStack
    return currentFrame.withExecutionState(List(listMapped))


def handleSpecialFormListStep(currentFrame, snd):
    """
    Evaluate the items in snd into their fully evaluated form.
    :param currentFrame:
    :param snd:
    :return:
    """
    newStackExpression = None
    listMapped = []
    for i in snd.value:
        if i.kind == Kind.sExpression:
            if newStackExpression is not None:
                listMapped.append(StackReturnValue())
                newStackExpression = i
            else:
                listMapped.append(i)
        else:
            listMapped.append(dereference(currentFrame.withExecutionState(i)))
    return listMapped, newStackExpression


def ExecuteSpecialForm(currentFrame: StackFrame) -> StackFrame:
    name = currentFrame.executionState.value[0].value
    if name == SpecialForms.Lambda.value.keyword:
        return handleSpecialFormLambda(currentFrame)

    if name == SpecialForms.macro.value.keyword:
        # ignore for this implementation, interpreter doesn't support eval yet
        [_, rest] = SpecialFormSlicer(currentFrame, SpecialForms.macro)
        return currentFrame.withExecutionState(rest)

    if name == SpecialForms.let.value.keyword:
        return handleSpecialFormLet(currentFrame)

    if name == SpecialForms.quote.value.keyword:
        # quotes item directly after it
        [[_, snd], tail] = SpecialFormSlicer(currentFrame, SpecialForms.quote)
        newSnd = QuoteCode(currentFrame, snd)
        return currentFrame.executionState(sExpression([newSnd] + tail))

    if name == SpecialForms.list.value.keyword:
        return handleSpecialFormList(currentFrame)

    if name == SpecialForms.cond.value.keyword:
        return handleSpecialFormCond(currentFrame)

    currentFrame.throwError("Unknown special form (engine bug)")
