class Building:
    def __init__(self, id: int):
        self._id = id
        self._rooms = []

    @property
    def id(self):
        return self._id

    def add_room(self, room):
        room.set_building(self)
        self._rooms.append(room)
