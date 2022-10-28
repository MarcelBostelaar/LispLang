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
    "handledRuntimeEffects": handleExample,
    "handledMacroEffects": handleExample,
    "sourceFolder" : "src",
    libraryFallbackWord: {
        "path": "Libraries",
        libraryFallbackWord: {
            "abspath": "bin"
        }
    }
}
