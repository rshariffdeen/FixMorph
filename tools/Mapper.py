from common import Definitions, Values
from common.Utilities import execute_command, error_exit, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
from tools import Emitter, Logger, Finder, Converter, Writer
from ast import Generator
import sys


def map_ast_from_source(source_a, source_b, script_file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Generator.generate_ast_script(source_a, source_b, script_file_path, True)
    mapping = dict()
    with open(script_file_path, 'r', encoding='utf8', errors="ignore") as script_file:
        script_lines = script_file.readlines()
        for script_line in script_lines:
            if "Match" in script_line:
                node_id_a = int(((script_line.split(" to ")[0]).split("(")[1]).split(")")[0])
                node_id_b = int(((script_line.split(" to ")[1]).split("(")[1]).split(")")[0])
                mapping[node_id_b] = node_id_a
    return mapping


def generate_map(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    Emitter.normal("\t\t" + file_a + Definitions.TO + file_b + "...")
    try:
        extra_arg = ""
        if file_a[-1] == 'h':
            extra_arg = " --"
        command = Definitions.DIFF_COMMAND + " -s=" + Definitions.DIFF_SIZE + " -dump-matches "
        if Values.DONOR_REQUIRE_MACRO:
            command += " " + Values.DONOR_PRE_PROCESS_MACRO + " "
        if Values.TARGET_REQUIRE_MACRO:
            command += " " + Values.TARGET_PRE_PROCESS_MACRO + " "
        command += file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        command += "| grep '^Match ' "
        command += " > " + output_file
        execute_command(command, False)
        Emitter.normal("\t\t\tmap generated")
    except Exception as e:
        error_exit(e, "Unexpected fail at generating map: " + output_file)


def clean_parse(content, separator):
    if content.count(separator) == 1:
        return content.split(separator)
    i = 0
    while i < len(content):
        if content[i] == "\"":
            i += 1
            while i < len(content) - 1:
                if content[i] == "\\":
                    i += 2
                elif content[i] == "\"":
                    i += 1
                    break
                else:
                    i += 1
            prefix = content[:i]
            rest = content[i:].split(separator)
            node1 = prefix + rest[0]
            node2 = separator.join(rest[1:])
            return [node1, node2]
        i += 1
    # If all the above fails (it shouldn't), hope for some luck:
    nodes = content.split(separator)
    half = len(nodes) // 2
    node1 = separator.join(nodes[:half])
    node2 = separator.join(nodes[half:])
    return [node1, node2]


def get_mapping(map_file_name):
    node_map = dict()
    with open(map_file_name, 'r') as ast_map:
        line = ast_map.readline().strip()
        while line:
            line = line.split(" ")
            operation = line[0]
            content = " ".join(line[1:])
            if operation == Definitions.MATCH:
                try:
                    node_a, node_c = clean_parse(content, Definitions.TO)
                    node_map[node_a] = node_c
                except Exception as exception:
                    error_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return node_map


def generate(generated_script_files):
    variable_map_info = dict()
    if len(generated_script_files) == 0:
        Emitter.normal("\t -nothing-to-do")
    else:
        for file_list, generated_data in generated_script_files.items():
            slice_file_a = file_list[0]
            slice_file_c = file_list[2]
            vector_source_a = get_source_name_from_slice(slice_file_a)
            vector_source_c = get_source_name_from_slice(slice_file_c)

            backup_file_orig(vector_source_a)
            backup_file_orig(vector_source_c)
            replace_file(slice_file_a, vector_source_a)
            replace_file(slice_file_c, vector_source_c)

            map_file_name = Definitions.DIRECTORY_TMP + "/diff_script_AC"
            if not Values.USE_CACHE:
                generate_map(vector_source_a, vector_source_c, map_file_name)
            ast_node_map = get_mapping(map_file_name)
            derive_var_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            restore_file_orig(vector_source_a)
            restore_file_orig(vector_source_c)
            variable_map_info[file_list] = ast_node_map
            # variable_map_info[file_list] = dict()
            # variable_map_info[file_list]['ast-map'] = ast_node_map
            # variable_map_info[file_list]['var-map'] = var_map
    return variable_map_info


def derive_var_map(ast_node_map, source_a, source_c, slice_file_a):
    var_map = dict()
    refined_var_map = dict()

    ast_tree_a = Generator.get_ast_json(source_a, Values.DONOR_REQUIRE_MACRO)
    ast_tree_c = Generator.get_ast_json(source_c, Values.TARGET_REQUIRE_MACRO)

    neighbor_ast = None
    neighbor_ast_range = None
    neighbor_type, neighbor_name, slice = str(slice_file_a).split("/")[-1].split(".c.")[-1].split(".")
    if neighbor_type == "func":
        neighbor_ast = Finder.search_function_node_by_name(ast_tree_a, neighbor_name)
    elif neighbor_type == "var":
        neighbor_name = neighbor_name[:neighbor_name.rfind("_")]
        neighbor_ast = Finder.search_node(ast_tree_a, "VarDecl", neighbor_name)

    if neighbor_ast:
        neighbor_ast_range = (int(neighbor_ast['begin']), int(neighbor_ast['end']))
    else:
        error_exit("No neighbor AST Found")

    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        ast_node_a = Finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = Finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)
        value_score = 1
        if ast_node_a:
            if ast_node_id_a in range(neighbor_ast_range[0], neighbor_ast_range[1]):
                value_score = 100
        if ast_node_a:
            node_type_a = ast_node_a['type']
            if node_type_a in ["VarDecl", "DeclRefExpr", "ParmVarDecl"]:
                if "identifer" in ast_node_a.keys():
                    identifier_a = ast_node_a['identifier']
                    if ast_node_c:
                        node_type_c = ast_node_c['type']
                        if node_type_c in ["VarDecl", "DeclRefExpr", "ParmVarDecl"]:
                            identifier_c = ast_node_c['identifier']
                            if identifier_a not in var_map:
                                var_map[identifier_a] = dict()
                            if identifier_c not in var_map[identifier_a]:
                                var_map[identifier_a][identifier_c] = value_score
                            else:
                                var_map[identifier_a][identifier_c] = var_map[identifier_a][identifier_c] + value_score

            elif node_type_a == "Macro":
                if 'value' in ast_node_a.keys():
                    value_a = ast_node_a['value']
                    if ast_node_c:
                        node_type_c = ast_node_c['type']
                        if node_type_c == "Macro":
                            if 'value' in ast_node_c.keys():
                                value_c = ast_node_c['value']
                                if value_a not in var_map:
                                    var_map[value_a] = dict()
                                if value_c not in var_map[value_a]:
                                    var_map[value_a][value_c] = value_score
                                else:
                                    var_map[value_a][value_c] = var_map[value_a][value_c] + value_score

            elif node_type_a in ["MemberExpr", "ArraySubscriptExpr"]:
                # value_a = ast_node_a['value']
                node_type_a = ast_node_a['type']
                if node_type_a in ["MemberExpr"]:
                    value_a, var_type, auxilary_list = Converter.convert_member_expr(ast_node_a)
                elif node_type_a == "ArraySubscriptExpr":
                    value_a, var_type, auxilary_list = Converter.convert_array_subscript(ast_node_a)

                if ast_node_c:
                    node_type_c = ast_node_c['type']
                    if node_type_c in ["MemberExpr", "ArraySubscriptExpr"]:
                        # value_c = ast_node_c['value']
                        if node_type_c in ["MemberExpr"]:
                            value_c, var_type, auxilary_list = Converter.convert_member_expr(ast_node_c)
                        elif node_type_c == "ArraySubscriptExpr":
                            value_c, var_type, auxilary_list = Converter.convert_array_subscript(ast_node_c)

                        if value_a not in var_map:
                            var_map[value_a] = dict()
                        if value_c not in var_map[value_a]:
                            var_map[value_a][value_c] = value_score
                        else:
                            var_map[value_a][value_c] = var_map[value_a][value_c] + value_score
    for value_a in var_map:
        candidate_list = var_map[value_a]
        max_score = 0
        best_candidate = None
        for candidate in candidate_list:
            candidate_score = candidate_list[candidate]
            if max_score < candidate_score:
                best_candidate = candidate
                max_score = candidate_score
        refined_var_map[value_a] = best_candidate

    Writer.write_var_map(refined_var_map, Definitions.FILE_VAR_MAP)
    # print(refined_var_map)
    return refined_var_map

