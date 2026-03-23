from collections import deque
from copy import deepcopy
import models

def compute_layout(graph, root_id = 0):
    # check (Root and nodes are empty)
    if not hasattr(graph, 'nodes') or not graph.nodes:
        print("Warning: グラフにノードがないため、レイアウト計算をスキップします。")
        return

    # Identifying the root node
    if root_id in graph.nodes:
        root = graph.nodes[root_id]
    else:
        root = next(iter(graph.nodes.values()))

    assign_levels(graph, root)
    order, most_level_nodes = generate_drawing_order(graph, root)
    graph.drawing_order = order
    calculate_positions(graph, most_level_nodes)

def build_hyper_edges(graph, bind_nodes, bind_label = 'bind'):
    # check (The original graph is empty)
    if not graph or not hasattr(graph, 'nodes') or not graph.nodes:
        return graph

    # Cloning a graph and a specific node
    bind_graph = graph.clone()
    for nid in bind_nodes:
        if nid in bind_graph.nodes:
            bind_graph.nodes[nid] = bind_graph.nodes[nid].clone()

    bind_graph = sync_variable_counts(bind_graph, bind_nodes, bind_label)

    # Check if `drawing_order` exists and has content
    if hasattr(graph, 'drawing_order') and graph.drawing_order and graph.drawing_order[0]:
        root_id = graph.drawing_order[0][0]
        root = bind_graph.nodes.get(root_id)

    # Backup in case it is not found in drawing_order
    if root is None:
        root = next(iter(bind_graph.nodes.values()), None)
    if root:
        order, most_nodes = generate_drawing_order(bind_graph, root)
        bind_graph.drawing_order = order

    return bind_graph

def substitute_variable(graph, bind_graph, bind_map):
    substitute_graph= graph.clone()
    bind_clone = bind_graph.clone()

    around = get_around_nodes(graph, bind_map)

    for nid in around:
        if nid in bind_graph.nodes:
            substitute_graph.nodes[nid] = graph.nodes[nid].clone()
    align_subgraph_geometry(substitute_graph, bind_clone, bind_map, around)

    """# Check if `drawing_order` exists and has content
    if hasattr(graph, 'drawing_order') and graph.drawing_order and graph.drawing_order[0]:
        root_id = graph.drawing_order[0][0]
        root = substitute_graph.nodes.get(root_id)

    # Backup in case it is not found in drawing_order
    if root is None:
        root = next(iter(substitute_graph.nodes.values()), None)
    if root:
        order, most_nodes = generate_drawing_order(substitute_graph, root)
        substitute_graph.drawing_order = order"""
    return substitute_graph

def sync_variable_counts(graph, bind_nodes, bind_label):
    top_node, bottom_nodes = find_topmost_node(graph, bind_nodes)
    abstracted_nodes = find_connected_nodes(graph, top_node, bottom_nodes)
    bind_graph = bind_as_variable(graph, bind_nodes, bind_label, abstracted_nodes, top_node, bottom_nodes)
    return bind_graph

def align_subgraph_geometry(main_graph, sub_graph, bind_map, around):
    # ID preparation
    new_bind_map = prepare_subgraph_ids(main_graph, sub_graph, bind_map)

    # Identifying connection points
    insertion_info = find_insertion_point(main_graph, bind_map)
    if not insertion_info:
        return

    top_id = insertion_info['top_id']
    bottom_ids = insertion_info['bottom_ids']
    target_var_id = insertion_info['target_var_id']

    # Organize the layout of the graph to be inserted.
    refresh_subgraph_layout(sub_graph, new_bind_map, top_id)

    new_top_id = new_bind_map[top_id]
    compute_layout(sub_graph, new_top_id)
    print(new_bind_map)
    expand_variable(
        main_graph, sub_graph, new_bind_map,
        top_id,
        bottom_ids,
        target_var_id,
        around
    )

