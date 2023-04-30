from __future__ import annotations

import os
from enum import Enum
from typing import List


class CompileStatus(Enum):
    Uncompiled = 0
    Compiling = 1
    Compiled = 2


class Searchable:
    def __init__(self, name, compileStatus: CompileStatus):
        self.name = name
        self.parent = None
        self.compileStatus: CompileStatus = compileStatus
        self.values = {}

    def getByPath(self, pathElements: [str]) -> Searchable:
        """Retrieves the specified subelements of this searchable"""
        raise NotImplementedError("Abstract")

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        """Retrieves a specified item using the containing package of this searchable as a base,
        going up levels as per the convention.
        """
        raise NotImplementedError("Abstract")

    def getSearchable(self, pathElement: [str]) -> Searchable:
        """
        Gets the specified searchable where the specified value is located, or None if not found
        :param pathElement: List of elements
        :return: Searchable or None
        """
        raise NotImplementedError("Abstract")

    def getValue(self, name: str) -> Searchable:
        """
        Attempts to get a value from the given searchable
        :param name: Name of the item to import
        :return: Found value, or None if none was found.
        """
        raise NotImplementedError("Abstract")


class Leaf(Searchable):
    def __init__(self, name, isLisp):
        super().__init__(name,
                         CompileStatus.Uncompiled if isLisp else CompileStatus.Compiled)  # python files are compiled by default
        self.isLisp = isLisp

    def getByPath(self, pathElements: [str]) -> Searchable:
        if len(pathElements) != 0:
            raise Exception(
                f"Tried to retrieve for {'.'.join(pathElements)} in {self.name} but {self.name} is a {'lisp' if self.isLisp else 'python'} file."
                f"Possible naming conflict.")
        return self

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        return self.parent.getInverseRecursively(pathElements)


class Container(Searchable):
    def __init__(self, name, children: List[Searchable]):
        super().__init__(name, CompileStatus.Uncompiled)  # TODO FIX
        self.children = {x.name: x for x in children}

    def getByPath(self, pathElements: [str]):
        if len(pathElements) == 0:
            return self
        if pathElements[0] in self.children.keys():
            return self.children[pathElements[0]].getByPath(pathElements[1:])
        raise Exception(f"Tried to retrieve for {'.'.join(pathElements)} in {self.name} but {self.name} was not found."
                        f"Possible naming conflict.")

    def fixChildren(self):
        for i in self.children.values():
            i.parent = self
        return self

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        raise NotImplementedError("Abstract")


class Folder(Container):
    def __init__(self, name, children):
        super().__init__(name, children)

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        return self.parent.getInverseRecursively(pathElements)


class LispPackage(Container):
    def __init__(self, name, children):
        super().__init__(name, children)

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        if pathElements[0] in self.children.keys():
            return self.children[pathElements[0]].getByPath(pathElements[1:])
        return self.parent.getInverseRecursively(pathElements)


class PythonPackage(Container):
    def __init__(self, name, children):
        super().__init__(name, children)
        self.isCompiled = True

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        return self.parent.getInverseRecursively(pathElements)


class Library(Container):
    def __init__(self, children: List[Searchable], libraryRoot):
        super().__init__(None, children)
        self.libraryRoot = splitPathFully(libraryRoot)

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        if self.parent is None:
            return self.getByPath(pathElements)
        else:
            if pathElements[0] in self.children.keys():
                return self.getByPath(pathElements)
            return self.parent.getInverseRecursively(pathElements)

    def getSearchableByPath(self, pathToFind):
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
        super().__init__(None,
                         CompileStatus.Compiled
                         if primary.compileStatus == fallback.compileStatus == CompileStatus.Compiled
                         else CompileStatus.Uncompiled)
        self.primary = primary
        primary.parent = self
        self.fallback = fallback

    def getByPath(self, pathElements: [str]) -> Searchable:
        if pathElements[0] in self.primary.children.keys():
            return self.primary.getByPath(pathElements)
        return self.fallback.getByPath(pathElements)

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        return self.getByPath(pathElements)


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
