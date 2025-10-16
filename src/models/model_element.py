import abc

from models.guid import Guid
from models.model_element_geometry import IModelElementGeometry


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


class ModelElement(IModelElement):
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

    def __hash__(self):
        return hash(self._guid.value)

    def __eq__(self, other):
        if not isinstance(other, ModelElement):
            return NotImplemented
        return self._guid.value == other._guid.value
