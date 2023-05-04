from __future__ import annotations

from enum import Enum


class CompileStatus(Enum):
    Uncompiled = 0
    Compiling = 1
    Compiled = 2
