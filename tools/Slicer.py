#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common.Utilities import get_code, error_exit
from ast import Generator as ASTGenerator
from tools import Extractor, Oracle, Logger, Filter, Emitter

segment_map = {"func": "FunctionDecl"}


def slice_source_file(source_path, segment_code, segment_identifier):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ast_tree = ASTGenerator.get_ast_json(source_path)
    segment_type = segment_map[segment_code]
    ast_script = list()
    for ast_node in ast_tree:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifer = ast_node['identifier']
            if node_identifer != segment_identifier:
                ast_script.append("Delete " + node_type + "(" + str(node_id) + ")")

    print(ast_script)
