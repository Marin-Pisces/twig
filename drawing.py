import matplotlib.pyplot as plt
import models

def draw(graph, node_label_draw = True, edgh_label_draw = True, node_drawing_style = None, variable_drawing_style = None):
    plt.figure()
    plt.axis('off')

    node_style     = models.NodeStyle()
    variable_style = models.NodeStyle()
    node_style     = set_node_style(node_drawing_style)
    variable_style = set_node_style(node_drawing_style, True)

    root = graph.drawing_order[0]
    first_draw = True

    for node_index, node in graph.nodes.items():

        if first_draw and node_index in root:
            plt.scatter(node.x - 10, node.y, s=1, alpha=0.0)
            plt.scatter(node.x + 10, node.y, s=1, alpha=0.0)
            first_draw = False

        if not node.is_variable:
            plt.scatter(node.x, node.y, s=node_style.size, marker=node_style.marker, c=node_style.color, edgecolor=node_style.edgecolor, zorder=2)
        else:
            plt.scatter(node.x, node.y, s=variable_style.size, marker=variable_style.marker, c=variable_style.color, edgecolor=variable_style.edgecolor, zorder=2)
        if node_label_draw:
            plt.text(node.x, node.y, node.label)
        else:
            plt.text(node.x, node.y, node.node_id)

    for edge in graph.edges:
        sx = edge.source.x
        sy = edge.source.y
        tx = edge.target.x - sx
        ty = edge.target.y - sy

        plt.arrow(sx, sy, tx, ty, head_width=0, head_length=0, width = 0.001)

        text_x = sx + (tx/2)
        text_y = sy + (ty/2)

        if edgh_label_draw:
            plt.text(text_x, text_y, edge.label)
        else:
            plt.text(text_x, text_y, edge.edge_id)
    plt.show()

def set_node_style(input_style, is_variable = False):
    style = models.NodeStyle()
    s = input_style if input_style else models.NodeStyle()
    style.size = 100 if s.size == 0 else s.size
    style.alpha = s.alpha if s.alpha != 0.0 else 1.0
    style.edgecolor = s.edgecolor if s.edgecolor != '' else '#000000'
    if is_variable:
        style.color = s.color if s.color != '' else '#0000FF'
        style.marker = s.marker if s.marker != '' else '^'
    else:
        style.color = s.color if s.color != '' else '#FF0000'
        style.marker = s.marker if s.marker != '' else 'o'
    return style