from gml_io import load, dump
from geometry import compute_layout, build_hyper_edges
from drawing import draw
import models

def main():
    #graph = load("stress_test.gml")
    graph = load("test.gml")
    compute_layout(graph)
    bind = build_hyper_edges(graph, [4,11,12])
    draw(bind)
    #dump("dump.gml", graph)

if __name__ == "__main__":
    main()