runtimeConfig = None
currentFileSystem = None

MacroHandlerFrame = None
RuntimeHandlerFrame = None

debug = False

consolePrint = False
textPrint = False
if textPrint:
    log = open("log.txt", "w")


def writeLineLog(obj):
    stringed = str(obj)
    if consolePrint:
        print(stringed)
    if textPrint:
        log.write(stringed + "\n")
