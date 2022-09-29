from Evaluator.Classes import Kind, Scope, VarType, Lambda, List, UserLambda
from Config.langConfig import SpecialForms
from Evaluator.EvaluatorCode import MustBeKind, ThrowAnError, SpecialFormSlicer, Eval, toAST


def isMacro(expression, currentScope):
    """
    Returns whether the given expression is a macro keyword
    :param expression:
    :param currentScope:
    :return:
    """
    if expression.kind == Kind.QuotedName:
        if currentScope.hasValue(expression.value):
            if currentScope.isVarType(expression.value, VarType.Macro):
                return True
    return False


def demacroSubelementSingle(expression, currentScope):
    if expression.kind == Kind.List:
        return DemacroTop(expression, currentScope)
    if isMacro(expression, currentScope):
        ThrowAnError("Element in this position may not be a macro", expression)
    return expression


def demacroSubelements(listOfExpressions: [], currentScope):
    """
    Applies the demacro process to all the subelements in the expression, with a new scope
    Top level may not be a macro
    :param listOfExpressions:
    :param currentScope:
    :return:
    """
    return [demacroSubelementSingle(x, currentScope) for x in listOfExpressions]


def handleMacroInvocation(expression, currentScope):
    head = expression.value[0]
    tail = expression.value[1:]

    lambdaVal: Lambda = currentScope.retrieveValue(head.value)
    result = lambdaVal\
        .bind(currentScope)\
        .bind(List(tail))\
        .run(Eval)
    if not result.isSerializable():
        ThrowAnError("Macro returned something non-serializable (not LLQ)", expression)
    return DemacroTop(result, currentScope)


def handleMacro(currentScope, expression):
    [[macroword, varname, callingScope, inputHolder, body], tail] = SpecialFormSlicer(expression, SpecialForms.macro)
    MustBeKind(varname, "First arg after a macro def must be a name", Kind.QuotedName)
    MustBeKind(inputHolder, "Second arg after a macro def is the input holder, must be a name", Kind.QuotedName)
    MustBeKind(callingScope, "Third arg after a macro def is the calling scope holder, must be a name", Kind.QuotedName)
    MustBeKind(body, "Macro body must be a list", Kind.List)
    expandedBody = DemacroTop(body, currentScope)
    lambdaForm = UserLambda([callingScope.value, inputHolder.value], toAST(expandedBody), currentScope)
    newScope = currentScope.addValue(varname.value, lambdaForm, VarType.Macro)
    return List([macroword, varname, callingScope, inputHolder, expandedBody])\
        .concat(DemacroTop(List(tail), newScope))  # the tail, demacroed, with the new macro added



def handleLet(currentScope, expression):
    [[letword, varname, body], tail] = SpecialFormSlicer(expression, SpecialForms.let)
    MustBeKind(varname, "The first arg after a let must be a name", Kind.QuotedName)
    expandedBody = DemacroTop(body, currentScope)
    # if isStatic(expandedBody, currentScope): # left out for the interpreter
    evaluated = Eval(expandedBody, currentScope)
    currentScope = currentScope.addValue(varname.value, evaluated, VarType.Regular)
    return List([letword, varname, expandedBody]).concat(  # demacroed version of the let
        DemacroTop(List(tail), currentScope))  # the tail, demacroed, with if applicable


def DemacroTop(expression, currentScope: Scope):
    """
    Demacroes a given piece of code
    :param expression: LLQ of code
    :param currentScope: Compile time scope
    :return: LLQ of demacroed code
    """
    if expression.kind != Kind.List:
        return handleNotAList(expression, currentScope)

    if len(expression.value) == 0:
        return expression

    head = expression.value[0]

    if head.kind == Kind.QuotedName:
        return handleQuotedName(expression, currentScope)
    #all others, initial is not any sort of macro or special form we need to deal with
    return List(demacroSubelements(expression.value, currentScope))


def handleQuotedName(expression, currentScope):
    """
    :param currentScope:
    :param expression:
    :param head:
    :param tail:
    :return:
    """

    head = expression.value[0]

    #handle macro expands
    if currentScope.hasValue(head.value):
        if currentScope.isVarType(head.value, VarType.Macro):
            return handleMacroInvocation(expression, currentScope)
        else: #case function/value
            return List(demacroSubelements(expression.value, currentScope))

    # possibily a special form, we only care about the macro, let and quote form
    if head.value == SpecialForms.let.value.keyword:
        return handleLet(currentScope, expression)

    if head.value == SpecialForms.macro.value.keyword:
        return handleMacro(currentScope, expression)

    if head.value == SpecialForms.quote.value.keyword:
        # quoted code should NOT be demacroed (so the item following a QUOTE special form)
        return List(expression.value[:2] + demacroSubelements(expression.value[2:], currentScope))

    return List(demacroSubelements(expression.value, currentScope))


def handleNotAList(expression, currentScope):
    if expression.kind == Kind.QuotedName:
        if isMacro(expression, currentScope):
            ThrowAnError("Found a macro without any code behind it, invalid macro usage", expression)
    # its a literal.
    return expression

# normally speaking, you should check this, however, the interpreter will just throw an error at runtime
# if you use non static functions
# def isStatic(expression, currentScope: Scope, *selfScopeNames):
#     not implemented
#
#     #
#
#     return False