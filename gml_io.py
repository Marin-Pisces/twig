import os

def load(gml_file_name):
    os.getcwd()

    #TODO:  file path修正
    gml_file_path = os.path.join(os.path.dirname(__file__), gml_file_name)
    gml_file      = open(gml_file_path,'r',encoding="utf_8")

    print('open gml file name :',gml_file_name)

def dump():
    print("dump")