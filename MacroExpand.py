from classes import Kind, Scope, VarType, Lambda, List
from langConfig import SpecialForms
from Evaluator import MustBeKind, ThrowAnError, SpecialFormSlicer, Eval


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


def demacroSubelements(listOfExpressions: [], currentScope):
    """
    Applies the demacro process to all the subelements in the expression, with a new scope
    :param listOfExpressions:
    :param currentScope:
    :return:
    """
    return [DemacroTop(x, currentScope.newChild())  # demacro every sublist in the s expression behind the head
            for x in listOfExpressions
            if x.kind == Kind.List]


def handleNameInScope(expression, currentScope):
    head = expression.value[0]
    tail = expression.value[1:]

    if currentScope.isVarType(head.value, VarType.Macro):
        # its a macro, execute it
        lambdaVal: Lambda = currentScope.retrieveValue(head.value)
        result = lambdaVal\
            .bind(tail)\
            .bind(currentScope)\
            .run(Eval)
        return DemacroTop(List(result + tail), currentScope)

    # not a macro, just a quoted var name, return it + macroexpand any lists after it
    for i in tail:
        if isMacro(i, currentScope):
            ThrowAnError(expression, "Found a macro keyword not in first position. Invalid")
    tail = demacroSubelements(tail, currentScope)
    return List([head] + DemacroTop(List(tail), currentScope).value)


def handleMacro(currentScope, expression):
    [[macroword, varname, inputHolder, callingScope, body], tail] = SpecialFormSlicer(expression, SpecialForms.macro)
    MustBeKind(varname, "First arg after a macro def must be a name", Kind.QuotedName)
    MustBeKind(inputHolder, "Second arg after a macro def is the input holder, must be a name", Kind.QuotedName)
    expandedBody = DemacroTop(body, currentScope.newChild())
    # if not isStatic(expandedBody, currentScope): #left out for interpreter
    #     ThrowAnError("Macros must always be statis functions. "
    #                  "This macro definition uses a non static value or function", expression)
    lambdaForm = Lambda([inputHolder, callingScope], expandedBody, currentScope)
    newScope = currentScope.addValue(varname.value, lambdaForm, VarType.Macro)
    return List(
        [macroword, varname, inputHolder, expandedBody] +  # demacroed version of the macro
        DemacroTop(List(tail), newScope)  # the tail, demacroed, with the new macro added
    )


def handleLet(currentScope, expression):
    [[letword, varname, body], tail] = SpecialFormSlicer(expression, SpecialForms.let)
    MustBeKind(varname, "The first arg after a let must be a name", Kind.QuotedName)
    expandedBody = DemacroTop(body, currentScope.newChild())
    # if isStatic(expandedBody, currentScope): # left out for the interpreter
    evaluated = Eval(expandedBody, currentScope)
    currentScope = currentScope.addValue(varname.value, evaluated, VarType.Regular)
    return List(
        [letword, varname, expandedBody] +  # demacroed version of the let
        DemacroTop(List(tail), currentScope)  # the tail, demacroed, with if applicable
    )  # the static value added to the compile scope


def DemacroTop(expression, currentScope: Scope):
    """
    Demacroes a given piece of code
    :param expression: LLQ of code
    :param currentScope: Compile time scope
    :return: LLQ of demacroed code
    """
    if expression.kind != Kind.List:
        return handleNotAList(expression, currentScope)

    head = expression.value[0]

    if head.kind == Kind.QuotedName:
        return handleQuotedName(expression, currentScope)
    #all others, initial is not any sort of macro or special form we need to deal with
    return demacroSubelements(expression.value, currentScope)


def handleQuotedName(expression, currentScope):
    """
    :param currentScope:
    :param expression:
    :param head:
    :param tail:
    :return:
    """

    head = expression.value[0]

    if currentScope.hasValue(head.value):
        return handleNameInScope(expression, currentScope)

    # possibily a special form, we only care about the macro, let and quote form
    if head.value == SpecialForms.let.value.keyword:
        return handleLet(currentScope, expression)

    if head.value == SpecialForms.macro.value.keyword:
        return handleMacro(currentScope, expression)

    if head.value == SpecialForms.quote.value.keyword:
        # quoted code should NOT be demacroed (so the item following a QUOTE special form)
        return List(expression.value[:2] + demacroSubelements(expression.value[2:], currentScope))

    return demacroSubelements(expression.value, currentScope)


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