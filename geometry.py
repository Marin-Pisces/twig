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
    bind_graph = models.Graph()
    bind_graph.nodes = graph.nodes.copy()
    bind_graph.edges = graph.edges.copy()
    bind_graph.variables = graph.variables.copy()
    bind_graph.drawing_order = graph.drawing_order[:]
    bind_graph.bind_count = graph.bind_count

    for nid in bind_nodes:
        if nid in bind_graph.nodes:
            original = bind_graph.nodes[nid]
            cloned = models.Node()
            cloned.node_id = original.node_id
            cloned.x, cloned.y = original.x, original.y
            cloned.parent_nodes = original.parent_nodes[:]
            cloned.child_nodes = original.child_nodes[:]
            bind_graph.nodes[nid] = cloned
    bind_graph = sync_variable_counts(bind_graph, bind_nodes, bind_label)
    root_id = graph.drawing_order[0][0]
    root = bind_graph.nodes.get(root_id)
    bind_graph.drawing_order, most_level_nodes = generate_drawing_order(bind_graph, root)
    return bind_graph

def sync_variable_counts(graph, bind_nodes, bind_label):
    top_node, bottom_nodes = find_topmost_node(graph, bind_nodes)
    abstracted_nodes = find_connected_nodes(graph, top_node, bottom_nodes)
    bind_graph = bind_as_variable(graph, bind_nodes, bind_label, abstracted_nodes, top_node, bottom_nodes)
    return bind_graph

def assign_levels(graph, root):
    adj = {}
    for edge in graph.edges.values():
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
    return None, None

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

def bind_as_variable(graph, bind_nodes, bind_label, abstracted_nodes, top_node_id, bottom_node_ids):
    top_node = graph.nodes.get(top_node_id)
    bottom_nodes = [graph.nodes.get(nid) for nid in bottom_node_ids]
    target_nodes = [top_node] + bottom_nodes

    b_x_coords = [n.x for n in bottom_nodes]

    min_x, max_x = min(b_x_coords), max(b_x_coords)
    width = max_x - min_x
    half_width = width / 2

    bind_node_x = min_x + half_width

    min_y = bottom_nodes[0].y
    max_y = top_node.y
    height = min_y - max_y

    bind_node_y = max_y + (height / 2)

    bind_node_id = max(graph.nodes.keys(), key=int, default=0) + 1

    bind_node = models.Node()
    bind_node.node_id = bind_node_id
    bind_node.label = bind_label
    bind_node.is_variable = True

    bind_node.x, bind_node.y = min_x + half_width, max_y + height / 2
    bind_node.width, bind_node.height, bind_node.half_width = width, height, half_width

    bind_node.parent_nodes = [top_node]
    bind_node.child_nodes = bottom_nodes
    top_node.child_nodes = [bind_node]
    for bn in bottom_nodes:
        bn.parent_nodes = [bind_node]

    abs_set = set(abstracted_nodes)

    for nid in abs_set:
        graph.nodes.pop(nid, None)
    graph.nodes[bind_node_id] = bind_node

    current_max_edge_id = max((e.edge_id for e in graph.edges.values()), default=0)

    graph.edges = {
        eid: e for eid, e in graph.edges.items()
        if e.source.node_id not in abs_set and e.target.node_id not in abs_set
    }


    for i, target in enumerate(target_nodes):
        new_edge = models.Edge()
        new_edge.edge_id = current_max_edge_id + 1 + i
        new_edge.label = bind_label
        new_edge.source = bind_node
        new_edge.target = target
        graph.edges[new_edge.edge_id] = new_edge

    new_var_id = max((v.variable_node_id for v in graph.variables.values()), default=0) + 1
    variable = models.Variable()
    variable.variable_node_id = new_var_id
    variable.abstracted_nodes = target_nodes[:]
    graph.variables[new_var_id] = variable

    graph.bind_count += 1
    return graph