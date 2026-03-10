graph [
  comment "Twig library test data - 3 levels, 10 nodes, 9 edges"
  directed 1

  node [ id 1 label "Root" ]

  node [ id 2 label "Branch_A" ]
  node [ id 3 label "Branch_B" ]
  node [ id 4 label "Branch_C" ]

  node [ id 5 label "Leaf_A1" ]
  node [ id 6 label "Leaf_A2" ]
  node [ id 7 label "Leaf_B1" ]
  node [ id 8 label "Leaf_C1" ]
  node [ id 9 label "Leaf_C2" ]
  node [ id 10 label "Leaf_C3" ]

  # --- Edge に ID(11-19) と Label を追加 ---
  edge [ id 11 source 1 target 2 label "R-A" ]
  edge [ id 12 source 1 target 3 label "R-B" ]
  edge [ id 13 source 1 target 4 label "R-C" ]

  edge [ id 14 source 2 target 5 label "A-L1" ]
  edge [ id 15 source 2 target 6 label "A-L2" ]

  edge [ id 16 source 3 target 7 label "B-L1" ]

  edge [ id 17 source 4 target 8 label "C-L1" ]
  edge [ id 18 source 4 target 9 label "C-L2" ]
  edge [ id 19 source 4 target 10 label "C-L3" ]
]