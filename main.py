from gml_io import load, dump
from geometry import compute_layout, build_hyper_edges, substitute_variable
from drawing import draw
import models

def main():
    graph = load("test.gml")
    graph2 = load("stress_test.gml")
    compute_layout(graph, 1)
    bind = build_hyper_edges(graph, [4,11,12])
    substitute = substitute_variable(bind, graph2, {4:1, 11:4, 12:3})
    draw(substitute)

if __name__ == "__main__":
    main()