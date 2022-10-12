class HandlerStateRegistry:
    def __init__(self):
        self.value = []

    def registerHandlerFrame(self, stateSeed) -> int:
        """
        Saves the given starting state to the handler ID and returns the corresponding new ID
        :param stateSeed:
        :return: An integer ID for the specific stacks state
        """
        index = len(self.value)
        self.value.append(stateSeed)
        return index

    def unregisterHandlerFrame(self, ID: int):
        """
        Frees the handler frame with the given ID and removed the state from storage
        :param ID:
        :return:
        """
        if ID + 1 != len(self.value):
            raise Exception("Code error, deregistration should happen from end to top.")
        self.value.pop()

    def retrieveState(self, ID: int):
        if ID > len(self.value):
            raise Exception("Code error")
        return self.value[ID]

    def setState(self, ID: int, stateValue):
        if ID > len(self.value):
            raise Exception("Code error")
        self.value[ID] = stateValue


HandlerStateSingleton = HandlerStateRegistry()
