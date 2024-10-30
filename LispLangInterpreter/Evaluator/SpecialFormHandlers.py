from ..Config.langConfig import SpecialForms
from ..DataStructures.Classes import StackFrame, dereference, sExpression, StackReturnValue, UserLambda, List, HandleReturnValue, HandleBranchPoint, UserHandlerFrame
from ..DataStructures.Kind import Kind
from ..DataStructures.HandlerStateRegistry import HandlerStateSingleton
from ..DataStructures.SupportFunctions import isIndirectionValue
from .SupportFunctions import MustBeKind, SpecialFormSlicer, QuoteCode, MustBeString
from ..ImportHandlerSystem.CompileStatus import CompileStatus


def handleSpecialFormImport(currentFrame: StackFrame):
    [[_, what, saveAs], tail] = \
        SpecialFormSlicer(currentFrame, SpecialForms.import__)
    if not currentFrame.isFullyEvaluated(1):
        return currentFrame.SubEvaluate(1)
    if not currentFrame.isFullyEvaluated(2):
        return currentFrame.SubEvaluate(2)
    MustBeKind(currentFrame, saveAs, "Target name must be a reference", Kind.QuotedName)
    error = "Import target must be a list of strings"
    MustBeKind(currentFrame, what, error, Kind.List)
    for i in what.value:
        MustBeString(currentFrame, i, error)
    pathItems = ["".join([z.value for z in x.value]) for x in what.value]

    value = currentFrame.currentScope.currentFile.find(currentFrame, pathItems)
    if value is None:
        currentFrame.throwError("Could not find " + ".".join(pathItems))
    return currentFrame.withExecutionState(sExpression(tail)).addScopedRegularValue(saveAs.value, value)


def handleSpecialFormCond(currentFrame: StackFrame):
    # eval condition, if true, return true unevaluated, else return falsepath unevaluated
    [[condAtom, condition, truePath, falsePath], tail] = \
        SpecialFormSlicer(currentFrame, SpecialForms.cond)
    if not currentFrame.isFullyEvaluated(1):
        return currentFrame.SubEvaluate(1)
    MustBeKind(currentFrame, condition, "Tried to evaluate an conditional, value to evaluate not a boolean",
               Kind.Boolean)
    if condition.value:
        path = truePath
    else:
        path = falsePath
    return currentFrame.withExecutionState(sExpression([path] + tail))


def handleSpecialFormLambda(currentFrame: StackFrame):
    [[_, args, body], rest] = SpecialFormSlicer(currentFrame, SpecialForms.Lambda)
    lambdaerr = "First arg after lambda must be a flat list/s expression of names"
    MustBeKind(currentFrame, args, lambdaerr, Kind.sExpression)
    [MustBeKind(currentFrame, x, lambdaerr, Kind.Reference) for x in args.value]
    MustBeKind(currentFrame, body, "Body of a lambda must be an s expression or a single name",
               Kind.sExpression, Kind.Reference)
    return currentFrame.withExecutionState(
        sExpression([UserLambda([z.value for z in args.value], body, currentFrame.currentScope)] + rest)
    )


def handleSpecialFormLet(currentFrame: StackFrame):
    [[let, name, value], tail] = SpecialFormSlicer(currentFrame, SpecialForms.let)
    MustBeKind(currentFrame, name, "The first arg after a let must be a name", Kind.Reference)
    if not currentFrame.isFullyEvaluated(2):
        return currentFrame.SubEvaluate(2)
    return currentFrame\
        .addScopedRegularValue(name.value, value)\
        .withExecutionState(sExpression(tail))


def handleSpecialFormList(currentFrame):
    """
    Evaluate the items in snd into their fully evaluated form.
    :param currentFrame:
    :return:
    """
    [[listAtom, snd], tail] = SpecialFormSlicer(currentFrame, SpecialForms.list)
    MustBeKind(currentFrame, snd, "Item after list must be a list", Kind.sExpression)

    #Walk over the snd, save the first instance of a subexpression into new stack expression
    # and replace with a stack return value in the list, the following expressions as is
    newStackExpression = None
    listMapped = []
    for i in snd.value:
        if i.kind == Kind.sExpression:
            if newStackExpression is None:
                listMapped.append(StackReturnValue())
                newStackExpression = i
            else:
                listMapped.append(i)
        else:
            if isIndirectionValue(i):
                valueToAppend = dereference(currentFrame.withExecutionState(i)).value
            else:
                valueToAppend = [i]
            listMapped += valueToAppend

    # if a subexpression was found and replaced, make it into a new stackframe, with parent being the updates list
    if newStackExpression is not None:
        currentFrame = currentFrame.withExecutionState(sExpression([listAtom, sExpression(listMapped)] + tail))
        newStack = currentFrame.createChild(newStackExpression)
        return newStack
    #No subexpression found, all subitems are evaluated
    return currentFrame.withExecutionState(List(listMapped))


