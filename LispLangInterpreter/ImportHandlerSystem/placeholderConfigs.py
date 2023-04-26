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

exampleConfig = {
    "enableImports": True,
    "enableExceptions": True,
    "handledRuntimeEffects": handleExample,
    "handledMacroEffects": handleExample,
    "sourceFolder": "src",
    libraryFallbackWord: {
        "path": "Libraries",
        libraryFallbackWord: {
            "abspath": "bin"
        }
    }
}
