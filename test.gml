graph [
  comment "Twig library test data - 3 levels, 10 nodes"
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

  edge [ source 1 target 2 ]
  edge [ source 1 target 3 ]
  edge [ source 1 target 4 ]

  edge [ source 2 target 5 ]
  edge [ source 2 target 6 ]

  edge [ source 3 target 7 ]

  edge [ source 4 target 8 ]
  edge [ source 4 target 9 ]
  edge [ source 4 target 10 ]
]