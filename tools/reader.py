#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import json
import os
from tools import logger


def read_json(file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    json_data = dict()
    if os.path.isfile(file_path):
        with open(file_path, 'r') as in_file:
            content = in_file.readline()
            json_data = json.loads(content)
    return json_data


def read_var_map(file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_map = dict()
    with open(file_path, 'r') as map_file:
        content = map_file.readlines()
        for mapping in content:
            id_a, id_c = mapping.split(":")
            var_map[id_a] = id_c
    return var_map


def read_namespace_map(file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    namespace_map = dict()
    with open(file_path, 'r') as map_file:
        content = map_file.readlines()
        vector_index = ""
        for line in content:
            if "-" in line:
                vector_index = (line.split("-")[0], line.split("-")[1].strip().replace("\n", ""))
                namespace_map[vector_index] = dict()
            if ":" in line:
                id_a, id_c = line.strip().replace("\n", "").split(":")
                namespace_map[vector_index][id_a] = id_c

    return namespace_map


def read_ast_map(file_path):
    ast_map = dict()
    map_list = read_json(file_path)
    for (file_path_info, node_map) in map_list:
        ast_map[(file_path_info[0], file_path_info[1])] = node_map
    return ast_map


