__import [list ["StandardLibrary" "sum"]] [quote sum]
__import [list ["StandardLibrary" "tail"]] [quote tail]
__import [list ["StandardLibrary" "head"]] [quote head]
__import [list ["StandardLibrary" "concat"]] [quote concat]

macro test2 outerScope ast [
    let front [tail ast]
    let end [head ast]
    concat front [list [end]]
]

test2 1 sum 4