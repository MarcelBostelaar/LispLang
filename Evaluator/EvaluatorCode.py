from Evaluator.Classes import sExpression, Kind, StackFrame, Value, \
    StackReturnValue, Lambda
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
        new = applied.createEvaluationFrame(old)
        return new
    else:
        return currentFrame.withExecutionState(
            sExpression([applied] + trueTail)
        )


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
    if currentFrame.executionState.kind in [Kind.Reference, Kind.HandleInProgress, Kind.StackReturnValue]:
        resultValue = dereference(currentFrame)
    if currentFrame.executionState.kind == Kind.HandleBranchPoint:
        raise NotImplementedError("")
        #TODO if its continue path is none, treat as a stack return value, just pass along child value
        #TODO if it has a continue branch, check if its continue or stop, if continue, append contained value in new stack to continue,
        # else if its stop, return unit
    else:
        resultValue = currentFrame.executionState

    if currentFrame.parent is None:
        return True, resultValue
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
            currentFrame = old.createChild(head)
            continue

        if head.kind == Kind.Lambda:
            currentFrame = EvalLambda(currentFrame)
            continue

        # All other options are wrong
        currentFrame.throwError("Cant apply arguments to type at head/unhandled head kind")
