from copy import deepcopy
import os
import re

import models

def load(gml_file_name):
    os.getcwd()
    #TODO:  file path修正
    gml_file_path = os.path.join(os.path.dirname(__file__), gml_file_name)
    gml_file      = open(gml_file_path,'r',encoding="utf_8")
    print('open gml file name :',gml_file_name)
    parse_attributes(gml_file)

def dump():
    print("dump")

def parse_attributes(gml_file):
    data_types = {'node', 'edge', 'hyper_edge'}
    is_in_block = False
    element_list = []

    nodes = []
    edges = []
    variables = []
    pending_edges = []
    pending_variables = []

    while True:
        line = gml_file.readline()
        if line:
            split_data = line.split()
            if not split_data:
                continue
            head = split_data[0]
            if head in data_types:
                is_in_block = True
                elements = ""
                element_list = []
                data_type = head
            if is_in_block:
                element_list.extend(split_data)
                if ']' in split_data:
                    is_in_block = False
                    element_str = "".join(f"{s} " for s in element_list)

                    match data_type:
                        case "node":
                            nodes.append(deepcopy(process_node(element_str)))
                        case "edge":
                            pending_edges.append(deepcopy(parse_edge(element_str)))
                        case "hyper_edge":
                            hyper_edge_node, hyper_edge_edges, hyper_edge_variable = parse_hyper_edge(element_str)
                            nodes.append(hyper_edge_node)
                            pending_edges.extend(hyper_edge_edges)
                            pending_variables.append(hyper_edge_variable)
        else:
            break
    node_dict = {n.node_id: n for n in nodes}
    edges = process_edge(node_dict, pending_edges)
    variables = process_variable(node_dict, pending_variables)

def process_node(element_str):
    node = models.Node()
    node_element = {'id', 'label'}
    is_next_value = False
    element_name = ""

    pattern = r'("[^"]*"|\S+)'
    items = re.findall(pattern, element_str)
    for item in items:
        if is_next_value:
            is_next_value = False
            match element_name:
                case 'id':
                    node.node_id = int(item)
                case 'label':
                    item = item[1:-1]
                    node.label = item
        if item in node_element:
            is_next_value = True
            element_name = item
    return node

def parse_edge(element_str):
    pending_edge = models.PendingEdge()
    edge_element = {'id', 'label', 'source', 'target'}
    is_next_value = False
    element_name = ""

    pattern = r'("[^"]*"|\S+)'
    items = re.findall(pattern, element_str)
    for item in items:
        if is_next_value:
            is_next_value = False
            match element_name:
                case 'id':
                    pending_edge.edge_id = int(item)
                case 'label':
                    item = item[1:-1]
                    pending_edge.label = item
                case 'source':
                    pending_edge.source = int(item)
                case 'target':
                    pending_edge.target = int(item)
        if item in edge_element:
            is_next_value = True
            element_name = item
    return pending_edge

def parse_hyper_edge(element_str):
    node = models.Node()
    pending_edge = models.PendingEdge()
    pending_variable = models.PendingVariable()
    hyper_edge_element = {'node_id', 'edge_id', 'label', 'target'}
    is_next_value = False
    element_name = ""

    pending_edge_source = 0
    pending_edge_label  = ""
    pending_edge_ids     = []
    pending_edge_targets = []


    pending_edges = []

    pattern = r'("[^"]*"|\S+)'
    items = re.findall(pattern, element_str)
    for item in items:
        if is_next_value:
            is_next_value = False
            match element_name:
                case 'node_id':
                    node.node_id = int(item)
                    pending_variable.variable_node_id = int(item)
                    pending_edge_source = int(item)
                case 'edge_id':
                    item = item[1:-1]
                    pending_edge_ids = item.split(",")
                case 'label':
                    item = item[1:-1]
                    node.label = item
                    pending_edge_label = item
                case 'target':
                    item = item[1:-1]
                    pending_variable.abstracted_nodes = item.split(",")
                    pending_edge_targets = item.split(",")
        if item in hyper_edge_element:
            is_next_value = True
            element_name = item
    for edge_id, target in zip(pending_edge_ids, pending_edge_targets):
        pending_edge.edge_id = edge_id
        pending_edge.label   = pending_edge_label
        pending_edge.source  = int(pending_edge_source)
        pending_edge.target = int(target)
        pending_edges.append(deepcopy(pending_edge))
    return node, pending_edges, pending_variable

def process_edge(node_dict, pending_edges):
    edge = models.Edge()
    edges = []
    for pending in pending_edges:
        edge.edge_id = pending.edge_id
        edge.label   = pending.label
        edge.source  = node_dict.get(pending.source)
        edge.target  = node_dict.get(pending.target)
        edges.append(deepcopy(edge))
    return edges

def process_variable(node_dict, pending_variables):
    variable = models.Variable()
    variables = []
    for pending in pending_variables:
        nodes = []
        variable.variable_node_id = pending.variable_node_id
        for abstracted_node in pending.abstracted_nodes:
            nodes.append(node_dict.get(int(abstracted_node)))
        variable.abstracted_nodes.extend(nodes)
        variables.append(deepcopy(variable))
    return variables