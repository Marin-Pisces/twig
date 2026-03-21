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
    bind_graph= graph.clone()

    for nid in bind_nodes:
        if nid in bind_graph.nodes:
            bind_graph.nodes[nid] = bind_graph.nodes[nid].clone()

    bind_graph = sync_variable_counts(bind_graph, bind_nodes, bind_label)
    root_id = graph.drawing_order[0][0]
    root = bind_graph.nodes.get(root_id)
    bind_graph.drawing_order, most_level_nodes = generate_drawing_order(bind_graph, root)
    return bind_graph

def substitute_variable(graph, bind_graph, bind_map, bind_label = ''):
    substitute_graph= graph.clone()
    bind_clone = bind_graph.clone()

    around = get_around_nodes(graph, bind_map)

    for nid in around:
        if nid in bind_graph.nodes:
            substitute_graph.nodes[nid] = graph.nodes[nid].clone()
    align_subgraph_geometry(substitute_graph, bind_clone, bind_map, bind_label, around)
    root_id = graph.drawing_order[0][0]
    root = bind_graph.nodes.get(root_id)
    substitute_graph.drawing_order, most_level_nodes = generate_drawing_order(substitute_graph, root)
    return substitute_graph

def sync_variable_counts(graph, bind_nodes, bind_label):
    top_node, bottom_nodes = find_topmost_node(graph, bind_nodes)
    abstracted_nodes = find_connected_nodes(graph, top_node, bottom_nodes)
    bind_graph = bind_as_variable(graph, bind_nodes, bind_label, abstracted_nodes, top_node, bottom_nodes)
    return bind_graph

def align_subgraph_geometry(substitute, bind, bind_map, bind_label, around):
    node_offset = max(substitute.nodes.keys()) + 1
    edge_offset = max(substitute.edges.keys()) + 1
    set_new_ids(bind, node_offset, edge_offset)
    new_bind_map = {iid: i + node_offset for iid, i in bind_map.items()}
    bind_nodes = [n for n in bind_map.keys()]
    top_node, bottom_nodes = find_topmost_node(substitute, bind_nodes)
    target_variable_node_id = substitute.nodes[bottom_nodes[0]].parent_nodes[0].node_id
    assign_levels(bind, bind.nodes[new_bind_map[top_node]])
    bind.drawing_order, most_level_nodes = generate_drawing_order(bind, bind.nodes[new_bind_map[top_node]])
    expand_variable(substitute, bind, bind_label, new_bind_map, top_node, bottom_nodes, target_variable_node_id, around)

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
    top_node.child_nodes = [
        child for child in top_node.child_nodes
        if child.node_id not in abstracted_nodes
    ]
    top_node.child_nodes.append(bind_node)
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

def get_around_nodes(graph, mapping):
    around_ids = set()
    target_ids = set(mapping.keys())

    for mid in target_ids:
        t_node = graph.nodes[mid]

        around_ids.update(p.node_id for p in t_node.parent_nodes)
        around_ids.update(c.node_id for c in t_node.child_nodes)

    return around_ids

def set_new_ids(bind, node_offset, edge_offset):
    node_id_map = {old_id: old_id + node_offset for old_id in bind.nodes.keys()}
    new_nodes = {}
    count = 0
    for old_id, node in bind.nodes.items():
        new_id = old_id + node_offset
        node.node_id = new_id
        new_nodes[new_id] = node
        if count < new_id:
            count = new_id

    bind.nodes = new_nodes

    new_edges = {}
    for old_eid, edge in list(bind.edges.items()):
        new_eid = old_eid + edge_offset
        edge.edge_id = new_eid
        new_edges[new_eid] = edge
    bind.edges = new_edges

    new_variables = {}
    for old_vid, variable in list(bind.variables.items()):
        new_vid = count + 1
        variable.variable_node_id = new_vid
        new_variables[new_vid] = variable
        count += 1
    bind.variables = new_variables

