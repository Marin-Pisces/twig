from collections import deque
import models

def compute_layout(graph, root_id = 0):
    if root_id in graph.nodes:
        root = graph.nodes[root_id]
    else:
        root = next(iter(graph.nodes.values()))
    assign_levels(graph, root)
    graph.drawing_order, most_level_nodes = generate_drawing_order(graph, root)
    calculate_positions(graph, most_level_nodes)

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

        neighbor_ids = adj.get(current_id, set())

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