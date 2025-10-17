import abc
from enum import Enum, auto

from models.guid import Guid
from models.model_element_geometry import IModelElementGeometry


class ElementKind(Enum):
    WALL = auto()
    SLAB = auto()
    ROOF = auto()
    CONTAINER = auto()
    LEAF = auto()


class IModelElement(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def guid(self) -> Guid:
        pass

    @property
    @abc.abstractmethod
    def geometry(self) -> IModelElementGeometry:
        pass

    @property
    @abc.abstractmethod
    def kind(self) -> ElementKind:
        pass

    @property
    def children(self) -> list["IModelElement"]:
        raise NotImplementedError("Children are not implemented for this model element.")


class ModelNodeElement(IModelElement):
    def __init__(self, guid: Guid, name: str, geometry: IModelElementGeometry, children: list[IModelElement]):
        self._name = name
        self._guid = guid
        self._geometry = geometry
        self._children = children

    @property
    def name(self) -> str:
        return self._name

    @property
    def guid(self) -> Guid:
        return self._guid

    @property
    def geometry(self) -> IModelElementGeometry:
        return self._geometry

    @property
    def kind(self) -> ElementKind:
        return ElementKind.CONTAINER

    @property
    def children(self) -> list[IModelElement]:
        return self._children

    def __hash__(self):
        return hash(self._guid.value)

    def __eq__(self, other):
        if not isinstance(other, ModelNodeElement):
            return NotImplemented
        return self._guid.value == other._guid.value


class ModelLeafElement(IModelElement):
    def __init__(self, guid: Guid, name: str, geometry: IModelElementGeometry):
        self._geometry: IModelElementGeometry = geometry
        self._name = name
        self._guid = guid

    @property
    def name(self) -> str:
        return self._name

    @property
    def guid(self) -> Guid:
        return self._guid

    @property
    def geometry(self) -> IModelElementGeometry:
        return self._geometry

    @property
    def kind(self) -> ElementKind:
        return ElementKind.LEAF

    def __hash__(self):
        return hash(self._guid.value)

    def __eq__(self, other):
        if not isinstance(other, ModelLeafElement):
            return NotImplemented
        return self._guid.value == other._guid.value


# Domain-specific typed elements
class Wall(ModelNodeElement):
    @property
    def kind(self) -> ElementKind:
        return ElementKind.WALL


class Slab(ModelNodeElement):
    @property
    def kind(self) -> ElementKind:
        return ElementKind.SLAB


class Roof(ModelNodeElement):
    @property
    def kind(self) -> ElementKind:
        return ElementKind.ROOF


class Container(ModelNodeElement):
    @property
    def kind(self) -> ElementKind:
        return ElementKind.CONTAINER
