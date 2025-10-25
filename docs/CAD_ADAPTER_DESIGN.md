# CAD Adapter Pattern - Design Documentation

## Overview

The CAD Adapter pattern provides a clean abstraction layer over the cadwork API, enabling:

- **Testability**: Write unit tests without a running CAD instance
- **Dependency Injection**: Pass adapters to services and builders
- **Maintainability**: Centralize CAD API interactions in one place
- **Flexibility**: Easy to swap implementations (production, mock, stub)

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────┐
│                   Your Services/Builders                 │
│  (ModelElementTreeBuilder, ModelElementFactory, etc.)   │
└───────────────────────┬─────────────────────────────────┘
                        │ depends on
                        ▼
┌─────────────────────────────────────────────────────────┐
│                    ICadAdapter (Protocol)                │
│  - Defines interface for all CAD operations             │
│  - Pure abstraction, no implementation                   │
└───────────────────────┬─────────────────────────────────┘
                        │ implemented by
           ┌────────────┴────────────┐
           ▼                         ▼
┌──────────────────────┐  ┌──────────────────────┐
│  CadworkAdapter      │  │  MockCadAdapter      │
│  (Production)        │  │  (Testing)           │
│                      │  │                      │
│  - Wraps real CAD    │  │  - In-memory data    │
│    API controllers   │  │  - Predictable       │
│  - Requires CAD      │  │  - No CAD needed     │
│    instance running  │  │                      │
└──────────────────────┘  └──────────────────────┘
```

## Usage

### Production Code

```python
from cad_adapter.cad_adapter import CadworkAdapter
from allocation.model_tree_builder import ModelElementTreeBuilder

# Create the production adapter
adapter = CadworkAdapter()

# Inject it into your builder/service
builder = ModelElementTreeBuilder(element_ids, adapter)
trees = builder.build()
```

### Test Code

```python
from tests.mock_cad_adapter import MockCadAdapter
from allocation.model_tree_builder import ModelElementTreeBuilder

# Create a mock adapter
mock = MockCadAdapter()

# Setup test data
mock.add_element(1, "TestWall", is_wall=True, subgroup="G1")
mock.add_element(2, "TestBeam", subgroup="G1")

# Use it in tests
builder = ModelElementTreeBuilder([1, 2], mock)
trees = builder.build()

# Assert expected behavior
assert len(trees) == 1
assert trees[0].name == "TestWall"
assert len(trees[0].children) == 1
```

## File Structure

```
src/allocation/
├── cad_adapter.py              # Interface + Production adapter
│   ├── ICadAdapter             # Protocol defining the interface
│   ├── CadworkAdapter          # Production implementation
│   ├── to_point()              # Utility functions
│   └── to_vector()
│
├── model_element_factory.py    # Factory using adapter
├── model_tree_builder.py       # Builder using adapter
├── storey_assignment_service.py # Service using adapter
└── cwapi_wrapper.py            # Legacy wrapper (backward compat)

tests/
├── mock_cad_adapter.py         # Mock implementation
└── test_with_mock_adapter.py   # Example tests
```

## Migration Guide

### Before (Direct CAD API usage)

```python
import attribute_controller as ac
import element_controller as ec
import geometry_controller as gc


class MyBuilder:
    def build(self, element_id):
        name = ac.get_name(element_id)
        guid = ec.get_element_cadwork_guid(element_id)
        p1 = gc.get_p1(element_id)
        # ...
```

**Problems:**

- ❌ Cannot test without CAD instance
- ❌ Hard to mock
- ❌ Direct dependencies scattered everywhere

### After (Adapter pattern)

```python
from .cad_adapter import ICadAdapter


class MyBuilder:
    def __init__(self, adapter: ICadAdapter):
        self._adapter = adapter

    def build(self, element_id):
        name = self._adapter.get_name(element_id)
        guid = self._adapter.get_element_cadwork_guid(element_id)
        p1 = self._adapter.get_p1(element_id)
        # ...
```

**Benefits:**

- ✅ Testable with mock adapter
- ✅ Clean dependency injection
- ✅ Centralized CAD API access

## Best Practices

### 1. Always Use Dependency Injection

**Good:**

```python
class MyService:
    def __init__(self, adapter: ICadAdapter):
        self._adapter = adapter
