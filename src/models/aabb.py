from compas.geometry import bounding_box
from compas.geometry import Point


class BoundingBox:
    """Bounding box defined by 8 corner points.

    Parameters
    ----------
    corner_points : list[[float, float, float]]
        XYZ coordinates of 8 points defining a box.

    """

    def __init__(self, corner_points: list):
        self._corner_points = bounding_box(corner_points)

    @classmethod
    def from_points(cls, points: list) -> "BoundingBox":
        """Constructs a Bounding box that contains the given points.

        Parameters
        ----------
        points : list[[float, float, float]]
            XYZ coordinates of the points.

        Returns
        -------
        BoundingBox
            The bounding box.

        """
        if len(points) < 3:
            raise ValueError("At least 3 points are required.")
        bbox = bounding_box(points)
        return cls(bbox)

    def to_list(self) -> list:
        """Returns the corner points of the bounding box as a list.

        Returns
        -------
        list[[float, float, float]]
            XYZ coordinates of 8 points defining a box.

        """
        return self._corner_points

    def centroid(self) -> Point:
        """Returns the centroid of the bounding box.

        Returns
        -------
        list[float]
            XYZ coordinates of the centroid.

        """
        x_coords = [p[0] for p in self._corner_points]
        y_coords = [p[1] for p in self._corner_points]
        z_coords = [p[2] for p in self._corner_points]
        centroid = [
            sum(x_coords) / len(x_coords),
            sum(y_coords) / len(y_coords),
            sum(z_coords) / len(z_coords),
        ]
        return Point(*centroid)
