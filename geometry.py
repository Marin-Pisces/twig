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

def assign_levels(graph, root):
    source_id_list = [e.source.node_id for e in graph.edges]
    target_id_list = [e.target.node_id for e in graph.edges]

    parent_id_list = [root.node_id]
    next_level = 1

    next_ids = set()

    while parent_id_list:
        source_indices = []
        target_indices = []
        indices = []
        child_ids = set()

        current_id = parent_id_list.pop(0)
        current_node = graph.nodes.get(current_id)

        source_indices.extend([i for i, val in enumerate(source_id_list) if val == current_id])
        target_indices.extend([i for i, val in enumerate(target_id_list) if val == current_id])

        indices = list(sorted(set(source_indices + target_indices)))

        for idx_list, to_ids in [
            (source_indices, target_id_list),
            (target_indices, source_id_list)
        ]:
            for idx in idx_list:
                to_id = to_ids[idx]
                if to_id != current_id:
                    next_ids.add(to_id)
                    node = graph.nodes.get(to_id)
                    if node:
                        child_ids.add(node.node_id)

        for child_node_id in child_ids:
            child_node = graph.nodes.get(child_node_id)
            if current_id not in child_node.parent_nodes:
                child_node.parent_nodes.extend(resolve_node([current_id], graph.nodes))
        current_node.child_nodes.extend(resolve_node(child_ids, graph.nodes))
        for i in reversed(indices):
            source_id_list.pop(i)
            target_id_list.pop(i)

        if not parent_id_list:
            parent_id_list.extend(next_ids)
            next_level += 1
            next_ids = set()


def generate_drawing_order(graph, root):
    top_down_order = []
    most_level_nodes = 0
    target_nodes = [root]
    child_nodes = []
    current_level_nodes = [root.node_id]

    top_down_order.append(deepcopy(current_level_nodes))

    while target_nodes:
        target = target_nodes.pop(0)
        if current_level_nodes:
            current_level_nodes.pop()
        target_nodes.extend([t for t in target.child_nodes])
        child_nodes.extend([t for t in target.child_nodes])
        if (not current_level_nodes) and child_nodes:
            child_node_ids = [c.node_id for c in child_nodes]
            top_down_order.append(deepcopy(child_node_ids))
            current_level_nodes = deepcopy(child_node_ids)
            child_nodes = []
            if len(child_node_ids) > most_level_nodes:
                most_level_nodes = len(child_node_ids)
    return top_down_order, most_level_nodes

def calculate_positions(graph, most_level_nodes):
    node_w = 100
    node_h = 100

    root_node = True
    w = most_level_nodes * node_w
    h = 0
    for level in graph.drawing_order:
        for node_id in level:
            node = graph.nodes.get(node_id)
            if root_node:
                root_node = False
                node.x = w/len(level)
                node.y = h
                node.width = w
                node.height = h
                node.half_width = w/len(level)
            if node.child_nodes:
                parent_x = node.x
                parent_w = node.width
                parent_h = node.height
                parent_hw = node.half_width
                x = parent_x - parent_hw
                w = parent_w/len(node.child_nodes)
                h = parent_h + node_h
                hw = w/2
                for i, child in enumerate(node.child_nodes):
                    child.x = x + hw + (w * i)
                    child.y = h
                    child.width  = w
                    child.height = h
                    child.half_width = hw

def resolve_node(target_ids, node_dict):
    node_list = []
    for target_id in target_ids:
        node_list.append(node_dict.get(target_id))
    return node_list