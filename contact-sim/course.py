class Course:
    def __init__(self, id: int, datetime: int, room, prob):
        self._id = id
        self._dow = datetime // 100
        self._time = datetime - (self._dow * 100)
        self._prob = prob
        self._room = room

    @property
    def id(self):
        return self._id

    @property
    def room(self):
        return self._room

    @property
    def probability(self):
        return self._prob

    @property
    def dow(self):
        return self._dow

    @property
    def time(self):
        return self._time

    def set_room(self, room):
        self._room = room
