/**
macro functions get the entire AST list behind its initial keyword
ie
*/

macro removefirst x [
    //macro body
    tail x
]

ignore [removefirst 1 2 3]
/*
    gets turned into
ignore [2 3]

    This allows for complex macros to operate on entire subsections of code and create powerfull DSL
    Is/will be used to implement recursive functions
    Is/will be used to implement argMacro (a macro with specific numbers of args)
*/

macro argMacro x [
    let arglist [head x]
    let body [head [tail x]]
    let rest [tail [tail x]]
    quote NotImplemented
]


argMacro ' [followingList] [
    [list [quote quote [followinglist]]]
]

//random ass comment

macro if [condition _then option1 _else option2] [
    list ['cond condition option1 option2]
]



macro func [somename arguments body] /* inline comments*/ [
    let x [some calculation] //wordt uitgevoert in de macro
    list ['let somename [lambda arguments body]]
]



func somename [arg1 arg2] [
    macro dummy [test test2] [

    ]
    ignore [print arg1]
    let someshit [some calculation]
    ignore [print arg2]
    sum [list [1,2,3,4]]
]

let x [
    sum 1 [
        let z 6
        argMacro y [] [
            list [z]
        ]
        sum 3 y
    ]
]


somename "some" "string\n"