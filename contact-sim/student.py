class Student:
    def __init__(self, id: int, classes: list):
        self._id = id
        self._classes = classes

    @property
    def id(self):
        return self._id

    @property
    def classes(self):
        return self._classes