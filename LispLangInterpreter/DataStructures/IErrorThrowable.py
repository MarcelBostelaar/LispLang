
class IErrorThrowable:
    def throwError(self, errorMessage):
        raise NotImplementedError("Abstract")


class ErrorCatcher(IErrorThrowable):
    def __init__(self):
        self.error = None

    def throwError(self, errorMessage):
        raise Exception(self.error)