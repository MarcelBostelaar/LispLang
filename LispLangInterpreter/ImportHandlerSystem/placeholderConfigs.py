handleExample = [
    {
        "path": "Libraries.someFile",
        "handlers": [
            {
                "nameInFile": "someName",
                "handlesFunction": "someOtherName",
            }
        ]
    },
    {
        "path": "Libraries.someOtherFile",
        "handlers": [
            {
                "nameInFile": "someName",
                "handlesFunction": "someOtherName",
            }
        ]
    }
]

libraryFallbackWord = "libraryFallback"
sourceFolderWord = "sourceFolder"

exampleConfig = {
    "enableImports": True,
    "enableExceptions": True,
    "handledRuntimeEffects": handleExample,
    "handledMacroEffects": handleExample,
    sourceFolderWord: "src",
    "mainFile": "main.lisp",
    libraryFallbackWord: {
        "path": "Libraries",
        libraryFallbackWord: {
            "abspath": "bin"
        }
    }
}
