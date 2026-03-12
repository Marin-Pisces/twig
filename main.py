from gml_io import load, dump
from geometry import compute_layout
import models

def main():
    graph = models.RawGraph()
    graph = load("test.gml")
    compute_layout(graph)

if __name__ == "__main__":
    main()