#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import json
from tools import Logger


def write_as_json(data_list, output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = json.dumps(data_list)
    with open(output_file_path, 'w') as out_file:
        out_file.writelines(content)


def write_var_map(var_map, output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = ""
    for var in var_map:
        content += var + ":" + var_map[var] + "\n"
    with open(output_file_path, 'w') as map_file:
        map_file.writelines(content)


def write_skip_list(skip_list, output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = "0\n"
    for line_number in skip_list:
        content += str(line_number) + "\n"
    with open(output_file_path, 'w') as map_file:
        map_file.writelines(content)


def write_ast_script(ast_script, output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    content = ""
    with open(output_file_path, 'w') as script_file:
        for op in ast_script:
            content += op
            if op != ast_script[-1] and not str(op).endswith("\n"):
                content += "\n"
        script_file.writelines(content)


def write_clone_list(clone_list, output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    data_list = list()
    for (vec_a, vec_c, var_map) in clone_list:
        vec_a_info = (vec_a.file_path, vec_a.function_name, vec_a.start_line, vec_a.end_line)
        vec_c_info = (vec_c.file_path, vec_c.function_name, vec_c.start_line, vec_c.end_line)
        data_list.append((vec_a_info, vec_c_info, var_map))

    content = json.dumps(data_list)
    with open(output_file_path, 'w') as out_file:
        out_file.writelines(content)


def write_script_info(script_info, output_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    data_list = list()
    for vec_path_info in script_info:
        vec_info = script_info[vec_path_info]
        data_list.append((vec_path_info, vec_info))
    content = json.dumps(data_list)
    with open(output_file_path, 'w') as out_file:
        out_file.writelines(content)
