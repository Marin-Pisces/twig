from collections import deque
from copy import deepcopy
import models

def compute_layout(graph, root_id = 0):
    if root_id in graph.nodes:
        root = graph.nodes[root_id]
    else:
        root = next(iter(graph.nodes.values()))
    assign_levels(graph, root)
    graph.drawing_order, most_level_nodes = generate_drawing_order(graph, root)
    calculate_positions(graph, most_level_nodes)

def build_hyper_edges(graph, bind_nodes, bind_label = 'bind'):
    root = graph.nodes.get(graph.drawing_order[0][0])
    bind_graph = models.Graph()
    bind_graph = deepcopy(graph)
    bind_graph = sync_variable_counts(bind_graph, bind_nodes, bind_label)
    bind_graph.drawing_order, most_level_nodes = generate_drawing_order(bind_graph, root)
    return bind_graph

def sync_variable_counts(graph, bind_nodes, bind_label):
    top_node, bottom_nodes = find_topmost_node(graph, bind_nodes)
    abstracted_nodes = find_connected_nodes(graph, top_node, bottom_nodes)
    bind_graph = test(graph, bind_nodes, bind_label, abstracted_nodes, top_node, bottom_nodes)
    return bind_graph

def assign_levels(graph, root):
    adj = {}
    for edge in graph.edges:
        s, t = edge.source.node_id, edge.target.node_id
        adj.setdefault(s, set()).add(t)
        adj.setdefault(t, set()).add(s)

    queue = deque([root])

    visited = {root.node_id}

    while queue:
        current_node = queue.popleft()
        current_id = current_node.node_id

        neighbor_ids = sorted(adj.get(current_id, set()))

        child_ids = set()
        for to_id in neighbor_ids:
            if to_id not in visited:
                visited.add(to_id)
                child_ids.add(to_id)

                child_node = graph.nodes.get(to_id)

                if child_node:
                    if current_node not in child_node.parent_nodes:
                        child_node.parent_nodes.append(current_node)
                    if child_node not in current_node.child_nodes:
                        current_node.child_nodes.append(child_node)

                    queue.append(child_node)

def generate_drawing_order(graph, root):
    top_down_order = []
    most_level_nodes = 0
    current_level_nodes = [root]

    while current_level_nodes:
        level_size = len(current_level_nodes)
        if level_size > most_level_nodes:
            most_level_nodes = level_size

        current_level_ids = []
        next_level_nodes = []

        for target in current_level_nodes:
            current_level_ids.append(target.node_id)
            next_level_nodes.extend(target.child_nodes)

        top_down_order.append(current_level_ids)
        current_level_nodes = next_level_nodes
    return top_down_order, most_level_nodes

def calculate_positions(graph, most_level_nodes):
    node_w = 100
    node_h = 100

    canvas_width = most_level_nodes * node_w

    if not graph.drawing_order:
        return

    root_level = graph.drawing_order[0]

    for i, root_id in enumerate(root_level):
        root = graph.nodes.get(root_id)
        root.width = canvas_width / len(root_level)
        root.half_width = root.width / 2
        root.x = (root.width * i) + root.half_width
        root.y = 0
        root.base_y = 0

    for level in graph.drawing_order:
        for node_id in level:
            node = graph.nodes.get(node_id)
            if not node or not node.child_nodes:
                continue
            num_children = len(node.child_nodes)
            child_w = node.width / num_children
            child_hw = child_w / 2

            start_x = node.x - node.half_width
            next_base_y = node.base_y - node_h

            for i, child in enumerate(node.child_nodes):
                child.width = child_w
                child.half_width = child_hw
                child.x = start_x + (child_w * i) + child_hw

                child.base_y = next_base_y
                child.y = next_base_y + (node_h / 2 if child.is_variable else 0)

def resolve_node(target_ids, node_dict):
    node_list = []
    for target_id in target_ids:
        node_list.append(node_dict.get(target_id))
    return node_list

def find_topmost_node(graph, bind_node_ids):
    targets = set(bind_node_ids)
    order = []
    for level in graph.drawing_order:
        for n in level:
            order.append(n)

    for level in graph.drawing_order:
        for node_id in level:
            if node_id in targets:
                targets.discard(node_id)
                bottom_list = sorted(targets, key=order.index)
                return node_id, bottom_list
    return None

def find_connected_nodes(graph, top_node, bottom_nodes):
    abstracted_nodes = set()
    for node_id in bottom_nodes:
        node = graph.nodes.get(node_id)
        parent_node = node.parent_nodes[0]
        not_top = True
        while not_top:
            if parent_node.node_id == top_node:
                not_top = False
                break
            abstracted_nodes.add(parent_node.node_id)
            parent_node = parent_node.parent_nodes[0]
    return abstracted_nodes

def test(graph, bind_nodes, bind_label, abstracted_nodes, top_node_id, bottom_node_ids):
    min_x = top_node.x
    max_x = top_node.x
    min_y = top_node.y
    max_y = top_node.y
    bottom_nodes = []
    for i, node_id in enumerate(bottom_node_ids):
        bottom_node = graph.nodes.get(node_id)
        bottom_nodes.append(bottom_node)
        if i == 0:
            min_x = bottom_node.x
        if max_x < bottom_node.x:
            max_x = bottom_node.x
        else:
            min_x = bottom_node.x
        if min_y > bottom_node.y:
            min_y = bottom_node.y
    width = max_x - min_x
    half_width = width/2
    height = min_y - max_y
    bind_node_id = max(graph.nodes, key=int, default=0) + 1
    bind_node = models.Node()
    bind_node.node_id = bind_node_id
    bind_node.label = bind_label
    bind_node.parent_nodes = [top_node]
    bind_node.child_nodes = bottom_nodes
    bind_node.x = min_x + half_width
    bind_node.y = max_y + height/2
    bind_node.width = width
    bind_node.height = height
    bind_node.half_width = half_width
    bind_node.is_variable = True

    graph.nodes[bind_node_id] = bind_node

    top_node.child_nodes = [bind_node]
    for node_id in bottom_node_ids:
        bottom_node = graph.nodes.get(node_id)
        bottom_node.parent_nodes = [bind_node]

    for abs in abstracted_nodes:
        del graph.nodes[abs]

    edge_ids = [e.edge_id for e in graph.edges]
    bind_edge_id = 0
    if edge_ids:
        bind_edge_id = max(edge_ids) + 1
    remaining_edges = []
    for edge in graph.edges:
        s, t = edge.source.node_id, edge.target.node_id
        if s not in abstracted_nodes and t not in abstracted_nodes:
            remaining_edges.append(edge)
    binds = [bottom_node for bottom_node in bottom_nodes]
    binds.append(top_node)
    for bind in binds:
        edge = models.Edge()
        edge.edge_id = bind_edge_id
        edge.label = bind_label
        edge.source = bind_node
        edge.target = bind
        bind_edge_id = bind_edge_id + 1
        remaining_edges.append(edge)
    graph.edges = remaining_edges

    variable = models.Variable()
    variable_ids = [v.variable_node_id for v in graph.variables]
    bind_variable_id = 0
    if variable_ids:
        bind_variable_id = max(variable_ids) + 1

    variable.variable_node_id = bind_variable_id
    for bind in binds:
        variable.abstracted_nodes.append(bind)
    graph.variables.append((variable))

    graph.bind_count = graph.bind_count + 1

    return graph