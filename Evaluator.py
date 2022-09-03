from classes import Scope, Lambda, sExpression, Value, Kind, Reference, IgnoredValue

"""Only operates on demacroed code"""


def stringify(sExpression):
    return "Error stringification not implemented"


def ThrowAnError(message, currentExpression=None):
    if currentExpression is None:
        raise Exception(message)
    raise Exception(message + "\nLine: " + stringify(currentExpression))


def toAST(LLQ):
    """
    Takes an LLQ and turns it into the interpreter representation of executable AST
    :param LLQ: List, Literal, Quoted names AST
    :return: The AST as s-expressions and unquoted names
    """
    if LLQ.kind == Kind.List:
        return sExpression([toAST(x) for x in LLQ.value])
    if LLQ.kind == Kind.QuotedName:
        return Reference(LLQ.value)
    return LLQ


def EvalLambda(expression, currentScope):
    head = expression.value[0]
    tail = expression.value[1:]
    #   apply Eval(second arg) to it,
    #   check if its fully bound,
    #       eval and replace if so,
    #   restart loop
    tailhead = tail[0]
    truetail = tail[1:]
    evaluated = Eval(tailhead, currentScope.newChild())
    applied = head \
        .bind(evaluated) \
        .run(Eval)
    expression = sExpression([applied] + truetail)
    return [expression, currentScope]


def Dereference(expression, currentScope):
    head = expression.value[0]
    tail = expression.value[1:]

    if currentScope.hasValue(head.value):
        head = currentScope.retrieveValue(head.value)
        expression = sExpression([head] + tail)
        return [expression, currentScope]
    if isSpecialFormKeyword(head.value):
        return ExecuteSpecialForm(expression, currentScope)

    ThrowAnError("Could not find reference " + head.value + ".", expression)

def Eval(expression, currentScope):
    """
    Evaluates a piece of interpreter representational code
    :param expression: s Expression and/or value
    :param currentScope: Currently scoped variables and their values
    :return: Return value of the calculation
    """
    # continue statements used to achieve tail call optimisation, and to keep stack usage to a minimum
    while True:
        if expression.kind != Kind.sExpression:
            if expression.kind == Kind.Reference:
                [expression, currentScope] = Dereference(sExpression([expression]), currentScope)
                continue
            return expression

        ##its an s expression
        # if 0 children, error, cant execute
        # if 1 child, extract child, restart loop
        if len(expression.value) == 0:
            ThrowAnError("Cant evaluate an s expression with 0 items in it")
        if len(expression.value) == 1:
            expression = expression.value[0]
            currentScope = currentScope.newChild()
            continue

        ## two or more
        # if head if reference (a name)
        # if head is reference in scope, replace with its value from scope
        # (dereferencing is done before special forms to allow scoped overrides of special forms.
        # This makes special forms undistinct from macro forms from a user perspective,
        # which can also be scoped overridden)
        # if head is reference of special form, execute it via special form execution, continue
        # if head is ignoredValue, restart eval with tail
        # if head is s expression, replace head with Eval(head), restart loop
        # if head is lambda,
        #   apply Eval(second arg) to it,
        #   check if its fully bound,
        #       eval and replace if so,
        #   restart loop
        # if head is anything else, cant be applied, error

        head = expression.value[0]
        tail = expression.value[1:]

        if head.kind == Kind.Reference:
            [expression, currentScope] = Dereference(expression, currentScope)
            continue

        if head.kind == Kind.IgnoredValue:
            expression = sExpression(tail)
            continue

        if head.kind == Kind.sExpression:
            expression = sExpression([Eval(head.value, currentScope.newChild())] + tail)
            continue

        if head.kind == Kind.Lambda:
            [expression, currentScope] = EvalLambda(expression, currentScope)
            continue

        # All other options are wrong
        ThrowAnError("Cannot apply an argument to value at head.", expression)


def isSpecialFormKeyword(name) -> bool:
    return name in ["lambda", "let"]


def MustHaveLength(expression, N):
    if len(expression.value) < N:
        ThrowAnError("Special form " + expression.value[0].value + " must have at least "
                     + str(N) + " items arguments, only has " + str(len(expression.value)))


def MustBeKind(expression, message: str, *kinds: [Kind]):
    """
    Error check for all allowed types of an expression
    :param expression:
    :param message:
    :param kinds:
    :return:
    """
    if expression.kind in kinds:
        return
    ThrowAnError(message + "\nIt has type " + expression.kind.name, expression)


def ExecuteSpecialForm(expression, currentScope):
    name = expression.value[0].value
    if name == "lambda":
        MustHaveLength(expression, 3)
        args = expression.value[1]
        body = expression.value[2]
        lambdaerr = "First arg after lambda must be a flat list/s expression of names"
        MustBeKind(args, lambdaerr, Kind.sExpression, )
        [MustBeKind(x, lambdaerr, Kind.Reference) for x in args.value]
        MustBeKind(body, "Body of a lambda must be an s expression or a single name", Kind.sExpression, Kind.Reference)

        tail = expression.value[3:]
        return [sExpression([Lambda([z.value for z in args.value], body, currentScope.newChild())] + tail), currentScope]

    if name == "let":
        MustHaveLength(expression, 3)
        name = expression.value[1]
        value = Eval(expression.value[2], currentScope)
        MustBeKind(name, "The first arg after a let must be a name", Kind.Reference)
        newScope = currentScope.addValue(name.value, value)
        tail = expression.value[3:]
        return [sExpression([IgnoredValue] + tail), newScope]

    ThrowAnError("Unknown special form (engine bug)", expression)
