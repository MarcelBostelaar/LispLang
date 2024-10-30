__import [list ["PythonFuncs" "head"]] [quote head]
__import [list ["PythonFuncs" "tail"]] [quote tail]
__import [list ["PythonFuncs" "concat"]] [quote concat]
//__import PythonFuncs.equals
__import [list ["PythonFuncs" "sum"]] [quote sum]
__import [list ["PythonFuncs" "continue_"]] [quote continue]
//__import PythonFuncs.stop_
//__import PythonFuncs.isString
//__import PythonFuncs.printFunction
__import [list ["PythonFuncs" "handlerInvocationDefinition"]] [quote handlerInvocationDefinition]
//__import PythonFuncs.genSym
list [ 
    [list ["head" head]] 
    [list ["tail" tail]] 
    [list ["concat" concat]]  
    [list ["sum" sum]]  
    [list ["handlerInvocationDefinition" handlerInvocationDefinition]] 
    [list ["continue" continue]] 
]