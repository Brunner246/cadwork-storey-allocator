import dataclasses


@dataclasses.dataclass
class BuildingStorey:
    building_name: str
    storey_name: str
    elevation: float

    # elements: Iterable[models.IModelElement] = dataclasses.field(default_factory=list)

    def __hash__(self) -> int:
        return hash((self.building_name, self.storey_name))

    def __eq__(self, other) -> bool:
        if not isinstance(other, BuildingStorey):
            return NotImplemented
        return (self.building_name, self.storey_name) == (other.building_name, other.storey_name)

    def __lt__(self, other) -> bool:
        if not isinstance(other, BuildingStorey):
            return NotImplemented
        return self.elevation < other.elevation



@dataclasses.dataclass
class Building:
    name: str
    storeys: list[BuildingStorey]

    def __post_init__(self):
        self.storeys.sort(key=lambda s: s.elevation)

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Building):
            return NotImplemented
        return self.name == other.name
