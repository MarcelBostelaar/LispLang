from __future__ import annotations

from .Classes import *
from .Kind import Kind
from ..Config.langConfig import SpecialForms




def isSpecialFormKeyword(name) -> bool:
    return name in [e.value.keyword for e in SpecialForms]


def isIndirectionValue(someValue: Value):
    return someValue.kind in [Kind.Reference, Kind.StackReturnValue, Kind.HandleReturnValue]