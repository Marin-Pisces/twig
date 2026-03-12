import models

def compute_layout(graph, root_id = 0):
    if root_id in graph.nodes:
        root = graph.nodes[root_id]
    else:
        root = next(iter(graph.nodes.values()))
    assign_levels(graph, root)

def assign_levels(graph, root):
    source_id_list = [e.source.node_id for e in graph.edges]
    target_id_list = [e.target.node_id for e in graph.edges]

    parent_id_list = [root.node_id]
    next_parent_level    = 1

    next_parent_ids = set()

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
                    next_parent_ids.add(to_id)
                    node = graph.nodes.get(to_id)
                    if node:
                        child_ids.add(node.node_id)

        print(child_ids)
        for child_node_id in child_ids:
            child_node = graph.nodes.get(child_node_id)
            if current_id not in child_node.parent_nodes:
                child_node.parent_nodes.extend(resolve_node([current_id], graph.nodes))
        current_node.child_nodes.extend(resolve_node(child_ids, graph.nodes))
        for i in reversed(indices):
            source_id_list.pop(i)
            target_id_list.pop(i)

        if not parent_id_list:
            parent_id_list.extend(next_parent_ids)
            next_parent_level += 1
            next_parent_ids = set()
    print(graph.nodes)

def resolve_node(target_ids, node_dict):
    node_list = []
    for target_id in target_ids:
        node_list.append(node_dict.get(target_id))
    return node_list