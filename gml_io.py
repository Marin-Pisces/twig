import os

def load(gml_file_name):
    os.getcwd()
    #TODO:  file path修正
    gml_file_path = os.path.join(os.path.dirname(__file__), gml_file_name)
    gml_file      = open(gml_file_path,'r',encoding="utf_8")
    print('open gml file name :',gml_file_name)

    data_types = {'node', 'edge', 'hyper_edge'}
    is_in_block = False
    element_list = []
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
            if is_in_block:
                element_list.extend(split_data)
                if ']' in split_data:
                    is_in_block = False
                    elements = "".join(f"{s} " for s in element_list)
        else:
            break
def dump():
    print("dump")

def