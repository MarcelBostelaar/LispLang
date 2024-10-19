__import [list ["StandardLibrary" "sum"]] [quote sum]

macro test outerScope ast [
    ast
]

sum test 1 2