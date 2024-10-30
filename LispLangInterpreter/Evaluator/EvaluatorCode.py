from LispLangInterpreter.Config import Singletons
from ..DataStructures.Classes import dereference, sExpression, StackFrame, Value, \
    StackReturnValue, Lambda, HandleBranchPoint, ContinueStop, subevaluateMacro
from ..DataStructures.Kind import Kind
from ..DataStructures.HandlerStateRegistry import HandlerStateSingleton
from .SpecialFormHandlers import ExecuteSpecialForm
from ..DataStructures.SupportFunctions import isIndirectionValue, isSpecialFormKeyword

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
        return subevaluateMacro(currentFrame, 0)
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
    if isIndirectionValue(currentFrame.executionState):
        #retrieve value and substitute it
        resultValue = dereference(currentFrame)
        return False, currentFrame.withExecutionState(sExpression(resultValue))
    
    if currentFrame.parent is None:
        return True, currentFrame.executionState
    return False, currentFrame.parent.withChildReturnValue(currentFrame.executionState)


def non_looping_eval(currentFrame: StackFrame) -> Value:
    """
    Evaluates one step of a piece of interpreter representational code
    """
    Singletons.debugCounter += 1
    if Singletons.debug:
        print(str(Singletons.debugCounter) + "----\n")
        currentFrame.__stackTrace__()
    if currentFrame.executionState.kind != Kind.sExpression:
        program_finished, returnValue = EvalHandleTopLevelValue(currentFrame)
        return program_finished, returnValue

    if len(currentFrame.executionState.value) == 0:
        return False, currentFrame.throwError("Cant evaluate an s expression with 0 items in it")
    if len(currentFrame.executionState.value) == 1:
        # nested single item, pop s expression
        return False, currentFrame.withExecutionState(currentFrame.executionState.value[0])

    head = currentFrame.executionState.value[0]
    tail = currentFrame.executionState.value[1:]

    if head.kind == Kind.Reference:
        return False, handleReferenceAtHead(currentFrame)

    if head.kind == Kind.sExpression:
        old = currentFrame.withExecutionState(
            sExpression([StackReturnValue()] + tail)
        )
        return False, old.createChild(head)

    if head.kind == Kind.Lambda:
        return False, EvalLambda(currentFrame)

    # All other options are wrong
    currentFrame.throwError("Cant apply arguments to type at head/unhandled head kind")


# TODO Add tailcall optimization
def Eval(currentFrame: StackFrame) -> Value:
    """
    Evaluates a piece of interpreter representational code
    """
    # continue statements used to achieve tail call optimisation, and to keep stack usage to a minimum
    Singletons.debugCounter = 0
    program_finished = False
    while not program_finished:
        program_finished, currentFrame = non_looping_eval(currentFrame)
    return currentFrame
