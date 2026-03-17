from gml_io import load, dump
from geometry import compute_layout
from drawing import draw

def main():
    graph = load("test.gml")
    compute_layout(graph)
    draw(graph)
    dump("dump.gml", graph)

if __name__ == "__main__":
    main()