def assign_levels(graph, root):
    # check (Root and nodes are empty)
    if not root or not hasattr(graph, 'nodes') or not graph.nodes:
        return

    # clean up (Node parent and child)
    for node in graph.nodes.values():
        node.parent_nodes = []
        node.child_nodes = []

    # Building an adjacency list
    adj = {}
    for edge in graph.edges.values():
        # check (Not None, exists in nodes)
        if not edge.source or not edge.target:
            continue
        s, t = edge.source.node_id, edge.target.node_id
        # check (IDs that do not exist in the graph)
        if s not in graph.nodes or t not in graph.nodes:
            continue
        adj.setdefault(s, set()).add(t)
        adj.setdefault(t, set()).add(s)

    # Search using BFS
    queue = deque([root])
    visited = {root.node_id}
    while queue:
        current_node = queue.popleft()
        current_id = current_node.node_id
        neighbor_ids = sorted(adj.get(current_id, set()))
        for next_id in neighbor_ids:
            if next_id not in visited:
                visited.add(next_id)
                # check (The node entity does not exist in the dictionary)
                child_node = graph.nodes.get(next_id)
                if not child_node:
                    continue
                current_node.child_nodes.append(child_node)
                child_node.parent_nodes.append(current_node)
                queue.append(child_node)

def generate_drawing_order(graph, root):
    # check (No root access)
    if not root:
        return [], 0

    top_down_order = []
    most_level_nodes = 0
    current_level_nodes = [root]

    # guard (Infinite loop due to circular reference (loop))
    processed_ids = set()

    while current_level_nodes:
        # check (Number of nodes at this level)
        level_size = len(current_level_nodes)
        if level_size > most_level_nodes:
            most_level_nodes = level_size
        current_level_ids = []
        next_level_nodes = []
        for target in current_level_nodes:
            # Nodes that have already been processed will be skipped
            if target.node_id in processed_ids:
                continue
            current_level_ids.append(target.node_id)
            next_level_nodes.extend(target.child_nodes)
        # Do not create empty hierarchies
        if current_level_ids:
            top_down_order.append(current_level_ids)
        current_level_nodes = next_level_nodes

    return top_down_order, most_level_nodes

def calculate_positions(graph, most_level_nodes):
    # check (The drawing order and maximum number of nodes are unknown)
    if not graph.drawing_order or most_level_nodes <= 0:
        return

    node_w = 100
    node_h = 100
    canvas_width = most_level_nodes * node_w

    # Root hierarchy (top level)
    root_level = graph.drawing_order[0]
    num_roots = len(root_level)

    for i, root_id in enumerate(root_level):
        root = graph.nodes.get(root_id)
        if not root:
            continue
        # Divide the parent width by the number of square roots.
        root.width = canvas_width / num_roots
        root.half_width = root.width / 2
        # Calculate the center coordinates
        root.x = (root.width * i) + root.half_width
        root.y = 0
        root.base_y = 0
    # Placement from the second layer onwards
    for level in graph.drawing_order:
        for node_id in level:
            node = graph.nodes.get(node_id)

            # Skip if the parent node does not exist or has no children.
            if not node or not hasattr(node, 'child_nodes') or not node.child_nodes:
                continue
            num_children = len(node.child_nodes)
            # Prevent division by zero in the number of child nodes
            if num_children == 0:
                continue
            # The width a child can hold per item
            child_w = node.width / num_children
            child_hw = child_w / 2
            # Use the left edge of the parent as the reference point
            start_x = node.x - node.half_width
            next_base_y = node.base_y - node_h

            for i, child in enumerate(node.child_nodes):
                child.width = child_w
                child.half_width = child_hw
                # LaTeX
                # $$ x_{child} = x_{start} + (w_{child} \times i) + \frac{w_{child}}{2} $$
                child.x = start_x + (child_w * i) + child_hw

                child.base_y = next_base_y
                y_offset = (node_h / 2) if child.is_variable else 0
                child.y = next_base_y + y_offset

