import Config.langConfig
from Evaluator.Classes import Kind, Lambda, List, UserLambda, StackFrame, sExpression, Value, Reference
from Config.langConfig import SpecialForms
from Evaluator.EvaluatorCode import Eval
from Evaluator.SupportFunctions import toAST, MustBeKind, SpecialFormSlicer


def demacroSubelementSingle(currentFrame: StackFrame) -> Value:
    if currentFrame.executionState.kind == Kind.List:
        return DemacroTop(currentFrame)
    if currentFrame.hasScopedMacroValue(currentFrame.executionState.value):
        currentFrame.throwError("Element in this position may not be a macro")
    return currentFrame.executionState


def demacroSubelements(currentFrame: StackFrame) -> [Value]:
    """
    Applies the demacro process to all the subelements in the expression, with a new scope
    Top level may not be a macro
    """
    return [demacroSubelementSingle(currentFrame.createChild(x)) for x in currentFrame.executionState.value]


def handleMacroInvocation(currentFrame: StackFrame) -> Value:
    head = currentFrame.executionState.value[0]
    tail = currentFrame.executionState.value[1:]
    lambdaVal: Lambda = currentFrame.retrieveScopedMacroValue(head.value)
    newFrame = StackFrame(sExpression([lambdaVal, Reference(Config.langConfig.currentScopeKeyword), List(tail)]))
    newFrame.currentScope = currentFrame.currentScope
    result = Eval(newFrame)
    if not result.isSerializable():
        currentFrame.throwError("Macro returned something non-serializable (not LLQ)")
    return DemacroTop(currentFrame.withExecutionState(result))


def handleMacro(currentFrame: StackFrame) -> Value:
    [[macroword, varname, callingScope, inputHolder, body], tail] = SpecialFormSlicer(currentFrame, SpecialForms.macro)
    MustBeKind(currentFrame, varname, "First arg after a macro def must be a name", Kind.QuotedName)
    MustBeKind(currentFrame, inputHolder, "Second arg after a macro def is the input holder, must be a name", Kind.QuotedName)
    MustBeKind(currentFrame, callingScope, "Third arg after a macro def is the calling scope holder, must be a name", Kind.QuotedName)
    MustBeKind(currentFrame, body, "Macro body must be a list", Kind.List)
    expandedBody = DemacroTop(currentFrame.createChild(body))
    lambdaForm = UserLambda([callingScope.value, inputHolder.value], toAST(expandedBody), currentFrame.currentScope)
    newFrame = currentFrame.addScopedMacroValue(varname.value, lambdaForm)
    return List([macroword, varname, callingScope, inputHolder, expandedBody])\
        .concat(DemacroTop(newFrame.withExecutionState(List(tail))))


def handleLet(currentFrame: StackFrame) -> Value:
    [[letword, varname, body], tail] = SpecialFormSlicer(currentFrame, SpecialForms.let)
    MustBeKind(currentFrame, varname, "The first arg after a let must be a name", Kind.QuotedName)
    expandedBody = DemacroTop(currentFrame.createChild(body))
    createdValue = Eval(currentFrame.createChild(toAST(expandedBody)))
    newFrame = currentFrame.addScopedRegularValue(varname.value, createdValue)
    return List([letword, varname, expandedBody])\
        .concat(DemacroTop(newFrame.withExecutionState(List(tail))))


def handleQuotedNameAtHead(currentFrame: StackFrame) -> Value:
    head = currentFrame.executionState.value[0]

    #handle macro expands
    if currentFrame.hasScopedRegularValue(head.value):
        #case function/value
        return List(demacroSubelements(currentFrame))
    elif currentFrame.hasScopedMacroValue(head.value):
        return handleMacroInvocation(currentFrame)

    # possibily a special form, we only care about the macro, let and quote form
    if head.value == SpecialForms.let.value.keyword:
        return handleLet(currentFrame)

    if head.value == SpecialForms.macro.value.keyword:
        return handleMacro(currentFrame)

    if head.value == SpecialForms.quote.value.keyword:
        # quoted code should NOT be demacroed (so the item following a QUOTE special form)
        [quotewordAndItem, tail] = SpecialFormSlicer(currentFrame, SpecialForms.quote)
        return List(quotewordAndItem + demacroSubelements(currentFrame.withExecutionState(List(tail))))

    return List(demacroSubelements(currentFrame))


def handleList(currentFrame: StackFrame) -> Value:

    if len(currentFrame.executionState.value) == 0:
        return currentFrame.executionState

    head = currentFrame.executionState.value[0]

    if head.kind == Kind.QuotedName:
        return handleQuotedNameAtHead(currentFrame)
    #all others, initial is not any sort of macro or special form we need to deal with
    return List(demacroSubelements(currentFrame))


def handleNotAList(currentFrame: StackFrame) -> Value:
    if currentFrame.executionState.kind == Kind.QuotedName:
        if currentFrame.hasScopedMacroValue(currentFrame.executionState[0].value):
            currentFrame.throwError("Found a macro without any code behind it, invalid macro usage")
    # its a literal.
    return currentFrame.executionState


def DemacroTop(currentFrame: StackFrame) -> Value:
    """
    Demacroes a given piece of code
    :return: LLQ of demacroed code
    """
    if currentFrame.executionState.kind != Kind.List:
        return handleNotAList(currentFrame)
    return handleList(currentFrame)
