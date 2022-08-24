from classes import Scope, Lambda, Name, sExpression, NameConst, Value, QuoteConst, ListConst

macros = {}


def stringify(sExpression):
    return "Error stringification not implemented"


def ThrowAnError(message, currentExpression=None):
    if currentExpression is None:
        raise Exception(message)
    raise Exception(message + "\nLine: " + stringify(currentExpression))


def defineMacro(name, input, transformation):
    if name in macros.keys():
        raise Exception("Cant redefine macros")
    macros[name] = [input, transformation]

def EvalLambda(lambdaValue):
    return Eval(lambdaValue.body, lambdaValue.boundScope)

def Eval(expression, scope):
    # continue statements used to achieve tail call optimisation, and to keep stack usage to a minimum

    # if 0 children, error, cant execute
    # if 1 child, extract child, restart loop

    # two or more
    # if first arg is reserved word, expand statement, restart loop
    ## if first arg is ignore, remove it, restart loop
    # if first arg is a name, retrieve value from scope, restart loop
    # if first arg is an s expression, evaluate it recursively with new scope
    # if first arg is a lambda,
        #lambda code

    while True:
        if len(expression.children) == 0:
            ThrowAnError("Tried to evaluate an empty list")
        if len(expression.children) == 1:
            if expression.children[0].issExpression:
                expression = expression[0]
                continue  # tail call
            return expression.children[0]

        if isSpecialFormKeyword(expression, scope):
            #expand special form, returns new expression and changed scope
            [expression, scope] = ExpandSpecialForm(expression, scope)
            continue

        first = expression.children[0]
        tail = expression.children[1:]

        if first.type == NameConst:
            # extract value from scope
            expression = sExpression([scope.retrieveValue(first.name)] + tail)
            continue

        if first.issExpression:
            #evaluate first arg in place
            first = Eval(first, scope.newChild())
            expression = sExpression([first] + tail)
            continue

        if first.type == Lambda:
            second = tail[0]
            # if second arg is special, expand tail, restart loop
            if isSpecialFormKeyword(second, scope):
                [tail, scope] = ExpandSpecialForm(tail, scope)
                expression = sExpression([first] + tail)
                continue
            else:
                # eval second arg on its own
                tailtail = tail[1:]
                second = Eval(second, scope.newChild())
                # apply second arg
                first = first.bind(second)

                # if lambda finished binding, eval it with its bound scope
                    # put result in place of lambda
                if first.bindIsFinished():
                    if len(tailtail) == 0:
                        #no more arguments after this, tail call optimize
                        expression = sExpression(first.body)
                        scope = first.boundScope
                        continue #tail call optimization
                    else:
                        #still some more code in this scope, evaluate recursively with bound lambda scope
                        first = EvalLambda(first)
                        expression = sExpression([first] + tailtail)
                        continue
                #lambda isn't finished binding, do not execute yet
                expression = sExpression([first] + tailtail)
                continue

        else:
            ThrowAnError("Cannot apply arguments to this type", expression)

def findMacroPattern(expression, scope) -> Lambda:
    ThrowAnError("Not implemented")

def isSpecialFormKeyword(expression, scope) -> bool:
    #if macro pattern in scope, true
    #if reserved word, true
    ThrowAnError("Not implemented")

def ASTtoData(expression):
    if expression.issExpression:
        #s expression becomes itself in list presentation
        return Value([ASTtoData(x) for x in expression.children], ListConst)
    if expression.kind == NameConst:
        #quote names
        return Value(expression.__value__, QuoteConst)
    return expression  # anything else is passed along as is (shouldnt really be anything?)
    # note for compiler: in a compiler you would keep everything in list&quote&literal form,
    # then when encountering a macro, compile the macro and pass the code to it, returning a new list-quote-literal form
    # which you would then put in place. This avoids having to deal with complex function types and captured scope,
    # in the interpreter this shouldn't ever be an issue since you pass compiled constructs like lambdas to this code
    # macros may return captured functions from inside the macro, but

def DatatoAST(expression):
    if expression.kind == ListConst:
        #list to s expression
        return sExpression([DatatoAST(x) for x in expression.__value__])
    if expression.kind == QuoteConst:
        #unquote name
        return Value(expression.__value__, NameConst)
    return expression  # anything else is passed along as is

def MacroExpand(foundMacro, expressionList):
    #macros return a quoted list
    #the macro itself should be replaced with the *contents* of the list, so without any brackets

    #bind all the lambda args with the code, quoted
    for i in range(foundMacro.bindingsLeft()):
        foundMacro = foundMacro.bind(ASTtoData(expressionList[0]))
        expressionList = expressionList[1:]

    #execute it, macro returns a list of symbols, some quoted, some values
    executedMacro = EvalLambda(foundMacro)
    #unquote once
    executedMacro = DatatoAST(executedMacro)
    #insert back into place of the macro
    return executedMacro + expressionList


def ExceptionIfNoExecutableCode(expressionList, itemBefore, original):
    if len(expressionList) == 0:
        ThrowAnError("Defined a " + itemBefore + " and no executable code after, illegal code", original)

def ExpandSpecialForm(expressionList, scope: Scope) -> [sExpression, Scope]:
    foundMacro = findMacroPattern(expressionList, scope)
    if foundMacro is not None:
        return [sExpression(MacroExpand(foundMacro, expressionList)), scope]

    if (expressionList[0] == "macro"):
        [_, macroname, input, transformation] = expressionList[:4]
        scope = scope.addMacro(macroname, Lambda(input, transformation, scope.OnlyMacrosCopy()))
        ExceptionIfNoExecutableCode(expressionList[4:], "macro", expressionList)
        return [expressionList[4:], scope]

    elif (expressionList[0] == "lambda"):
        [_, arguments, body] = expressionList[:3]
        return [[Lambda(arguments, body, scope)] + expressionList[3:], scope]

    elif (expressionList[0] == "let"):
        [_, varname, value] = expressionList[:3]
        value = Eval(value, scope)
        scope = scope.addValue(varname, value)
        ExceptionIfNoExecutableCode(expressionList[3:], "let", expressionList)
        return [expressionList[3:], scope]

    else:
        raise Exception("Unknown function")
