from __future__ import annotations
from ..Config.Singletons import writeLineLog
from ..Config import langConfig

def escape_string(string):
    writeLineLog("TODO implement string escaping")  # todo
    return string


def checkReservedKeyword(callingFrame: StackFrame, name):
    if name in langConfig.reservedWords:
        callingFrame.throwError("Tried to override the reserved keyword '" + name + "'. Now allowed.")