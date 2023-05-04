from __future__ import annotations

import importlib
import os
from os.path import basename
from typing import List

from LispLangInterpreter.Config.Singletons import MacroHandlerFrame, RuntimeHandlerFrame
from LispLangInterpreter.DataStructures.Classes import StackFrame
from LispLangInterpreter.Evaluator.EvaluatorCode import Eval
from LispLangInterpreter.Evaluator.MacroExpand import DemacroTop
from LispLangInterpreter.Evaluator.SupportFunctions import toAST
from LispLangInterpreter.ImportHandlerSystem.CompileStatus import CompileStatus
from LispLangInterpreter.Parser.ParserCode import parseAll
from LispLangInterpreter.Parser.ParserCombinator import SOF_value, EOF_value


class Searchable:
    def __init__(self, absPath, compileStatus: CompileStatus):
        self.absPath = absPath
        self.name = None if absPath is None else basename(absPath).split(".")[0]
        self.parent = None
        self.compileStatus: CompileStatus = compileStatus
        self.values = {}

    def getSearchable(self, pathElements: [str]) -> Searchable | None:
        """
        Gets the specified searchable where the specified value is located, or None if not found
        :param pathElements: List of elements
        :return: Searchable or None
        """
        raise NotImplementedError("Abstract")

    def getValue(self, name: str) -> Searchable | None:
        """
        Attempts to get a value from the given searchable
        :param name: Name of the item to import
        :return: Found value, or None if none was found.
        """
        raise NotImplementedError("Abstract")

    def execute(self, callingStack: StackFrame):
        raise NotImplementedError("Abstract")


class Leaf(Searchable):
    def __init__(self, absPath, isLisp):
        super().__init__(absPath, CompileStatus.Uncompiled)
        self.isLisp = isLisp
        self.data = None

    def getSearchable(self, pathElements: [str]) -> Searchable | None:
        return self #if it reaches here, its already correctly found

    def getValue(self, name: str) -> Searchable | None:
        #if python, check if its loaded
        raise NotImplementedError()
        pass

    def execute(self, callingStack: StackFrame):
        if self.compileStatus == CompileStatus.Compiled:
            raise Exception("Called execute on already compiled file, engine error")
        elif self.compileStatus == CompileStatus.Compiling:
            callingStack.throwError("Tried to compile " + self.absPath + " while already compiling, circular dependency")
        else:
            self.compileStatus = CompileStatus.Compiling
            if self.isLisp:
                text = open(self.absPath, "r").read()
                parsed = parseAll.parse([SOF_value] + list(text) + [EOF_value])
                ast = toAST(parsed.content)
                demacroedCode = DemacroTop(StackFrame(ast, self).withHandlerFrame(MacroHandlerFrame))
                self.data = Eval(StackFrame(demacroedCode, self).withHandlerFrame(RuntimeHandlerFrame))
            else:
                importedModule = importlib.import_module(self.absPath)
                self.data = importedModule
            self.compileStatus = CompileStatus.Compiled



class Container(Searchable):
    def __init__(self, absPath, children: List[Searchable]):
        super().__init__(absPath, CompileStatus.Uncompiled)
        self.children = {x.name: x for x in children}

    def fixChildren(self):
        for i in self.children.values():
            i.parent = self
        return self

    def getSearchable(self, pathElements: [str]) -> Searchable | None:
        if len(pathElements) == 0:
            return None
        print(self.children.keys())
        if pathElements[0] in self.children.keys():
            return self.children[pathElements[0]]
        return None


class Folder(Container):
    def __init__(self, absPath, children):
        super().__init__(absPath, children)


class LispPackage(Container):
    def __init__(self, absPath, children):
        super().__init__(absPath, children)


class PythonPackage(Container):
    def __init__(self, absPath, children):
        super().__init__(absPath, children)
        self.isCompiled = True


class Library(Container):
    def __init__(self, children: List[Searchable], libraryRoot):
        super().__init__(None, children)

    def getSearchableByPath(self, pathToFind): #TODO deprecated
        """
        Returns the searchable from the library corresponding to a given path
        :param pathToFind: The absolute path to a file, package or folder.
        :return: The searchable at the given path.
        """
        splittedPath = splitPathFully(pathToFind)
        rootcopy = self.libraryRoot
        while len(rootcopy) > 0:
            if rootcopy[0] != splittedPath[0]:
                raise Exception(f"Tried to find a path outside of the library: {pathToFind}")
            rootcopy = rootcopy[1:]
            splittedPath = splittedPath[1:]
            if len(splittedPath) == 0:
                raise Exception(f"Tried to find a path outside of the library: {pathToFind}")
        foundItem = self.getByPath(splittedPath)
        return foundItem


class LibraryWithFallback(Searchable):
    def __init__(self, primary: Library, fallback: Library | LibraryWithFallback):
        super().__init__(None,  #virtual folder
                         CompileStatus.Compiled
                         if primary.compileStatus == fallback.compileStatus == CompileStatus.Compiled
                         else CompileStatus.Uncompiled)
        self.primary = primary
        primary.parent = self
        self.fallback = fallback

    def getSearchable(self, pathElements: [str]) -> Searchable | None:
        if len(pathElements) == 0:
            return None
        primaryResult = self.primary.getSearchable(pathElements)
        if primaryResult is None:
            return self.fallback.getSearchable(pathElements)
        else:
            return primaryResult


def splitPathFully(path):
    splitted = []
    head = path
    tail = None
    while head is not "" and tail is not "":
        h, t = os.path.split(head)
        head = h
        tail = t
        if tail is not "":
            splitted.append(tail)
    if head is not "":
        splitted.append(head)
    splitted.reverse()
    return splitted
