from .cad_adapter import (
    # Composite interface (for backward compatibility)
    ICadAdapter,
    # Segregated interfaces
    IElementIdentifier,
    IElementGeometry,
    IElementClassification,
    IElementGrouping,
    IBuildingInformation,
    # Specialized adapter implementations
    ElementIdentifierAdapter,
    ElementGeometryAdapter,
    ElementClassificationAdapter,
    ElementGroupingAdapter,
    BuildingInformationAdapter,
    # Facade implementation
    CadworkAdapter,
    # Utilities
    to_vector,
    to_point,
    get_aabb_vertices,
    ElementGroupingType,
)

__all__ = [
    # Composite interface
    'ICadAdapter',
    # Segregated interfaces
    'IElementIdentifier',
    'IElementGeometry',
    'IElementClassification',
    'IElementGrouping',
    'IBuildingInformation',
    # Specialized adapter implementations
    'ElementIdentifierAdapter',
    'ElementGeometryAdapter',
    'ElementClassificationAdapter',
    'ElementGroupingAdapter',
    'BuildingInformationAdapter',
    # Facade implementation
    'CadworkAdapter',
    # Utilities
    'to_vector',
    'to_point',
    'get_aabb_vertices',
    'ElementGroupingType',
]
