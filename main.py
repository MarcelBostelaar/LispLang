from LispLangInterpreter.Evaluator.runFile import start

if __name__ == '__main__':
    # main("", "eval", "testcode.lisp")
    #main(*sys.argv)
    data = start()
    print(data.serializeLLQ())
    pass


