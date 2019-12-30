import sys
from tools import Logger, Emitter
from common.Utilities import execute_command
import os
from common import Definitions

FILE_MACRO_DEF = Definitions.DIRECTORY_TMP + "/macro-def"


def extract_child_id_list(ast_node):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    id_list = list()
    for child_node in ast_node['children']:
        child_id = int(child_node['id'])
        id_list.append(child_id)
        grand_child_list = extract_child_id_list(child_node)
        if grand_child_list:
            id_list = id_list + grand_child_list
    if id_list:
        id_list = list(set(id_list))
    return id_list


def extract_macro_definitions(source_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.normal("\textracting macro definitions from\n\t\t" + str(source_path))
    extract_command = "clang -E -dD -dM " + source_path + " > " + FILE_MACRO_DEF
    execute_command(extract_command)
    with open(FILE_MACRO_DEF, "r") as macro_file:
        macro_def_list = macro_file.readlines()
        return macro_def_list


def extract_complete_function_node(function_def_node, source_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # print(source_path)
    source_dir = "/".join(source_path.split("/")[:-1])
    # print(source_dir)
    if len(function_def_node['children']) > 1:
        source_file_loc = source_dir + "/" + function_def_node['file']
        # print(source_file_loc)
        source_file_loc = os.path.abspath(source_file_loc)
        # print(source_file_loc)
        return function_def_node, source_file_loc
    else:
        # header_file_loc = source_dir + "/" + function_def_node['file']
        header_file_loc = function_def_node['file']
        if str(header_file_loc).startswith("."):
            header_file_loc = source_dir + "/" + function_def_node['file']
        # print(header_file_loc)

        function_name = function_def_node['identifier']
        source_file_loc = header_file_loc.replace(".h", ".c")
        source_file_loc = os.path.abspath(source_file_loc)
        # print(source_file_loc)
        if not os.path.exists(source_file_loc):
            source_file_name = source_file_loc.split("/")[-1]
            header_file_dir = "/".join(source_file_loc.split("/")[:-1])
            search_dir = os.path.dirname(header_file_dir)
            while not os.path.exists(source_file_loc):
                search_dir_file_list = get_file_list(search_dir)
                for file_name in search_dir_file_list:
                    if source_file_name in file_name and file_name[-2:] == ".c":
                        source_file_loc = file_name
                        break
                if search_dir in [Values.PATH_A, Values.PATH_B, Values.PATH_C]:
                    return None, None
                search_dir = os.path.dirname(search_dir)

        ast_tree = ASTGenerator.get_ast_json(source_file_loc)
        function_node = Finder.search_function_node_by_name(ast_tree, function_name)
        return function_node, source_file_loc
