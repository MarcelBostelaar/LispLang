from classes import Kind, Scope, VarType, Lambda, List
from langConfig import SpecialForms
from Evaluator import MustBeKind, ThrowAnError, SpecialFormSlicer, Eval


#macro expand until the a statement is found
#   if its a let of macro statement,
#       if its static
#           evaluate it and add it to the macro expanding scope
#   if its not a macro statement
#       add to compiled file

# make sure build in forms get captured to ensure that the behaviour of macros and build in special forms are
# indistinguishable from a users perspective
# IE: let token1 token2 => let (token1) (token2)
# if this is not done, then user defined macros get executed in a pass before build in special forms, so
# lambda (a b c) somemacroname x y z => lambda (a b c) (somemacroname x y z) => lambda (a b c) macroresult more macro result
# rather than lambda first, then some macro, for consistency


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


def isStatic(expression, currentScope: Scope, *selfScopeNames):
    #TODO implement

    #

    return False


def deMacroTail(tail, currentScope):
    return [DemacroTop(x, currentScope.newChild())  # demacro every sublist in the s expression behind the head
            for x in tail
            if x.kind == Kind.List]

def handleNameInScope(expression, currentScope):
    head = expression.value[0]
    tail = expression.value[1:]

    if currentScope.isVarType(head.value, VarType.Macro):
        # its a macro, execute it
        lambdaVal: Lambda = currentScope.retrieveValue(head.value)
        result = lambdaVal.bind(tail).run(Eval)
        return DemacroTop(List(result + tail), currentScope)

    # not a macro, just a quoted var name, return it + macroexpand any lists after it
    for i in tail:
        if isMacro(i, currentScope):
            ThrowAnError(expression, "Found a macro keyword not in first position. Invalid")
    tail = deMacroTail(tail, currentScope)
    return List([head] + DemacroTop(List(tail), currentScope).value)


def handleMacro(currentScope, expression):
    [[macroword, varname, inputHolder, body], tail] = SpecialFormSlicer(expression, SpecialForms.macro)
    MustBeKind(varname, "First arg after a macro def must be a name", Kind.QuotedName)
    MustBeKind(inputHolder, "Second arg after a macro def is the input holder, must be a name", Kind.QuotedName)
    expandedBody = DemacroTop(body, currentScope.newChild())
    if not isStatic(expandedBody, currentScope):
        ThrowAnError("Macros must always be statis functions. "
                     "This macro definition uses a non static value or function", expression)
    lambdaForm = Lambda([inputHolder], expandedBody, currentScope)
    newScope = currentScope.addValue(varname.value, lambdaForm, VarType.Macro)
    return List(
        [macroword, varname, inputHolder, expandedBody] +  # demacroed version of the macro
        DemacroTop(List(tail), newScope)  # the tail, demacroed, with the new macro added
    )


def handleLet(currentScope, expression):
    [[letword, varname, body], tail] = SpecialFormSlicer(expression, SpecialForms.let)
    MustBeKind(varname, "The first arg after a let must be a name", Kind.QuotedName)
    expandedBody = DemacroTop(body, currentScope.newChild())
    if isStatic(expandedBody, currentScope):
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
    if expression.kind != Kind.List and expression.kind != Kind.QuotedName:
        #its a literal. Quoted name might be a macro that takes no args which needs to be expanded
        return expression

    head = expression.value[0]
    tail = expression.value[1:]

    if head.kind == Kind.QuotedName:
        if currentScope.hasValue(head.value):
            handleNameInScope(expression, currentScope)
        #possibily a special form, we only care about the macro, let and quote form
        if head.value == SpecialForms.let.value.keyword:
            return handleLet(currentScope, expression)
        if head.value == SpecialForms.macro.value.keyword:
            return handleMacro(currentScope, expression)
        if head.value == SpecialForms.quote.value.keyword:
            #quoted code should NOT be demacroed (so the item following a QUOTE special form)
            return List(expression.value[:1] + DemacroTop(expression.value[1:], currentScope).value)
    #all others, initial is not any sort of macro or special form we need to deal with
    return List([head] + deMacroTail(tail, currentScope))