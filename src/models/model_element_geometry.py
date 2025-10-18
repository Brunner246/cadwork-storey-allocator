import abc

from compas.geometry import Point
from compas.geometry import Vector

from .aabb import BoundingBox


class IModelElementGeometry(abc.ABC):

    @abc.abstractmethod
    def local_x_direction(self) -> Vector:
        pass

    @abc.abstractmethod
    def local_y_direction(self) -> Vector:
        pass

    @abc.abstractmethod
    def local_z_direction(self) -> Vector:
        pass

    @abc.abstractmethod
    def local_origin(self) -> Point:
        pass

    @abc.abstractmethod
    def bbx(self) -> BoundingBox:
        pass


class ModelElementGeometry(IModelElementGeometry):
    def __init__(self,
                 local_origin: Point,
                 local_x_direction: Vector,
                 local_y_direction: Vector,
                 local_z_direction: Vector,
                 bbx: list[Point]):
        self._local_origin: Point = local_origin
        self._local_x_direction: Vector = local_x_direction
        self._local_y_direction: Vector = local_y_direction
        self._local_z_direction: Vector = local_z_direction
        try:
            self._bbx: BoundingBox = BoundingBox.from_points(bbx)
        except ValueError as e:
            raise ValueError(f"Invalid Bounding Box data. {e}")

        if all(v.length < 1e-6 for v in (local_x_direction, local_y_direction, local_z_direction)):
            raise ValueError("At least one direction vector must be non-zero.")

    def local_x_direction(self) -> Vector:
        return self._local_x_direction

    def local_y_direction(self) -> Vector:
        return self._local_y_direction

    def local_z_direction(self) -> Vector:
        return self._local_z_direction

    def local_origin(self) -> Point:
        return self._local_origin

    def bbx(self) -> BoundingBox:
        return self._bbx