```

**Bad:**

```python
class MyService:
    def __init__(self):
        self._adapter = CadworkAdapter()  # Hard-coded dependency
```

### 2. Accept the Interface, Not the Implementation

**Good:**

```python
def process_elements(adapter: ICadAdapter) -> list:
    ...
```

**Bad:**

```python
def process_elements(adapter: CadworkAdapter) -> list:  # Too specific
    ...
```

### 3. Keep the Adapter Thin

The adapter should only:

- ✅ Forward calls to CAD API
- ✅ Convert data types (e.g., point_3d → Point)
- ❌ Not contain business logic
- ❌ Not make decisions

### 4. Create Focused Mock Data in Tests

```python
def test_wall_with_beams():
    mock = MockCadAdapter()

    # Only add the data needed for this test
    mock.add_element(1, "Wall", is_wall=True, subgroup="G1")
    mock.add_element(2, "Beam1", subgroup="G1")
    mock.add_element(3, "Beam2", subgroup="G1")

    # Test focuses on wall+beam relationship
    builder = ModelElementTreeBuilder([1, 2, 3], mock)
    trees = builder.build()

    assert len(trees[0].children) == 2
```

## Extension Points

### Adding New CAD Operations

1. **Add to the interface** (`ICadAdapter`):

```python
@runtime_checkable
class ICadAdapter(Protocol):
    # ... existing methods ...

    def get_element_color(self, element_id: int) -> tuple[int, int, int]:
        """Get RGB color of an element."""
        ...
```

2. **Implement in production adapter** (`CadworkAdapter`):

```python
class CadworkAdapter:
    # ... existing methods ...

    def get_element_color(self, element_id: int) -> tuple[int, int, int]:
        color = self._ac.get_color(element_id)
        return (color.r, color.g, color.b)
```

3. **Implement in mock adapter** (`MockCadAdapter`):

```python
class MockCadAdapter:
    # ... existing methods ...
    
    def get_element_color(self, element_id: int) -> tuple[int, int, int]:
        return self._elements.get(element_id, {}).get('color', (255, 255, 255))
```

### Creating Custom Adapters

You can create specialized adapters for different scenarios:

```python
class LoggingCadAdapter(ICadAdapter):
    """Adapter that logs all CAD operations."""

    def __init__(self, inner_adapter: ICadAdapter):
        self._inner = inner_adapter

    def get_name(self, element_id: int) -> str:
        logger.info(f"Getting name for element {element_id}")
        return self._inner.get_name(element_id)

    # ... delegate all other methods with logging ...
```

```python
class CachingCadAdapter(ICadAdapter):
    """Adapter that caches frequently accessed data."""

    def __init__(self, inner_adapter: ICadAdapter):
        self._inner = inner_adapter
        self._cache = {}

    def get_name(self, element_id: int) -> str:
        if element_id not in self._cache:
            self._cache[element_id] = self._inner.get_name(element_id)
        return self._cache[element_id]
```

## Troubleshooting

### "Module not found" errors in tests

If you see import errors when running tests, make sure:

1. Your `PYTHONPATH` includes the project root
2. Or run tests with: `python -m pytest tests/`

### "cadwork module not found" in production

The `CadworkAdapter` imports cadwork controllers in `__init__`. This is intentional:

- ✅ Fails fast if CAD is not available
- ✅ Makes it clear this needs a CAD instance
- ✅ Tests use `MockCadAdapter` and never import `CadworkAdapter`

### Type checking complaints about Protocol

If your IDE complains about Protocol usage:

- Make sure you're using Python 3.8+
- The `@runtime_checkable` decorator enables `isinstance()` checks
- Protocol is structural typing (duck typing with type hints)

## Related Patterns

- **Adapter Pattern**: Wraps incompatible interfaces (what we use here)
- **Strategy Pattern**: Could use adapters as strategies for different CAD systems
- **Facade Pattern**: The adapter also acts as a facade, simplifying the CAD API
- **Dependency Injection**: Core principle enabling testability

## References

- [PEP 544 – Protocols: Structural subtyping](https://peps.python.org/pep-0544/)
- [Dependency Injection in Python](https://en.wikipedia.org/wiki/Dependency_injection)
- [Adapter Pattern](https://refactoring.guru/design-patterns/adapter)
