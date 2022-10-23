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

exampleConfig = {
    "handledRuntimeEffects": handleExample,
    "handledMacroEffects": handleExample,
}
