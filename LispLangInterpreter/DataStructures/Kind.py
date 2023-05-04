from __future__ import annotations

from enum import Enum


class Kind(Enum):
    Lambda = 1
    Reference = 2
    QuotedName = 3
    List = 4
    sExpression = 5
    Char = 6
    Number = 7
    Boolean = 8
    Scope = 9
    StackReturnValue = 10
    ContinueStop = 11
    HandleReturnValue = 12
    HandlerFrame = 13
    HandleBranchPoint = 14
    Unit = 15
