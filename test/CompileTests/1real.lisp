/*
Allows for easy list head deconstruction
listcut [a b c] rest <somelist> =>
let a = first  item of <somelist>
let b = second item of <somelist>
let c = third  item of <somelist>
let rest = the rest of <somelist>
*/
macro listcut ast context[
    let varlist  [head ast]
    let tailvar  [head [tail ast]]
    let somelist [head [tail [tail ast]]]
    let ast      [tail [tail [tail ast]]]

    let varlistRest [tail varlist]
    let varlistHead [head varlist]

    cond [> [length varlistRest] 0] [
        concat [
            list [
                [quote let] varlistHead [list [[quote head] somelist]]
                [quote listcut] varlistRest tailvar [list [[quote tail] [somelist]]]
            ]
            ast
        ]
    ]
    [
        concat [
            list [
                [quote let] tailvar somelist
            ]
            ast
        ]
    ]
]


macro argMacro ast context[

    /*output (code unfinished)*/
    macro macroname nestedAst context [
        let args [head nestedAst]
        let nestedAst [tail nestedAst]
        listcut args rest nestedAst
    ]
]

macro list ast context [
    /*moet special form zijn, list y => List([Eval(x, cxt) for x in y])*/
]

macro letf ast context [
    let args [head ast]
    let body [head [tail ast]]
    let rest [tail [tail ast]]
    quote [let
]