def verifyHandlerQuotekeyValuePairs(callingFrame: StackFrame, keyValue):
    errMessage = "Handlers must be key value pairs of a quoted name and a function"

    MustBeKind(callingFrame, keyValue, errMessage, Kind.List)
    for i in keyValue.value:
        MustBeKind(callingFrame, i, errMessage, Kind.List)
        if len(i.value) != 2:
            callingFrame.throwError(errMessage)
        MustBeKind(callingFrame, i.value[0], errMessage, Kind.QuotedName)
        MustBeKind(callingFrame, i.value[1], errMessage, Kind.Lambda)


def handleSpecialFormHandle(currentFrame: StackFrame) -> StackFrame:
    """

    :param currentFrame:
    :return: A new stack in the form of, from top to bottom:
    <Original frame with handle invocation replaced with a stack return value> <-
    <A frame containing only a handle branch point, which keeps track of a possible branch> <=
    <A frame containing to code to evaluate, and the new handler stack frame>
    """
    [[handlerWord, codeToEvaluate, handlerQuotekeyValuePairs, stateSeed], tail] = SpecialFormSlicer(currentFrame, SpecialForms.handle)

    if not currentFrame.isFullyEvaluated(2):#handlerQuotekeyValuePairs
        return currentFrame.SubEvaluate(2)
    if not currentFrame.isFullyEvaluated(3):#stateSeed
        return currentFrame.SubEvaluate(3)

    verifyHandlerQuotekeyValuePairs(currentFrame, handlerQuotekeyValuePairs)

    #register the handler ID
    handlerID = HandlerStateSingleton.registerHandlerFrame(stateSeed)

    #Create the special stack return value inprogressvalue
    inProgressValue = HandleReturnValue(handlerID)
    #current frame with handle invocation replaced with the stack return value
    newParentFrame = currentFrame\
        .withExecutionState(sExpression([inProgressValue] + tail))

    #Should NOT contain the handlers, and only the branch point. Handles a possible branch moment.
    branchFrame = newParentFrame.createChild(HandleBranchPoint(handlerID))

    newHandler = UserHandlerFrame(handlerID, branchFrame)
    newHandler.parent = currentFrame.closestHandlerFrame

    for i in handlerQuotekeyValuePairs.value:
        newHandler = newHandler.addHandler(currentFrame, i.value[0].value, i.value[1])

    #Subevaluation stack with new handler added.
    evaluationFrame = branchFrame\
        .createChild(codeToEvaluate)\
        .withHandlerFrame(newHandler)

    return evaluationFrame


def handleSpecialFormIgnore(currentFrame: StackFrame) -> StackFrame:
    [[ignoreWord, codeToPerform], tail] = SpecialFormSlicer(currentFrame, SpecialForms.ignore)
    if currentFrame.isFullyEvaluated(1):
        return currentFrame.withExecutionState(sExpression(tail))
    return currentFrame.SubEvaluate(1)


def ExecuteSpecialForm(currentFrame: StackFrame) -> StackFrame:
    name = currentFrame.executionState.value[0].value
    if name == SpecialForms.Lambda.value.keyword:
        return handleSpecialFormLambda(currentFrame)

    if name == SpecialForms.macro.value.keyword:
        #calling scope is the scope the macro is called from, which is needed to subevaluate elements in the macro
        #As of yet, the calling scope is unable to be used, but it is a good idea to keep it for future use, such as with a "subeval" function that takes a custom scope
        [[_, macroname, callingScope_alias, input_ast_alias, macroFuncBody], rest] = SpecialFormSlicer(currentFrame, SpecialForms.macro)
        #current scope is the scope the macro is defined in, only those values are available to the macro
        macroLambda = UserLambda([callingScope_alias.value, input_ast_alias.value], macroFuncBody, currentFrame.currentScope)
        return currentFrame.addScopedMacroValue(macroname.value, macroLambda).withExecutionState(sExpression(rest))

    if name == SpecialForms.let.value.keyword:
        return handleSpecialFormLet(currentFrame)

    if name == SpecialForms.quote.value.keyword:
        # quotes item directly after it
        [[_, snd], tail] = SpecialFormSlicer(currentFrame, SpecialForms.quote)
        newSnd = QuoteCode(currentFrame, snd)
        return currentFrame.withExecutionState(sExpression([newSnd] + tail))

    if name == SpecialForms.list.value.keyword:
        return handleSpecialFormList(currentFrame)

    if name == SpecialForms.cond.value.keyword:
        return handleSpecialFormCond(currentFrame)

    if name == SpecialForms.handle.value.keyword:
        return handleSpecialFormHandle(currentFrame)

    if name == SpecialForms.ignore.value.keyword:
        return handleSpecialFormIgnore(currentFrame)

    if name == SpecialForms.import__.value.keyword:
        return handleSpecialFormImport(currentFrame)

    currentFrame.throwError("Unknown special form (engine bug)")

