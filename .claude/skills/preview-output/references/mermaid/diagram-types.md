# Mermaid.js Diagram Types

A full syntax reference for the 24+ diagram types Mermaid.js v11 supports.

## Core Diagrams

### Flowchart
For process flows, decision trees, and workflows.

**Syntax:**
```
flowchart {direction}
  {nodeId}[{label}] {arrow} {nodeId}[{label}]
```

**Directions:** TB/TD (top-bottom), BT, LR (left-right), RL
**Shapes:** `()` round, `[]` rect, `{}` diamond, `{{}}` hexagon, `(())` circle
**Arrows:** `-->` solid, `-.->` dotted, `==>` thick
**Subgraphs:** Group related nodes

### Sequence Diagram
For actor interactions, API flows, and the order messages travel in.

**Syntax:**
```
sequenceDiagram
  participant A as Actor
  A->>B: Message
  activate B
  B-->>A: Response
  deactivate B
```

**Arrows:** `->` solid, `->>` arrow, `-->` dotted, `-x` cross, `-)` async
**Also supports:** loops, alternatives, parallel paths, optional blocks, critical regions

### Class Diagram
For object structures, inheritance, and how classes relate.

**Syntax:**
```
classDiagram
  class Animal {
    +String name
    -int age
    +void eat()
  }
  Animal <|-- Dog : inherits
```

**Visibility:** `+` public, `-` private, `#` protected, `~` package
**Relationships:** `<|--` inheritance, `*--` composition, `o--` aggregation, `-->` association

### State Diagram
For state machines, transitions, and workflows.

**Syntax:**
```
stateDiagram-v2
  [*] --> State1
  State1 --> State2 : transition
  State2 --> [*]
```

**Also supports:** composite states, choice points, forks and joins, concurrency

### ER Diagram
For database relationships and schemas.

**Syntax:**
```
erDiagram
  CUSTOMER ||--o{ ORDER : places
  ORDER ||--|{ LINE_ITEM : contains
```

**Cardinality:** `||` one, `|o` zero-one, `}|` one-many, `}o` zero-many

## Planning Diagrams

### Gantt Chart
For project timelines and schedules.

**Syntax:**
```
gantt
  title Project
  dateFormat YYYY-MM-DD
  section Phase1
    Task1 :done, 2024-01-01, 5d
    Task2 :active, after Task1, 3d
```

**Status:** `done`, `active`, `crit`, `milestone`

### User Journey
For experience flows and tracking how each step feels.

**Syntax:**
```
journey
  title User Journey
  section Shopping
    Browse: 5: Customer
    Add to cart: 3: Customer, System
```

**Scores:** 1-5 satisfaction levels

### Kanban
For task boards and workflow stages.

**Syntax:**
```
kanban
  Todo[Task Board]
    task1[Implement API]
    @{ assigned: "Dev1", priority: "High" }
  InProgress[In Progress]
    task2[Fix bug]
```

### Quadrant Chart
For prioritization and spotting trends.

**Syntax:**
```
quadrantChart
  x-axis Low --> High
  y-axis Low --> High
  Item A: [0.3, 0.6]
```

## Architecture Diagrams

### C4 Diagram
For system architecture and its components.

**Syntax:**
```
C4Context
  Person(user, "User")
  System(app, "Application")
  Rel(user, app, "Uses")
```

### Architecture Diagram
For cloud infrastructure and services.

**Syntax:**
```
architecture-beta
  service api(server)[API]
  service db(database)[Database]
  api:R --> L:db
```

**Icons:** cloud, database, disk, internet, server, or iconify.design icons

### Block Diagram
For module dependencies and networks.

**Syntax:**
```
block-beta
  columns 3
  a["Block A"] b["Block B"]
  a --> b
```

**Shapes:** rounded, stadium, cylinder, diamond, trapezoid, hexagon

## Data Visualization

### Pie Chart
For proportions and distributions.

**Syntax:**
```
pie showData
  "Category A" : 45.5
  "Category B" : 30.0
```

### XY Chart
For trends and comparisons.

**Syntax:**
```
xychart-beta
  x-axis [jan, feb, mar]
  y-axis "Sales" 0 --> 100
  line [30, 45, 60]
  bar [25, 40, 55]
```

### Sankey
For visualizing flow and how resources get allocated.

**Syntax:**
```
sankey-beta
  Source,Target,Value
  A,B,10
  B,C,5
```

### Radar Chart
For comparing across several dimensions at once.

**Syntax:**
```
radar-beta
  axis Skill1, Skill2, Skill3
  curve Team1{3,4,5}
  curve Team2{4,3,4}
```

### Treemap
For proportions within a hierarchy.

**Syntax:**
```
treemap-beta
  "Root"
    "Category A"
      "Item 1": 100
      "Item 2": 200
```

## Technical Diagrams

### Git Graph
For branching strategies and git workflows.

**Syntax:**
```
gitGraph
  commit
  branch develop
  checkout develop
  commit
  checkout main
  merge develop
```

### Timeline
For events and milestones laid out in order.

**Syntax:**
```
timeline
  2024 : Event A : Event B
  2025 : Event C
```

### Packet Diagram
For network protocols and packet structures.

**Syntax:**
```
packet-beta
  0-15: "Header"
  16-31: "Data"
```

### ZenUML Sequence
A different syntax for sequence diagrams.

**Syntax:**
```
zenuml
  A.method() {
    B.process()
    return result
  }
```

### Mindmap
For brainstorming and laying out hierarchies.

**Syntax:**
```
mindmap
  root((Central Idea))
    Branch 1
      Sub 1
      Sub 2
    Branch 2
```

### Requirement Diagram
For SysML requirements and tracing them.

**Syntax:**
```
requirementDiagram
  requirement req1 {
    id: R1
    text: User shall login
    risk: Medium
  }
```

## Quick Reference

| Type | Best For | Complexity |
|------|----------|------------|
| Flowchart | Processes | Low |
| Sequence | Interactions | Medium |
| Class | OOP | High |
| State | Behaviors | Medium |
| ER | Databases | Low |
| Gantt | Timelines | Medium |
| Architecture | Systems | High |
