from __future__ import annotations

import os.path
from typing import List

from .LibraryClasses import Searchable, Leaf, Folder, LispPackage, PythonPackage, Library, LibraryWithFallback
from .placeholderConfigs import libraryFallbackWord
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


def listdir(folder):
    items = __listdir(folder)
    return [x for x in items if x != "__pycache__"]


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


def makeAbs(path):
    return os.path.join(os.path.abspath(os.getcwd()), path)


def mapLibrary(primaryAbsPath: str, libraryConfig) -> Library | LibraryWithFallback:
    if "path" in libraryConfig.keys():
        fallbackPath = makeAbs(libraryConfig["path"])
    elif "abspath" in libraryConfig.keys():
        fallbackPath = libraryConfig["abspath"]
    else:
        raise Exception("Path for fallback library not found")

    primary = Library(genericMapLispFolder(primaryAbsPath), primaryAbsPath).fixChildren()
    if libraryFallbackWord not in libraryConfig.keys():
        fallback = Library(genericMapLispFolder(fallbackPath), fallbackPath).fixChildren()
    else:
        fallback = mapLibrary(fallbackPath, libraryConfig[libraryFallbackWord])
    return LibraryWithFallback(primary, fallback)