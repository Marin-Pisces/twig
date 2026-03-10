from dataclasses import dataclass, field

@dataclass
class Node:
    node_id:     int = 0
    label:       str = ""
    parent_nodes: list["Node"] = field(default_factory=list, repr=False)
    child_nodes:  list["Node"] = field(default_factory=list, repr=False)
    x: float = 0.0
    y: float = 0.0
    width:  float = 0.0
    height: float = 0.0
    half_width: float = 0.0
    is_variable: bool = False

    def __repr__(self):
        parent_ids = [p.node_id for p in self.parent_nodes]
        child_ids  = [c.node_id for c in self.child_nodes]

        return (f"Node(id={self.node_id}, label='{self.label}', parents={parent_ids}, children={child_ids}, node position=({self.x:.2f},{self.y:.2f})), is variable={self.is_variable}")

@dataclass
class Edge:
    edge_id: int = 0
    label  : str = ""
    source: "Node | None" = field(default=None, repr=False)
    target: "Node | None" = field(default=None, repr=False)

    def __repr__(self):
        source_id = self.source.node_id if self.source else "None"
        target_id = self.target.node_id if self.target else "None"
        return (f"Edge(id={self.edge_id}, label='{self.label}', source={self.source_id}, target={self.target_id})")

@dataclass
class Variable:
    variable_node_id: int = 0
    abstracted_nodes: list[Node] = field(default_factory=list, repr=False)

    def __repr__(self):
        abstracted_ids = [a.node_id for a in self.abstracted_nodes]
        return (f"Variable(id={self.variable_node_id}, abstracteds={abstracted_ids})")

@dataclass
class RawGraph:
    nodes: dict[int, Node ] = field(default_factory=dict, repr=False)
    edges: list[Edge] = field(default_factory=list, repr=False)
    variables: list[Variable] = field(default_factory=list, repr=False)
    drawing_order: list[int]  = field(default_factory=list)
    bind_count: int = 0

    def __repr__(self):
        return (f"RawGraph(nodes count={len(self.nodes)}, edges count={len(self.edges)}, variables count={len(self.variables)}, binds={self.bind_count})")

@dataclass
class Binding:
    display_label: str=""
    nodes: dict[int, Node] = field(default_factory=dict, repr=False)
    edges: list[Edge] = field(default_factory=list, repr=False)
    variables: list[Variable]    = field(default_factory=list, repr=False)
    abstracted_nodes: list[Node] = field(default_factory=list, repr=False)
    drawing_order: list[int]     = field(default_factory=list)
    bind_count: int = 0

    def __repr__(self):
        return (f"Binding(nodes count={len(self.nodes)}, edges count={len(self.edges)}, variables count={len(self.variables)}, abstracteds count={len(self.abstracted_nodes)}, binds={self.bind_count})")
