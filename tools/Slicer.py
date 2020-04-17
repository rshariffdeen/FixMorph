#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common import Definitions
from common.Utilities import get_code, error_exit
from ast import Generator as ASTGenerator
from tools import Extractor, Oracle, Logger, Filter, Emitter, Transformer

segment_map = {"func": "FunctionDecl"}


def slice_source_file(source_path, segment_code, segment_identifier, project_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ast_tree = ASTGenerator.get_ast_json(source_path)
    segment_type = segment_map[segment_code]
    ast_script = list()
    source_relative_path = source_path.replace(project_path, ".")

    for ast_node in ast_tree['children']:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifier = ast_node['identifier']
            if node_identifier != segment_identifier:
                ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")

    # print(ast_script)
    output_file_name = "." + segment_code + "." + segment_identifier + ".slice"
    output_file_path = source_path + output_file_name
    Transformer.transform_source_file(source_path, ast_script, output_file_path)

