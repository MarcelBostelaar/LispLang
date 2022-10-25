from __future__ import annotations

import os.path
from typing import List

from ..Config.langConfig import extension, lispPackageFile
from os import listdir as __listdir
from os.path import isfile, join, basename

"""
Package imports work as follows:
It takes the file it is importing from as the starting point.
It then goes to its containing package.
From there, it sees if the first level identifier exists.
If it does, it imports further levels from there, and throws an error if it isnt found.
If it does not, it goes to the package containing the package, and tries again.
This way, imported/shared libraries can be in any arbitrary level above it, 
and you can shadow them with other packages locally.
Relative import functionally is thus unnecessary. Sibling packages act as if they are global.
"""


class Searchable:
    def __init__(self, name):
        self.name = name
        self.parent = None

    def getByPath(self, pathElements: [str]) -> Searchable:
        """Retrieves the specified subelements of this searchable"""
        raise NotImplementedError("Abstract")

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        """Retrieves a specified item using the containing package of this searchable as a base,
        going up levels as per the convention.
        """
        raise NotImplementedError("Abstract")


class Leaf(Searchable):
    def __init__(self, name, isLisp):
        super().__init__(name)
        self.isLisp = isLisp

    def getByPath(self, pathElements: [str]) -> Searchable:
        if len(pathElements) != 0:
            raise Exception(f"Tried to retrieve for {'.'.join(pathElements)} in {self.name} but {self.name} is a {'lisp' if self.isLisp else 'python'} file."
                            f"Possible naming conflict.")
        return self

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        return self.parent.getInverseRecursively(pathElements)


class Container(Searchable):
    def __init__(self, name, children: List[Searchable]):
        super().__init__(name)
        self.children = {x.name:x for x in children}

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

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        return self.parent.getInverseRecursively(pathElements)


class Library(Container):
    def __init__(self, children: List[Searchable], libraryRoot):
        super().__init__(None, children)
        self.libraryRoot = splitPathFully(libraryRoot)

    def getInverseRecursively(self, pathElements: [str]) -> Searchable:
        return self.getByPath(pathElements)

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


def listdir(folder):
    items = __listdir(folder)
    return [x for x in items if x != "__pycache__"]


def splitPathFully(path):
    splitted = []
    head = path
    tail = None
    while head is not "" and tail is not "":
        h,t = os.path.split(head)
        head = h
        tail = t
        if tail is not "":
            splitted.append(tail)
    if head is not "":
        splitted.append(head)
    splitted.reverse()
    return splitted


def getFoldersIn(folder: str):
    return [join(folder, f) for f in listdir(folder) if not isfile(join(folder, f))]


def getFilesIn(folder: str):
    return [join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]


def isLispPackage(folder: str) -> bool:
    return lispPackageFile + "." + extension in [basename(x) for x in getFilesIn(folder)]


def isPythonPackage(folder: str) -> bool:
    return "__init__.py" in [basename(x) for x in getFilesIn(folder)]


def isPythonFile(path: str) -> bool:
    return path[-3:] == ".py"


def isLispFile(path: str) -> bool:
    return path[-(len(extension) + 1):] == "." + extension


def genericMapLispFolder(folder: str) -> [Searchable]:
    files = getFilesIn(folder)
    pythonFiles: List[Searchable] = [Leaf(x, False) for x in files if isPythonFile(x)]
    lispFiles = [Leaf(x, True) for x in files if isLispFile(x)]
    folders = getFoldersIn(folder)
    regularFolders = [mapRegularFolder(x) for x in folders if not isLispPackage(x) and not isPythonPackage(x)]
    lispSubpackages = [mapLispPackage(x) for x in folders if isLispPackage(x)]
    pythonSubpackages = [mapPythonPackage(x) for x in folders if isPythonPackage(x)]

    return pythonFiles + lispFiles + regularFolders + lispSubpackages + pythonSubpackages


def mapRegularFolder(folder: str) -> Folder:
    name = basename(folder)
    children = genericMapLispFolder(folder)
    self = Folder(name, children).fixChildren()
    return self


def mapPythonPackage(folder: str) -> PythonPackage:
    subPackages: List[Searchable] = [mapPythonPackage(x) for x in getFoldersIn(folder) if isPythonPackage(x)]
    files = [Leaf(x, False) for x in getFilesIn(folder) if isPythonFile(x)]
    return PythonPackage(basename(folder), subPackages + files).fixChildren()


def mapLispPackage(folder: str) -> LispPackage:
    name = basename(folder)
    children = genericMapLispFolder(folder)
    return LispPackage(name, children).fixChildren()


def mapLibrary(rootFolder: str) -> Library:
    children = genericMapLispFolder(rootFolder)
    return Library(children, rootFolder).fixChildren()