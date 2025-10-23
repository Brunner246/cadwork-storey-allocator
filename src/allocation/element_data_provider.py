from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from compas.geometry import Point, Vector


class GroupingType(Enum):
    SUBGROUP = "subgroup"
    GROUP = "group"


class ElementDataProvider(ABC):
    @abstractmethod
    def is_wall(self, element_id: int) -> bool:
        pass

    @abstractmethod
    def is_floor(self, element_id: int) -> bool:
        pass

    @abstractmethod
    def is_roof(self, element_id: int) -> bool:
        pass

    @abstractmethod
    def is_container(self, element_id: int) -> bool:
        pass

    @abstractmethod
    def get_subgroup(self, element_id: int) -> str:
        pass

    @abstractmethod
    def get_group(self, element_id: int) -> str:
        pass

    @abstractmethod
    def get_grouping_type(self) -> GroupingType:
        pass

    @abstractmethod
    def get_name(self, element_id: int) -> str:
        pass

    @abstractmethod
    def get_cadwork_guid(self, element_id: int) -> str:
        pass

    @abstractmethod
    def get_p1(self, element_id: int) -> Point:
        pass

    @abstractmethod
    def get_xl(self, element_id: int) -> Vector:
        pass

    @abstractmethod
    def get_yl(self, element_id: int) -> Vector:
        pass

    @abstractmethod
    def get_zl(self, element_id: int) -> Vector:
        pass

    @abstractmethod
    def get_aabb_vertices(self, element_id: int) -> List[Point]:
        pass
