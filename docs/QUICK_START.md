# Quick Start Guide - CAD Adapter Pattern

## TL;DR

Your CAD API dependencies are now wrapped in a testable adapter pattern. Here's all you need to know:

## 5-Minute Setup

### 1. Production Code (with CAD running)

```python
from cad_adapter.cad_adapter import CadworkAdapter
from src.allocation.model_tree_builder import ModelElementTreeBuilder

# Create adapter
adapter = CadworkAdapter()

# Use it
builder = ModelElementTreeBuilder(element_ids, adapter)
trees = builder.build()
```

### 2. Test Code (no CAD needed)

```python
from tests.mock_cad_adapter import MockCadAdapter

# Create mock
mock = MockCadAdapter()
mock.add_element(1, "Wall", is_wall=True, subgroup="G1")
mock.add_element(2, "Beam", subgroup="G1")

# Test
builder = ModelElementTreeBuilder([1, 2], mock)
trees = builder.build()

assert trees[0].name == "Wall"
assert len(trees[0].children) == 1
```

## What Changed?

### Before ❌

```python
import attribute_controller as ac
import element_controller as ec


class MyBuilder:
    def build(self, element_id):
        name = ac.get_name(element_id)
        # Cannot test without CAD!
```

### After ✅

```python
from .cad_adapter import ICadAdapter


class MyBuilder:
    def __init__(self, adapter: ICadAdapter):
        self._adapter = adapter

    def build(self, element_id):
        name = self._adapter.get_name(element_id)
        # Can test with mock!
```

## File Cheat Sheet

| File                       | Purpose                        | When to Use                  |
|----------------------------|--------------------------------|------------------------------|
| `cad_adapter.py`           | Interface + Production adapter | Import when writing new code |
| `mock_cad_adapter.py`      | Test mock                      | Import in test files         |
| `model_element_factory.py` | Updated to use adapter         | Use with adapter injection   |
| `model_tree_builder.py`    | Updated to use adapter         | Use with adapter injection   |
| `cwapi_wrapper.py`         | Backward compatibility         | Legacy code (still works!)   |

## Common Patterns

### Pattern 1: Service with Adapter

```python
class MyService:
    def __init__(self, adapter: ICadAdapter):
        self._adapter = adapter

    def process(self, element_id: int):
        return self._adapter.get_name(element_id)
```

### Pattern 2: Testing the Service

```python
def test_my_service():
    mock = MockCadAdapter()
    mock.add_element(1, "Test")
    
    service = MyService(mock)
    result = service.process(1)
    
    assert result == "Test"
```

### Pattern 3: Factory Function with Adapter

```python
def create_elements(ids: list[int], adapter: ICadAdapter):
    factory = ModelElementFactory(adapter)
    return [factory.create(id) for id in ids]
```

## When to Use What

| Scenario           | Use This                                |
|--------------------|-----------------------------------------|
| Writing new code   | Accept `ICadAdapter` in constructor     |
| Testing services   | Use `MockCadAdapter`                    |
| Production runtime | Create `CadworkAdapter()`               |
| Legacy code        | Keep using it (it's updated internally) |
| Need more CAD ops  | Extend `ICadAdapter` protocol           |

## Example: Complete Test

```python
def test_wall_with_children():
    # Setup
    mock = MockCadAdapter()
    mock.add_element(1, "Wall-1", is_wall=True, subgroup="G1")
    mock.add_element(2, "Beam-1", subgroup="G1")
    mock.add_element(3, "Beam-2", subgroup="G1")

    # Execute
    builder = ModelElementTreeBuilder([1, 2, 3], mock)
    trees = builder.build()

    # Verify
    assert len(trees) == 1
    assert isinstance(trees[0], models.Wall)
    assert len(trees[0].children) == 2
```

## Troubleshooting

**Error: "adapter not defined"**
→ Add adapter parameter to your constructor

**Error: "cadwork module not found"** (in tests)
→ Use `MockCadAdapter`, not `CadworkAdapter` in tests

**My tests still need CAD**
→ You're using `CadworkAdapter` instead of `MockCadAdapter`

## What's Next?

1. ✅ **You're done!** - Your code is already using the adapter
2. 📝 **Write tests** - Use `MockCadAdapter` for unit tests
3. 🔄 **Migrate gradually** - Update new code to use adapter pattern
4. 📚 **Read more** - Check `docs/CAD_ADAPTER_DESIGN.md` for details

## Need Help?

- **Architecture details**: `docs/CAD_ADAPTER_DESIGN.md`
- **Full examples**: `examples/usage_example.py`
- **Test examples**: `tests/test_with_mock_adapter.py`
- **Implementation notes**: `docs/IMPLEMENTATION_SUMMARY.md`

---

**Bottom line**: Inject `CadworkAdapter()` in production, `MockCadAdapter()` in tests. That's it! 🎉
