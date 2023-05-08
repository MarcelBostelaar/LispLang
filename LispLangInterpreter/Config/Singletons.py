runtimeConfig = None
currentFileSystem = None

MacroHandlerFrame = None
RuntimeHandlerFrame = None

log = open("log.txt", "w")

consolePrint = False
textPrint = True


def writeLineLog(obj):
    stringed = str(obj)
    if consolePrint:
        print(stringed)
    if textPrint:
        log.write(stringed + "\n")
