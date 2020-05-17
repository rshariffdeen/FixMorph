#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common import Values
from common.Utilities import get_code, error_exit
from ast import Generator as ASTGenerator
from tools import Extractor, Oracle, Logger, Filter, Emitter, Transformer


def slice_source_file(source_path, segment_code, segment_identifier, project_path, use_macro=False):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ast_tree = ASTGenerator.get_ast_json(source_path, use_macro)
    segment_type = Values.segment_map[segment_code]
    ast_script = list()
    source_relative_path = source_path.replace(project_path, ".")
    segment_found = False
    for ast_node in ast_tree['children']:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifier = ast_node['identifier']
            if node_identifier != segment_identifier:
                ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")
            else:
                segment_found = True

    if not segment_found:
        Emitter.information("Slice not created")
        return False

    # print(ast_script)
    output_file_name = "." + segment_code + "." + segment_identifier + ".slice"
    output_file_path = source_path + output_file_name
    Transformer.transform_source_file(source_path, ast_script, output_file_path)
    Emitter.normal("\t\t\tcreated " + output_file_path)

