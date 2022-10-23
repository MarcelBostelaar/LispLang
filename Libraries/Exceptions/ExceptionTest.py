from LispLangInterpreter.DataStructures.Classes import *

def exceptionInternal(exceptionMessage, callingFrame: StackFrame):
    callingFrame.throwError(exceptionMessage.serialize())

exceptionEndpoint = SystemFunction(exceptionInternal, 1)