from LispLangInterpreter.DataStructures.Classes import *


def q(x):
    return QuotedName(x)


expected = List([
    q("somename"), List([q("nested"), q("item")]),
    Number(1.566), q("cijfer"),
    q("heel"), q("getal"), Number(1.0),
    List([q("dubbel"), List([q("genest")])]),
    Boolean(True), Boolean(False)
])