def find_topmost_node(graph, bind_node_ids):
    # check (The input is empty)
    if not hasattr(graph, 'drawing_order') or not graph.drawing_order or not bind_node_ids:
        return None, None

    targets = set(bind_node_ids)

    # Create a "rank" map for searching and sorting.
    flat_order = [node_id for level in graph.drawing_order for node_id in level]
    rank_map = {node_id: i for i, node_id in enumerate(flat_order)}

    # Focus only on effective targets
    valid_targets = [tid for tid in targets if tid in rank_map]
    if not valid_targets:
        return None, None

    # Sort by appearance order using the rank map.
    sorted_targets = sorted(valid_targets, key=lambda tid: rank_map[tid])

    # The first one is Top, the rest are Bottom.
    top_node_id = sorted_targets[0]
    bottom_list = sorted_targets[1:]

    return top_node_id, bottom_list

def find_connected_nodes(graph, top_node_id, bottom_node_ids):
    abstracted_nodes = set()

    for start_node_id in bottom_node_ids:
        current_node = graph.nodes.get(start_node_id)
        if not current_node:
            continue
        # As long as you have parents, you'll keep climbing higher and higher
        while current_node.parent_nodes:
            # Get the first parent
            parent = current_node.parent_nodes[0]
            # Once the destination is reached, the exploration of this branch is complete
            if parent.node_id == top_node_id:
                break
            # If you haven't reached your destination yet, record it as an intermediate node and continue climbing
            abstracted_nodes.add(parent.node_id)
            current_node = parent
    return abstracted_nodes

def bind_as_variable(graph, bind_nodes, bind_label, abstracted_nodes, top_node_id, bottom_node_ids):
    # check (the existence of a node)
    top_node = graph.nodes.get(top_node_id)
    bottom_nodes = [graph.nodes.get(nid) for nid in bottom_node_ids if nid in graph.nodes]

    if not top_node or not bottom_nodes:
        return graph

    # Calculation of coordinates and size
    b_x_coords = [n.x for n in bottom_nodes]
    min_x, max_x = min(b_x_coords), max(b_x_coords)
    width = max_x - min_x

    # hight = $$ | y_{bottom} - y_{top} | $$
    height = abs(bottom_nodes[0].y - top_node.y)
    if height == 0:
        height = 100

        for bn in bottom_nodes:
            print(bn)
            dy = (top_node.y - height) - bn.y
            shift_subtree(bn, dy)

    # Issuing a new variable node (Bind Node)
    new_node_id = max(graph.nodes.keys() or [0]) + 1

    bind_node = models.Node()
    bind_node.node_id = new_node_id
    bind_node.label = bind_label
    bind_node.is_variable = True
    # Set geometric information
    bind_node.x = min_x + (width / 2)
    bind_node.y = top_node.y - (height / 2)
    bind_node.width, bind_node.height = width, height
    bind_node.half_width = width / 2

    # Reconnecting parent-child relationships
    abs_set = set(abstracted_nodes)

    # Remove the intermediate node from the parent's child list and add a new node
    top_node.child_nodes = [n for n in top_node.child_nodes if n.node_id not in abs_set]
    top_node.child_nodes.append(bind_node)

    # Set the parent-child list for the new node
    bind_node.parent_nodes = [top_node]
    bind_node.child_nodes = bottom_nodes

    # Replace the child's parent with a new node
    for bn in bottom_nodes:
        bn.parent_nodes = [bind_node]

    # Updating graph data
    graph.nodes = {nid: n for nid, n in graph.nodes.items() if nid not in abs_set}
    graph.nodes[new_node_id] = bind_node

    # Remove old edges
    graph.edges = {
        eid: e for eid, e in graph.edges.items()
        if e.source.node_id not in abs_set and e.target.node_id not in abs_set
    }

    # Generating new edges
    current_max_eid = max(graph.edges.keys() or [0])

    # Create a list of opponents you want to challenge
    all_targets = [top_node] + bottom_nodes

    # Assign IDs in order from current_max_eid

    for i, target in enumerate(all_targets):
        new_edge_id = current_max_eid + 1 + i

        is_source_top = (target == top_node)

        new_edge = models.Edge(
            edge_id = new_edge_id,
            label = bind_label,
            source = target if is_source_top else bind_node,
            target = bind_node if is_source_top else target
        )
        graph.edges[new_edge.edge_id] = new_edge

    # Registration of variable management information
    new_var_id = max((v.variable_node_id for v in graph.variables.values()), default=0) + 1
    variable = models.Variable()
    variable.variable_node_id = new_var_id
    # The managed entities are the new node and its surrounding relationships
    variable.abstracted_nodes = [top_node] + bottom_nodes
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

