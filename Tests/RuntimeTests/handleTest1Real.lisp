let print [declareEffectfulFunction [quote print] 1]

let somefunction [lambda [x] [
    ignore [print "some string"]
    ignore [print x]
    1
    ]
]

let printHandler [lambda [state toPrint] [
    let state [concat state toPrint]
    let state [concat state "\n"]
    continue unit state
    ]
]

handle [somefunction "other string!"] [list [[list [[quote print] printHandler]]]] ""