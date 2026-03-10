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
    source: Node = field(repr=False)
    target: Node = field(repr=False)

    def __repr__(self):
        return (f"Edge(id={self.edge_id}, label='{self.label}', source={self.source.node_id}, target={self.target.node_id})")

@dataclass
class Variable:
    variable_node_id: int = 0
    abstracted_nodes: list[Node] = field(default_factory=list, repr=False)

    def __repr__(self):
        abstracted_ids = [a.node_id for a in self.abstracted_nodes]
        return (f"Variable(id={self.variable_node_id}, abstracteds={abstracted_ids})")

@dataclass
class RawGraph:
    nodes: Dict[int, Node] = field(default_factory=dict, repr=False)
    edges: list[Edge] = field(default_factory=list, repr=False)
    variables: list[Variable] = field(default_factory=list, repr=False)
    drawing_order: list[int]  = field(default_factory=list)
    bind_count: int = 0

    def __repr__(self):
        return (f"RawGraph(nodes count={len(self.nodes)}, edges count={len(self.edges)}, variables count={len(self.variables)}, binds={self.bind_count})")

@dataclass
class Binding:
    display_label: str=""
    nodes: Dict[int, Node] = field(default_factory=dict, repr=False)
    edges: list[Edge] = field(default_factory=list, repr=False)
    variables: list[Variable]    = field(default_factory=list, repr=False)
    abstracted_nodes: list[Node] = field(default_factory=list, repr=False)
    drawing_order: list[int]     = field(default_factory=list)
    bind_count: int = 0

    def __repr__(self):
        return (f"Binding(nodes count={len(self.nodes)}, edges count={len(self.edges)}, variables count={len(self.variables)}, abstracteds count={len(self.abstracted_nodes)}, binds={self.bind_count})")