def expand_variable(graph, bind, bind_map, top_node_id, bottom_node_ids, target_variable_node_id, around):
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

    drawing_order = bind.drawing_order[1:]

    width = max_width
    height = max_height / (len(drawing_order) + 1)
    for i, level in enumerate(drawing_order):
        for j, node_id in enumerate(level):
            if node_id not in bind_map.values():
                node = bind.nodes.get(node_id)
                w = width / len(level)
                node.x = (top_node.x) + (w * (j + 1))
                node.width = w
                node.half_width = w / 2
                print(i)
                node.y = top_node.y + (height * (i + 1)) + (height / 2 if node.is_variable else 0)
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

def shift_subtree(node, dy):
    node.y += dy
    if hasattr(node, 'child_nodes'):
        for child in node.child_nodes:
            shift_subtree(child, dy)

def prepare_subgraph_ids(main_graph, sub_graph, bind_map):
    node_offset = max(main_graph.nodes.keys() or [0]) + 1
    edge_offset = max(main_graph.edges.keys() or [0]) + 1
    set_new_ids(sub_graph, node_offset, edge_offset)
    print(bind_map)
    new_bind_map = {iid: i + node_offset for iid, i in bind_map.items()}
    n = {oid: oid + node_offset for oid in bind_map.keys()}
    print(n)
    print(new_bind_map)
    return {oid: oid + node_offset for oid in bind_map.keys()}

def set_new_ids(bind, node_offset, edge_offset):
    # Node ID update
    new_nodes = {}
    for old_id, node in bind.nodes.items():
        new_id = old_id + node_offset
        node.node_id = new_id
        new_nodes[new_id] = node
    bind.nodes = new_nodes

    # Edge ID update
    new_edges = {}
    for old_eid, edge in bind.edges.items():
        new_eid = old_eid + edge_offset
        edge.edge_id = new_eid
        new_edges[new_eid] = edge
    bind.edges = new_edges

    # Updating variable ID
    current_max_node_id = max(bind.nodes.keys() or [0])
    new_variables = {}

    for i, (old_vid, variable) in enumerate(bind.variables.items(), start=1):
        new_vid = current_max_node_id + i
        variable.variable_node_id = new_vid
        new_variables[new_vid] = variable
    bind.variables = new_variables

def find_insertion_point(main_graph, target_ids):
    top_id, bottom_ids = find_topmost_node(main_graph, target_ids)
    if not bottom_ids: return None

    # Identifying the variable node ID
    first_child = main_graph.nodes.get(bottom_ids[0])
    if not first_child or not first_child.parent_nodes: return None

    return {
        'top_id': top_id,
        'bottom_ids': bottom_ids,
        'target_var_id': first_child.parent_nodes[0].node_id
    }

def refresh_subgraph_layout(sub_graph, new_bind_map, top_id):
    # Use the map to identify the "route within the part" which now has a new ID
    new_root_id = new_bind_map.get(top_id)
    new_root = sub_graph.nodes.get(new_root_id)

    if new_root:
        # Establish parent-child relationships based on a new ID
        assign_levels(sub_graph, new_root)

        # Generate and set a new drawing order
        order, most_nodes = generate_drawing_order(sub_graph, new_root)
        sub_graph.drawing_order = order