from compas.geometry import bounding_box


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
