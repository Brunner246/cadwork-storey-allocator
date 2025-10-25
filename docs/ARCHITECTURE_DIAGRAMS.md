# Architecture Diagrams

This document contains architectural diagrams for the CAD Adapter Pattern implementation using Mermaid syntax.

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Component Diagram](#component-diagram)
- [Class Diagram](#class-diagram)
- [Sequence Diagrams](#sequence-diagrams)
    - [Production Flow](#production-flow)
    - [Test Flow](#test-flow)
    - [Tree Building Flow](#tree-building-flow)
- [Dependency Graph](#dependency-graph)
- [Testing Architecture](#testing-architecture)
- [Data Flow Diagram](#data-flow-diagram)

---

## High-Level Architecture

```mermaid
graph TB
    subgraph Application["Application Layer"]
        Entry[Main Entry Point]
        StoreyService[Storey Assignment Service]
        BuildingBuilder[Building Storey Builder]
    end

    subgraph Service["Service Layer"]
        TreeBuilder[ModelElementTreeBuilder]
        Factory[ModelElementFactory]
        Assignment[Assignment Visitors]
        Wrapper[cwapi_wrapper]
    end

    subgraph Adapter["Adapter Layer - Interface"]
        IAdapter[ICadAdapter Protocol<br/>---<br/>20+ method signatures]
    end

    subgraph Production["Production Implementation"]
        CadAdapter[CadworkAdapter]
        EC[element_controller]
        GC[geometry_controller]
        AC[attribute_controller]
        BC[bim_controller]
    end

    subgraph Testing["Testing Implementation"]
        MockAdapter[MockCadAdapter]
        TestData[In-Memory Test Data<br/>Dict of Elements]
    end

    Entry --> TreeBuilder
    Entry --> Factory
    StoreyService --> TreeBuilder
    BuildingBuilder --> Wrapper
    TreeBuilder --> IAdapter
    Factory --> IAdapter
    Assignment --> IAdapter
    Wrapper --> CadAdapter
    IAdapter -. implements .-> CadAdapter
    IAdapter -. implements .-> MockAdapter
    CadAdapter --> EC
    CadAdapter --> GC
    CadAdapter --> AC
    CadAdapter --> BC
    MockAdapter --> TestData
    style IAdapter fill: #e1f5ff, stroke: #0066cc, stroke-width: 3px
    style CadAdapter fill: #d4edda, stroke: #28a745, stroke-width: 2px
    style MockAdapter fill: #fff3cd, stroke: #ffc107, stroke-width: 2px
    style Application fill: #f8f9fa, stroke: #6c757d
    style Service fill: #e7f3ff, stroke: #0056b3
    style Production fill: #d4edda, stroke: #28a745
    style Testing fill: #fff3cd, stroke: #ffc107
```

---

## Component Diagram

```mermaid
graph LR
    subgraph Application["Application Components"]
        A1[storey_allocator.py]
        A2[storey_assignment_service]
        A3[building_storey_builder]
    end

    subgraph Services["Service Components"]
        S1[ModelElementTreeBuilder]
        S2[ModelElementFactory]
        S3[BuildingRegistry]
        S4[StoreyAssignmentService]
    end

    subgraph Adapters["Adapter Components"]
        AD1[cad_adapter.py]
        AD2[ICadAdapter Protocol]
        AD3[CadworkAdapter]
        AD4[cwapi_wrapper.py]
    end

    subgraph Models["Model Components"]
        M1[model_element.py]
        M2[spatial_element.py]
        M3[building_storey_boundary.py]
    end

    subgraph Tests["Test Components"]
        T1[mock_cad_adapter.py]
        T2[test_with_mock_adapter.py]
    end

    A1 --> A2
    A1 --> A3
    A2 --> S1
    A2 --> S4
    A3 --> S2
    S1 --> AD2
    S2 --> AD2
    S4 --> AD2
    AD2 --> AD3
    AD2 --> T1
    AD4 --> AD3
    S1 --> M1
    S2 --> M1
    S4 --> M3
    T2 --> T1
    T2 --> S1
    T2 --> S2
    style AD2 fill: #e1f5ff, stroke: #0066cc, stroke-width: 3px
    style AD3 fill: #d4edda, stroke: #28a745
    style T1 fill: #fff3cd, stroke: #ffc107
```

---

## Class Diagram

```mermaid
classDiagram
    class ICadAdapter {
        <<Protocol>>
    }

    class CadworkAdapter {
        -_ec element_controller
        -_gc geometry_controller
        -_ac attribute_controller
        -_bc bim_controller
        +__init__()
        +get_element_cadwork_guid(int) str
        +get_name(int) str
        +is_wall(int) bool
        +get_p1(int) point_3d
        ... all protocol methods
    }

    class MockCadAdapter {
        -_elements Dict~int, dict~
        -_guids_to_ids Dict~str, int~
        -_grouping_type int
        -_all_element_ids list~int~
        -_active_element_ids list~int~
        +__init__()
        +add_element(int, str, ...) None
        +set_active_elements(list) None
        +get_element_cadwork_guid(int) str
        +get_name(int) str
        +is_wall(int) bool
        ... all protocol methods
    }

    class ModelElementTreeBuilder {
        -_all_ids list~int~
        -_adapter ICadAdapter
        +__init__(Iterable~int~, ICadAdapter)
        +build() list~IModelElement~
        -_classify(Iterable~int~) Tuple
        -_grouping_by(int) str
        -_group_children(Iterable~int~) Dict
        -_create_typed_parent(int, list) IModelElement
        -_create_leaf_element(int) ModelLeafElement
        -_create_element_geometry(int) ModelElementGeometry
        -_empty_geometry() ModelElementGeometry
        -_collect_orphans(Dict, set) set~int~
    }

    class ModelElementFactory {
        -_adapter ICadAdapter
        +__init__(ICadAdapter)
        +create(int) IModelElement
    }

    class IModelElement {
        <<Interface>>
        +guid Guid
        +name str
        +geometry ModelElementGeometry
        +accept(visitor) None
    }

    class ModelLeafElement {
        +guid Guid
        +name str
        +geometry ModelElementGeometry
        +accept(visitor) None
    }

    class Wall {
        +guid Guid
        +name str
        +geometry ModelElementGeometry
        +children list~IModelElement~
        +accept(visitor) None
    }

    ICadAdapter <|.. CadworkAdapter: implements
    ICadAdapter <|.. MockCadAdapter: implements
    ModelElementTreeBuilder o-- ICadAdapter: uses
    ModelElementFactory o-- ICadAdapter: uses
    ModelElementTreeBuilder ..> IModelElement: creates
    ModelElementFactory ..> IModelElement: creates
    IModelElement <|-- ModelLeafElement: extends
    IModelElement <|-- Wall: extends
```

---

## Sequence Diagrams

### Production Flow

```mermaid
sequenceDiagram
    participant User as User Code
    participant Builder as ModelElementTreeBuilder
    participant Adapter as CadworkAdapter
    participant EC as element_controller
    participant AC as attribute_controller
    participant CAD as CAD Instance
    User ->>+ Adapter: __init__()
    Note over Adapter: Import CAD controllers
    Adapter -->>- User: adapter instance
    User ->>+ Builder: __init__(element_ids, adapter)
    Builder ->> Adapter: set_attribute_display_settings_for_2d()
    Adapter ->> AC: set_attribute_display_settings_for_2d()
    AC ->> CAD: configure settings
    Builder -->>- User: builder instance
    User ->>+ Builder: build()

    loop For each element
        Builder ->>+ Adapter: is_wall(element_id)
        Adapter ->> AC: is_wall(element_id)
        AC ->> CAD: query element type
        CAD -->> AC: element data
        AC -->> Adapter: true/false
        Adapter -->>- Builder: true/false
        Builder ->>+ Adapter: get_name(element_id)
        Adapter ->> AC: get_name(element_id)
        AC ->> CAD: query element name
        CAD -->> AC: name
        AC -->> Adapter: "Wall-1"
        Adapter -->>- Builder: "Wall-1"
        Builder ->>+ Adapter: get_element_cadwork_guid(element_id)
        Adapter ->> EC: get_element_cadwork_guid(element_id)
        EC ->> CAD: query GUID
        CAD -->> EC: GUID
        EC -->> Adapter: "{GUID-001}"
        Adapter -->>- Builder: "{GUID-001}"
    end

    Note over Builder: Construct model tree
    Builder -->>- User: list[IModelElement]
```

### Test Flow

```mermaid
sequenceDiagram
    participant Test as Test Code
    participant Mock as MockCadAdapter
    participant Builder as ModelElementTreeBuilder
    participant Memory as In-Memory Data
    Test ->>+ Mock: __init__()
    Mock ->> Memory: Initialize empty dicts
    Mock -->>- Test: mock instance
    Test ->>+ Mock: add_element(1, "Wall", is_wall=True)
    Mock ->> Memory: Store element data
    Memory -->> Mock: OK
    Mock -->>- Test: None
    Test ->>+ Mock: add_element(2, "Beam")
    Mock ->> Memory: Store element data
    Memory -->> Mock: OK
    Mock -->>- Test: None
    Test ->>+ Builder: __init__([1, 2], mock)
    Builder ->> Mock: set_attribute_display_settings_for_2d()
    Note over Mock: No-op for testing
    Builder -->>- Test: builder instance
    Test ->>+ Builder: build()

    loop For each element
        Builder ->>+ Mock: is_wall(1)
        Mock ->> Memory: Check element data
        Memory -->> Mock: is_wall=True
        Mock -->>- Builder: True
        Builder ->>+ Mock: get_name(1)
        Mock ->> Memory: Get element name
        Memory -->> Mock: "Wall"
        Mock -->>- Builder: "Wall"
        Builder ->>+ Mock: get_element_cadwork_guid(1)
        Mock ->> Memory: Get GUID
        Memory -->> Mock: "{GUID-0001}"
        Mock -->>- Builder: "{GUID-0001}"
    end

    Note over Builder: Construct model tree
    Builder -->>- Test: list[IModelElement]
    Test ->> Test: Assert expectations
```

### Tree Building Flow

```mermaid
sequenceDiagram
    participant Client as Client Code
    participant Builder as ModelElementTreeBuilder
    participant Adapter as ICadAdapter
    participant Factory as Internal Methods
    Client ->>+ Builder: build()
    Builder ->> Builder: _classify(all_ids)
    Note over Builder: Separate parents<br/>from leaves

    loop For each element
        Builder ->> Adapter: is_wall(id)
        Adapter -->> Builder: bool
        Builder ->> Adapter: is_floor(id)
        Adapter -->> Builder: bool
        Builder ->> Adapter: is_roof(id)
        Adapter -->> Builder: bool
    end

    Builder ->> Builder: _group_children(leaves)

    loop For each leaf
        Builder ->> Adapter: get_subgroup(id)
        Adapter -->> Builder: group_name
    end

    Note over Builder: Group by subgroup/group

    loop For each parent
        Builder ->> Builder: _create_typed_parent(parent_id, children)
        Builder ->> Adapter: get_element_cadwork_guid(id)
        Adapter -->> Builder: GUID
        Builder ->> Adapter: get_name(id)
        Adapter -->> Builder: name
        Builder ->> Factory: _create_element_geometry(id)
        Factory ->> Adapter: get_p1(id)
        Adapter -->> Factory: Point
        Factory ->> Adapter: get_xl(id)
        Adapter -->> Factory: Vector
        Factory ->> Adapter: get_yl(id)
        Adapter -->> Factory: Vector
        Factory ->> Adapter: get_zl(id)
        Adapter -->> Factory: Vector
        Factory -->> Builder: ModelElementGeometry
        Builder ->> Adapter: is_wall(id)
        Adapter -->> Builder: true
        Note over Builder: Create Wall instance

        loop For each child
            Builder ->> Builder: _create_leaf_element(child_id)
        end
    end

    Builder ->> Builder: _collect_orphans()
    Note over Builder: Handle elements<br/>without parents
    Builder -->>- Client: list[IModelElement]
```

---

## Dependency Graph

```mermaid
graph TD
    subgraph Legend
        L1[Production Dependency]
        L2[Test Dependency]
        L3[Protocol/Interface]
        style L1 stroke: #28a745, stroke-width: 2px
        style L2 stroke: #ffc107, stroke-width: 2px, stroke-dasharray: 5 5
        style L3 stroke: #0066cc, stroke-width: 3px
    end

    subgraph Core
        ICadAdapter[ICadAdapter<br/>Protocol]
        CadAdapter[CadworkAdapter]
        MockAdapter[MockCadAdapter]
    end

    subgraph Services
        TreeBuilder[ModelElementTreeBuilder]
        Factory[ModelElementFactory]
        AssignmentSvc[StoreyAssignmentService]
    end

    subgraph CAD_API
        EC[element_controller]
        GC[geometry_controller]
        AC[attribute_controller]
        BC[bim_controller]
    end

    subgraph Tests
        UnitTests[test_with_mock_adapter]
        IntegrationTests[integration_tests]
    end

    TreeBuilder -->|depends on| ICadAdapter
    Factory -->|depends on| ICadAdapter
    AssignmentSvc -->|depends on| ICadAdapter
    CadAdapter -->|implements| ICadAdapter
    MockAdapter -->|implements| ICadAdapter
    CadAdapter -->|imports| EC
    CadAdapter -->|imports| GC
    CadAdapter -->|imports| AC
    CadAdapter -->|imports| BC
    UnitTests -.->|uses| MockAdapter
    UnitTests -.->|tests| TreeBuilder
    UnitTests -.->|tests| Factory
    IntegrationTests -->|uses| CadAdapter
    IntegrationTests -->|tests| TreeBuilder
    style ICadAdapter fill: #e1f5ff, stroke: #0066cc, stroke-width: 3px
    style CadAdapter fill: #d4edda, stroke: #28a745, stroke-width: 2px
    style MockAdapter fill: #fff3cd, stroke: #ffc107, stroke-width: 2px
```

---

## Testing Architecture

```mermaid
graph TB
    subgraph TestLayer["Test Layer"]
        UnitTests[Unit Tests<br/>No CAD Required]
        IntegrationTests[Integration Tests<br/>CAD Required]
        E2ETests[E2E Tests<br/>Full System]
    end

    subgraph TestDoubles["Test Doubles"]
        Mock[MockCadAdapter<br/>In-Memory Data]
        Stub[Stub Services]
        Spy[Test Spies]
    end

    subgraph SUT["System Under Test"]
        Services[Services & Builders]
        Models[Domain Models]
    end

    subgraph Production["Production Code"]
        ProdAdapter[CadworkAdapter]
        CAD[CAD System]
    end

    UnitTests -->|uses| Mock
    UnitTests -->|tests| Services
    Mock -->|provides data| Services
    Services -->|operates on| Models
    IntegrationTests -->|uses| ProdAdapter
    IntegrationTests -->|tests| Services
    ProdAdapter -->|calls| CAD
    E2ETests -->|exercises| ProdAdapter
    E2ETests -->|validates| CAD
    style Mock fill: #fff3cd, stroke: #ffc107, stroke-width: 2px
    style ProdAdapter fill: #d4edda, stroke: #28a745, stroke-width: 2px
    style UnitTests fill: #cfe2ff, stroke: #0056b3
    style IntegrationTests fill: #d1e7dd, stroke: #0a3622
```

---

## Data Flow Diagram

```mermaid
graph LR
    subgraph Input["Data Input"]
        User[User Selection]
        CADData[CAD Database]
    end

    subgraph Processing["Data Processing"]
        GetIDs[Get Element IDs]
        Adapter[ICadAdapter]
        Extract[Extract Attributes]
        Classify[Classify Elements]
        Group[Group by Hierarchy]
        Build[Build Tree Structure]
    end

    subgraph Output["Data Output"]
        Tree[Model Element Tree]
        Assignment[Storey Assignment]
        Report[Assignment Report]
    end

    User -->|Selects Elements| GetIDs
    GetIDs -->|Element IDs| Adapter
    Adapter -->|Query| CADData
    CADData -->|Element Data| Adapter
    Adapter -->|Attributes| Extract
    Extract -->|Name, Type, GUID| Classify
    Classify -->|Parents & Leaves| Group
    Group -->|Grouped Elements| Build
    Build -->|Hierarchical Structure| Tree
    Tree -->|Input for| Assignment
    Assignment -->|Results| Report
    style Adapter fill: #e1f5ff, stroke: #0066cc, stroke-width: 2px
    style CADData fill: #f8d7da, stroke: #842029
    style Tree fill: #d1e7dd, stroke: #0a3622
```
