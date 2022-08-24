Lamda = 1
NameConst = 2
QuoteConst = 3
ListConst = 4


class sExpression:
    def __init__(self, children):
        self.issExpression = True
        self.children = children

    def map(self, f):
        return sExpression([f(x) for x in self.children])


class Name:
    def __init__(self, name):
        self.issExpression = False
        self.kind = NameConst
        self.name = name

    def toString(self):
        return self.name


class Value:
    def __init__(self, value, kind):
        self.issExpression = False
        self.kind = kind
        self.value = value

    def toString(self):
        return '"' + self.value + '"'


class Lambda:
    def __init__(self, bindings, body, currentScope, bindIndex=0):
        self.issExpression = False
        self.kind = Lambda

        self.bindings = bindings
        self.body = body
        self.boundScope = Scope(currentScope)
        self.bindIndex = bindIndex

    def bindIsFinished(self):
        return self.boundScope.countValues() == self.bindIndex + 1

    def bind(self, variable):
        if self.bindIsFinished():
            raise Exception("Binding fully bound lambda (engine error?)")
        newscope = self.boundScope.addValue(self.bindings[self.bindIndex], variable)
        return Lambda(self.bindings, self.body, newscope, self.bindIndex + 1)

    def bindingsLeft(self):
        return len(self.bindings) - self.boundScope.countValues()

    def map(self, f):
        return Lambda(self.bindings, f(self.body), self.boundScope.Map(f), self.bindIndex)


class Scope:
    def __init__(self, parent, startValues=None, startMacros=None):
        if startValues is None:
            startValues = {}
        if startMacros is None:
            startMacros = {}
        self.__values__ = startValues
        self.__macros__ = startMacros
        self.__parent__ = parent

    def addValue(self, name, value):
        if name in self.__values__.keys():
            raise Exception("Overwriting variables in the same scope is not allowed")
        copy = self.__values__.copy()
        copy[name] = value
        return Scope(self.__parent__, startValues=copy, startMacros=self.__macros__)

    def addMacro(self, macroname, lambdaValue):
        if macroname in self.__values__.keys():
            raise Exception("Overwriting macros in the same scope is not allowed")
        copy = self.__macros__.copy()
        copy[macroname] = lambdaValue
        return Scope(self.__parent__, startValues=self.__values__, startMacros=copy)

    def retrieveValue(self, name):
        if name in self.__values__.keys():
            return self.__values__[name]
        if self.__parent__ is not None:
            return self.__parent__.retrieveValue(name)
        raise Exception("Unknown variable")

    def countValues(self):
        if self.__parent__ is not None:
            return len(self.__values__) + self.__parent__.countValues()
        return len(self.__values__)

    def newChild(self):
        return Scope(self)

    def OnlyMacrosCopy(self):
        parent = None
        if self.__parent__ is not None:
            parent = self.__parent__.OnlyMacrosCopy()
        return Scope(parent, startMacros=self.__macros__)

    def Map(self, f):
        newValues = {k: f(v) for k, v in self.__values__.items()}
        newMacros = {k: f(v) for k, v in self.__macros__.items()}
        parent = None
        if self.__parent__ is not None:
            parent = self.__parent__.Map(f)
        return Scope(parent, startValues=newValues, startMacros=newMacros)
