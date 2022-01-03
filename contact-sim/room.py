from building import Building


class Room:
    def __init__(self, id: int):
        self._id = id
        self._building = None

    @property
    def id(self):
        return self._id

    @property
    def building(self):
        return self._building

    def set_building(self, building: Building):
        self._building = building
