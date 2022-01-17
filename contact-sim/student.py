class Student:
    def __init__(self, id: int, classes: list):
        self._id = id
        self._classes = classes
        self._fname = "Person"
        self._lname = "Last"
        self._email = f"Person{id}Last{id}@fake.com"

    @property
    def id(self):
        return self._id

    @property
    def email(self):
        return self._email

    def set_email(self, email: str):
        self._email = email

    @property
    def fname(self):
        return self._fname

    @property
    def lname(self):
        return self._lname

    @property
    def classes(self):
        return self._classes
