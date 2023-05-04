from ..DataStructures.Classes import sExpression, StackFrame, Value, \
    StackReturnValue, Lambda, HandleBranchPoint, ContinueStop
from ..DataStructures.Kind import Kind
from ..DataStructures.HandlerStateRegistry import HandlerStateSingleton
from .SpecialFormHandlers import ExecuteSpecialForm
from ..DataStructures.SupportFunctions import isIndirectionValue, dereference, isSpecialFormKeyword

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


def EvalHandleTopLevelValueHandleBranchPoint(currentFrame: StackFrame) -> (bool, any):
    """
    Evaluates a top level HandleBranchPoint.
    :param currentFrame:
    :return: Bool indicating whether the returned value is a new raw value, raw value if true/new frame if false
    """
    point: HandleBranchPoint = currentFrame.executionState
    if point.continueBranch is not None:
        returnedValue: ContinueStop = currentFrame.getChildReturnValue()
        if returnedValue.kind != Kind.ContinueStop:
            currentFrame.throwError("Returned a value that isn't a continue or stop!")
        #set the state to the new value
        HandlerStateSingleton.setState(point.handlerID, returnedValue.newState)
        if returnedValue.isContinue:
            #continue with the continuation value
            return False, point.continueBranch.createChild(returnedValue.returnValue)
        else:
            #stopped, return the given return value
            resultValue = returnedValue.returnValue
    else:
        #Return of the regular branch
        resultValue = currentFrame.getChildReturnValue()

    if currentFrame.parent is None:
        return True, resultValue
    return False, currentFrame.parent.withChildReturnValue(resultValue)


def EvalHandleTopLevelValue(currentFrame: StackFrame) -> (bool, any):
    """
    Evaluates a top level single value.
    :param currentFrame:
    :return: Bool indicating whether the returned value is a new raw value, raw value if true/new frame if false
    """
    if currentFrame.executionState.kind == Kind.HandleBranchPoint:
        return EvalHandleTopLevelValueHandleBranchPoint(currentFrame)
    elif isIndirectionValue(currentFrame.executionState):
        resultValue = dereference(currentFrame)
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
        # print("----\n")
        # currentFrame.__stackTrace__()
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
