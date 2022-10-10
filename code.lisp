letf x y = [
    ignore [print y]
    sum y 4
]

/* seed -> input (many) -> continue<seed'>/stop<value> */
letf printhandler state value = [
    cond [[isString value]]
        [continue [concat state value]]
        [stop state]
]
/*handle effectfullCode [list [handler1 handler2 etc]] stateSeed*/
//handlers must have compatible/identical state types, and return a continue or stop
let someResult = handle [x 3] [list [printhandler]] ""
//someResult = List [normalReturnValue handledStateResult]