

#macro expand until the a statement is found
#   if its a let of macro statement,
#       if its static
#           evaluate it and add it to the macro expanding scope
#   if its not a macro statement
#       add to compiled file


def MacroExpand

def isLLQ(someValue):

    return True

def MacroExpandTop(somecode, macroScope: Scope) -> [[], bool]:
    """
    Expand the first macro found in the top level of the LLQ list
    :param macroScope: The scope containing all macro definitions
    :param somecode: LLQ code to expand
    :return: [LLQ list, bool indicating successful expand]
    """
    head = somecode[0]
    if head.kind == Kind.QuotedName:
        if macroScope.hasValue(head.value):
            macrofunc : Lambda = macroScope.retrieveValue(head.value)
            boundMacro = macrofunc.bind(somecode[1:])
            if not boundMacro.bindIsFinished():
                ThrowAnError("Macro function should only ever take one argument (all the following code), "
                             "probably an engine error")
            transformedListRepresentation = boundMacro.run(None)
            if not isLLQ(transformedListRepresentation):
                ThrowAnError("Macro " + head.value + " returned a value that isn't an LLQ", transformedListRepresentation)
            if transformedListRepresentation.kind != Kind.List:
                ThrowAnError("Macro " + head.value + " didn't return a list", transformedListRepresentation)
            return transformedListRepresentation.value

    pass


def MacroExpandTopAll(somecode, scope):
    """
    Expands all macros on the top level of the LLQ list until a statement is found
    :param somecode: LLQ code to expand
    :param scope: The scope with the existing values and
    :return: Fully top expanded code
    """
    while not IsStatement(somecode, scope):
        [newCode, succesfullExpand] = MacroExpandTop(somecode, scope)
        if not succesfullExpand:
            ThrowAnError("No macro expansion could be done, and code is not valid code. "
                         "Missing macro definition or missing value definition.", newCode)
        somecode = newCode
    return somecode