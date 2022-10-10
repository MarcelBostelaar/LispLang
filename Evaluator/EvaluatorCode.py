from Evaluator.Classes import sExpression, Kind, StackFrame, Value, \
    StackReturnValue, Lambda, List
from Evaluator.SpecialFormHandlers import ExecuteSpecialForm
from Evaluator.SupportFunctions import dereference, isSpecialFormKeyword

"""Only operates on demacroed code"""


def EvalLambda(currentFrame: StackFrame) -> StackFrame:
    if not currentFrame.isFullyEvaluated(1):
        return currentFrame.SubEvaluate(1)
    head: Lambda = currentFrame.executionState.value[0]
    tail = currentFrame.executionState.value[1:]
    tailHead = tail[0]
    trueTail = tail[1:]

    applied = head.bind(tailHead, currentFrame)

    if applied.canRun():
        old = currentFrame.withExecutionState(
            sExpression([StackReturnValue()] + trueTail)
        )
        new = applied.createFrame(old)
        return new
    else:
        return currentFrame.withExecutionState(
            sExpression([applied] + trueTail)
        )


def EvalUnfinishedHandlerInvocation(currentFrame):
    if not currentFrame.isFullyEvaluated(1):
        return currentFrame.SubEvaluate(1)
    head = currentFrame.executionState.value[0]
    tail = currentFrame.executionState.value[1:]
    tailHead = tail[0]
    trueTail = tail[1:]

    applied = head.bind(tailHead, currentFrame)

    if not applied.canRun(currentFrame):
        return currentFrame.withExecutionState(
            sExpression([applied] + trueTail)
        )

    #get


def handleReferenceAtHead(currentFrame: StackFrame) -> StackFrame:
    head = currentFrame.executionState.value[0]
    tail = currentFrame.executionState.value[1:]

    if currentFrame.hasScopedRegularValue(head.value):
        head = currentFrame.retrieveScopedRegularValue(head.value)
        expression = sExpression([head] + tail)
        return currentFrame.withExecutionState(expression)
    if currentFrame.hasScopedMacroValue(head.value):
        currentFrame.throwError("Macro that isnt compiled out found")
    if isSpecialFormKeyword(head.value):
        return ExecuteSpecialForm(currentFrame)

    currentFrame.throwError("Could not find reference " + head.value + ".")


def EvalHandleTopLevelValue(currentFrame: StackFrame) -> (bool, any):
    if currentFrame.executionState.kind == Kind.Reference:
        resultValue = dereference(currentFrame)
    elif currentFrame.executionState.kind == Kind.StackReturnValue:
        resultValue = currentFrame.getChildReturnValue()
    else:
        resultValue = currentFrame.executionState

    if currentFrame.parent is None:
        return True, resultValue
    handlerState = currentFrame.getHandlerState()
    if handlerState is not None:
        return False, currentFrame.parent.withChildReturnValue(List([resultValue, handlerState]))
    return False, currentFrame.parent.withChildReturnValue(resultValue)


# TODO Add tailcall optimization
def Eval(currentFrame: StackFrame) -> Value:
    """
    Evaluates a piece of interpreter representational code
    """
    # continue statements used to achieve tail call optimisation, and to keep stack usage to a minimum
    while True:
        if currentFrame.executionState.kind != Kind.sExpression:
            programFinished, returnValue = EvalHandleTopLevelValue(currentFrame)
            if programFinished:
                return returnValue
            currentFrame = returnValue
            continue

        if len(currentFrame.executionState.value) == 0:
            currentFrame.throwError("Cant evaluate an s expression with 0 items in it")
        if len(currentFrame.executionState.value) == 1:
            # nested single item, pop s expression
            currentFrame = currentFrame.withExecutionState(currentFrame.executionState.value[0])
            continue

        head = currentFrame.executionState.value[0]
        tail = currentFrame.executionState.value[1:]

        if head.kind == Kind.Reference:
            currentFrame = handleReferenceAtHead(currentFrame)
            continue

        if head.kind == Kind.sExpression:
            old = currentFrame.withExecutionState(
                sExpression([StackReturnValue()] + tail)
            )
            currentFrame = old.child(head)
            continue

        if head.kind == Kind.Lambda:
            currentFrame = EvalLambda(currentFrame)
            continue

        if head.kind == Kind.UnfinishedHandlerInvocation:
            currentFrame = EvalUnfinishedHandlerInvocation(currentFrame)
            continue

        # All other options are wrong
        currentFrame.throwError("Cant apply arguments to type at head/unhandled head kind")