def expand_variable(graph, bind, bind_label, bind_map, top_node_id, bottom_node_ids, target_variable_node_id, around):
    old_top_node = graph.nodes.get(top_node_id)
    old_bottom_nodes = [graph.nodes.get(nid) for nid in bottom_node_ids]
    target_variable_node = graph.nodes.get(target_variable_node_id)
    around_nodes = [graph.nodes.get(nid) for nid in around]
    top_node = bind.nodes.get(bind_map[top_node_id])
    bottom_nodes = [bind.nodes.get(bind_map[nid]) for nid in bottom_node_ids]
    old_target = [old_top_node] + [target_variable_node] + old_bottom_nodes
    target_nodes = [top_node] + bottom_nodes
    target_node_id = [top_node_id] + bottom_node_ids

    new_nodes = {node.node_id: node for node in graph.nodes.values() if node not in old_target}
    new_edges = {}
    new_variables = {}

    for (old, new) in bind_map.items():
        old_node = graph.nodes.pop(old)
        new_node = bind.nodes.pop(new)
        if old == top_node_id:
            new_node.parent_nodes = old_node.parent_nodes
            new_list = [node for node in old_node.child_nodes if node.node_id != target_variable_node_id]
            new_node.child_nodes.extend(new_list)
        else:
            new_node.child_nodes = new_node.child_nodes
        new_node.x, new_node.y = old_node.x, old_node.y
        new_node.width, new_node.height = old_node.width, old_node.height
        new_node.half_width = old_node.half_width
        new_nodes[new_node.node_id] = new_node

    b_hw_coords = [n.half_width for n in bottom_nodes]
    b_x_coords = [n.x for n in bottom_nodes]
    half = min(b_hw_coords)
    min_x, max_x = min(b_x_coords) - half, max(b_x_coords) + half
    max_width = max_x - min_x
    half_max_width = max_width / 2

    min_y = bottom_nodes[0].y
    max_y = top_node.y
    max_height = min_y - max_y

    drawing_order = bind.drawing_order[1:-1]

    whidh = max_width
    heidht = max_height / (len(drawing_order) + 1)
    for i, level in enumerate(drawing_order):
        for j, node_id in enumerate(level):
            node = bind.nodes.get(node_id)
            w = whidh / len(level)
            node.x = top_node.x + (w * (j + 1))
            node.width = w
            node.half_width = w / 2
            print(i)
            node.y = top_node.y + (heidht * (i + 1)) + (heidht / 2 if node.is_variable else 0)
            width = w
            new_nodes[node.node_id] = node
    for node in around_nodes:
        if node in new_nodes.values():
            np = []
            nc = []
            for p in node.parent_nodes:
                if p.node_id in target_node_id:
                    p = new_nodes[bind_map[p.node_id]]
                np.append(p)
            node.parent_nodes = np
            for c in node.child_nodes:
                if c.node_id in target_node_id:
                    c = new_nodes[bind_map[c.node_id]]
                nc.append(c)
            node.child_nodes = nc
            new_nodes[node.node_id] = node
    for edge in graph.edges.values():
        if edge.source.node_id != target_variable_node_id and edge.target.node_id != target_variable_node_id:
            if edge.source.node_id in target_node_id:
                edge.source = new_nodes[bind_map[edge.source.node_id]]
            if edge.target.node_id in target_node_id:
                edge.target = new_nodes[bind_map[edge.target.node_id]]
            new_edges[edge.edge_id] = edge
    new_edges.update(bind.edges)
    is_bind = False
    for variable in graph.variables.values():
        for va in variable.abstracted_nodes:
            if va.node_id in target_node_id:
                is_bind = True
            else:
                is_bind = False
        if not is_bind:
            new_variables[variable.variable_node_id] = variable

    graph.nodes = new_nodes
    graph.edges = new_edges
    graph.variables = new_variables
    graph.bind_count -= 1
