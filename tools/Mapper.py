from common import Definitions, Values
from common.Utilities import execute_command, error_exit, backup_file_orig, restore_file_orig, replace_file, get_source_name_from_slice
from tools import Emitter, Logger, Finder, Converter, Writer
from ast import Generator
import sys

BREAK_LIST = [",", " ", " _", ";", "\n"]


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
        # command += "| grep '^Match ' "
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


def generate_ast_map(generated_script_files):
    ast_map_info = dict()
    if len(generated_script_files) == 0:
        Emitter.normal("\t -nothing-to-do")
    else:
        ast_map_info_local = generate_local_reference(generated_script_files)
        generate_global_reference(generated_script_files)
        ast_map_info = ast_map_info_local

        # extend namespace mapping using global reference
        Emitter.sub_sub_title("merging local and global references")
        for vector_pair in Values.map_namespace_global:
            map_global = Values.map_namespace_global[vector_pair]
            map_local = Values.map_namespace_local[vector_pair]
            map_merged = map_local
            for name_a in map_global:
                if name_a not in map_merged:
                    map_merged[name_a] = map_global[name_a]
            Values.map_namespace[vector_pair] = map_merged

        Writer.write_var_map(map_merged, Definitions.FILE_NAMESPACE_MAP)

    return ast_map_info


def generate_global_reference(generated_script_files):
    variable_map_info = dict()
    if len(generated_script_files) == 0:
        Emitter.normal("\t -nothing-to-do")
    else:
        Emitter.sub_sub_title("generating map using global reference")
        for file_list, generated_data in generated_script_files.items():
            slice_file_a = file_list[0]
            slice_file_c = file_list[2]
            vector_source_a = get_source_name_from_slice(slice_file_a)
            vector_source_c = get_source_name_from_slice(slice_file_c)

            map_file_name = Definitions.DIRECTORY_OUTPUT + "/" + slice_file_a.split("/")[-1].replace(".slice", "") + ".map"
            if not Values.USE_CACHE:
                generate_map(vector_source_a, vector_source_c, map_file_name)
            ast_node_map = get_mapping(map_file_name)
            Emitter.data(ast_node_map)
            ast_node_map = extend_mapping(ast_node_map, map_file_name, vector_source_a, vector_source_c)

            Emitter.normal("\tupdating map using anti-unification")
            Emitter.data(ast_node_map)
            refined_var_map = derive_namespace_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            Values.map_namespace_global[(vector_source_a, vector_source_c)] = refined_var_map
            Writer.write_var_map(refined_var_map, Definitions.FILE_NAMESPACE_MAP_GLOBAL)

            Emitter.normal("\tderiving method invocation map")
            method_invocation_map = extend_method_invocation_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            Emitter.data("method invocation map", method_invocation_map)
            Values.Method_ARG_MAP_GLOBAL[(vector_source_a, vector_source_c)] = method_invocation_map

            Emitter.normal("\tderiving function signature map")
            function_map = extend_function_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            Emitter.data("function map", function_map)
            Values.FUNCTION_MAP_GLOBAL[(vector_source_a, vector_source_c)] = function_map

            variable_map_info[file_list] = ast_node_map
            # variable_map_info[file_list] = dict()
            # variable_map_info[file_list]['ast-map'] = ast_node_map
            # variable_map_info[file_list]['var-map'] = var_map
    return variable_map_info


def generate_local_reference(generated_script_files):
    variable_map_info = dict()
    if len(generated_script_files) == 0:
        Emitter.normal("\t -nothing-to-do")
    else:
        Emitter.sub_sub_title("generating map using local reference")
        for file_list, generated_data in generated_script_files.items():
            slice_file_a = file_list[0]
            slice_file_c = file_list[2]
            vector_source_a = get_source_name_from_slice(slice_file_a)
            vector_source_c = get_source_name_from_slice(slice_file_c)

            backup_file_orig(vector_source_a)
            backup_file_orig(vector_source_c)
            replace_file(slice_file_a, vector_source_a)
            replace_file(slice_file_c, vector_source_c)

            map_file_name = Definitions.DIRECTORY_OUTPUT + "/" + slice_file_a.split("/")[-1] + ".map"
            if not Values.USE_CACHE:
                generate_map(vector_source_a, vector_source_c, map_file_name)
            ast_node_map = get_mapping(map_file_name)
            Emitter.data(ast_node_map)
            ast_node_map = extend_mapping(ast_node_map, map_file_name, vector_source_a, vector_source_c)

            Emitter.normal("\tupdating map using anti-unification")
            Emitter.data(ast_node_map)
            refined_var_map = derive_namespace_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            Values.map_namespace_local[(vector_source_a, vector_source_c)] = refined_var_map
            Writer.write_var_map(refined_var_map, Definitions.FILE_NAMESPACE_MAP_LOCAL)

            Emitter.normal("\tderiving method invocation map")
            method_invocation_map = extend_method_invocation_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            Emitter.data("method invocation map", method_invocation_map)
            Values.Method_ARG_MAP_LOCAL[(vector_source_a, vector_source_c)] = method_invocation_map

            Emitter.normal("\tderiving function signature map")
            function_map = extend_function_map(ast_node_map, vector_source_a, vector_source_c, slice_file_a)
            Emitter.data("function map", function_map)
            Values.FUNCTION_MAP_LOCAL[(vector_source_a, vector_source_c)] = function_map

            restore_file_orig(vector_source_a)
            restore_file_orig(vector_source_c)
            variable_map_info[file_list] = ast_node_map
            # variable_map_info[file_list] = dict()
            # variable_map_info[file_list]['ast-map'] = ast_node_map
            # variable_map_info[file_list]['var-map'] = var_map
    return variable_map_info


def derive_namespace_map(ast_node_map, source_a, source_c, slice_file_a):
    namespace_map = dict()
    refined_var_map = dict()

    ast_tree_a = Generator.get_ast_json(source_a, Values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = Generator.get_ast_json(source_c, Values.TARGET_REQUIRE_MACRO,  regenerate=True)

    neighbor_ast = None
    neighbor_ast_range = None
    neighbor_type, neighbor_name, slice = str(slice_file_a).split("/")[-1].split(".c.")[-1].split(".")
    if neighbor_type == "func":
        neighbor_ast = Finder.search_function_node_by_name(ast_tree_a, neighbor_name)
    elif neighbor_type == "var":
        neighbor_name = neighbor_name[:neighbor_name.rfind("_")]
        neighbor_ast = Finder.search_node(ast_tree_a, "VarDecl", neighbor_name)
    elif neighbor_type == "struct":
        neighbor_ast = Finder.search_node(ast_tree_a, "RecordDecl", neighbor_name)

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
                identifier_a = ast_node_a["value"]
                if "identifier" in ast_node_a.keys():
                    identifier_a = ast_node_a['identifier']
                if node_type_a == "DeclRefExpr" and ast_node_a["ref_type"] == "FunctionDecl":
                    identifier_a = identifier_a + "("
                if ast_node_c:
                    node_type_c = ast_node_c['type']
                    if node_type_c in ["VarDecl", "DeclRefExpr", "ParmVarDecl"]:
                        identifier_c = ast_node_c['value']
                        if "identifier" in ast_node_c.keys():
                            identifier_c = ast_node_c['identifier']
                        if node_type_c == "DeclRefExpr" and ast_node_c["ref_type"] == "FunctionDecl":
                            identifier_c = identifier_c + "("

                        if identifier_a not in namespace_map:
                            namespace_map[identifier_a] = dict()
                        if identifier_c not in namespace_map[identifier_a]:
                            namespace_map[identifier_a][identifier_c] = value_score
                        else:
                            namespace_map[identifier_a][identifier_c] = namespace_map[identifier_a][identifier_c] + value_score

            elif node_type_a == "Macro":
                if 'value' in ast_node_a.keys():
                    value_a = ast_node_a['value']
                    if ast_node_c:
                        node_type_c = ast_node_c['type']
                        if node_type_c == "Macro":
                            if 'value' in ast_node_c.keys():
                                value_c = ast_node_c['value']
                                if value_a not in namespace_map:
                                    namespace_map[value_a] = dict()
                                if value_c not in namespace_map[value_a]:
                                    namespace_map[value_a][value_c] = value_score
                                else:
                                    namespace_map[value_a][value_c] = namespace_map[value_a][value_c] + value_score

            elif node_type_a == "LabelStmt":
                if 'value' in ast_node_a.keys():
                    value_a = ast_node_a['value']
                    if ast_node_c:
                        node_type_c = ast_node_c['type']
                        if node_type_c == "LabelStmt":
                            if 'value' in ast_node_c.keys():
                                value_c = ast_node_c['value']
                                if value_a not in namespace_map:
                                    namespace_map[value_a] = dict()
                                if value_c not in namespace_map[value_a]:
                                    namespace_map[value_a][value_c] = value_score
                                else:
                                    namespace_map[value_a][value_c] = namespace_map[value_a][value_c] + value_score

            elif node_type_a in ["MemberExpr", "ArraySubscriptExpr"]:
                # value_a = ast_node_a['value']
                node_type_a = ast_node_a['type']
                if node_type_a in ["MemberExpr"]:
                    value_a = Converter.convert_member_expr(ast_node_a, True)
                elif node_type_a == "ArraySubscriptExpr":
                    value_a = Converter.convert_array_subscript(ast_node_a, True)

                if ast_node_c:
                    node_type_c = ast_node_c['type']
                    if node_type_c in ["MemberExpr", "ArraySubscriptExpr"]:
                        # value_c = ast_node_c['value']
                        if node_type_c in ["MemberExpr"]:
                            value_c = Converter.convert_member_expr(ast_node_c, True)
                        elif node_type_c == "ArraySubscriptExpr":
                            value_c = Converter.convert_array_subscript(ast_node_c, True)

                        if value_a not in namespace_map:
                            namespace_map[value_a] = dict()
                        if value_c not in namespace_map[value_a]:
                            namespace_map[value_a][value_c] = value_score
                        else:
                            namespace_map[value_a][value_c] = namespace_map[value_a][value_c] + value_score

            elif node_type_a in ["FunctionDecl"]:
                method_name_a = ast_node_a["identifier"]
                method_name_c = ast_node_c["identifier"]
                value_a = method_name_a + "("
                value_c = method_name_c + "("
                if value_a not in namespace_map:
                    namespace_map[value_a] = dict()
                if value_c not in namespace_map[value_a]:
                    namespace_map[value_a][value_c] = value_score
                else:
                    namespace_map[value_a][value_c] = namespace_map[value_a][value_c] + value_score

            elif node_type_a in ["CallExpr"]:
                children_a = ast_node_a["children"]
                children_c = ast_node_c["children"]

                method_name_a = children_a[0]["value"]
                method_name_c = children_c[0]["value"]
                value_a = method_name_a + "("
                value_c = method_name_c + "("
                if value_a not in namespace_map:
                    namespace_map[value_a] = dict()
                if value_c not in namespace_map[value_a]:
                    namespace_map[value_a][value_c] = value_score
                else:
                    namespace_map[value_a][value_c] = namespace_map[value_a][value_c] + value_score

    for value_a in namespace_map:
        candidate_list = namespace_map[value_a]
        max_score = 0
        best_candidate = None
        for candidate in candidate_list:
            candidate_score = candidate_list[candidate]
            if max_score < candidate_score:
                best_candidate = candidate
                max_score = candidate_score
        if "(" in value_a:
            value_a = value_a.split("(")[0] + "("
        if "(" in best_candidate:
            best_candidate = best_candidate.split("(")[0] + "("
        if not value_a or not best_candidate:
            continue
        if any(token in str(value_a).lower() for token in BREAK_LIST):
            continue
        if any(token in str(best_candidate).lower() for token in BREAK_LIST):
            continue

        # generate all possible member relations with each var mapping
        if "." in value_a and "." in best_candidate:
            refined_var_map["." + value_a.split(".")[-1]] = "." + best_candidate.split(".")[-1]
        refined_var_map[value_a] = best_candidate

    return refined_var_map


def extend_function_map(ast_node_map, source_a, source_c, slice_file_a):
    function_map = dict()

    ast_tree_a = Generator.get_ast_json(source_a, Values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = Generator.get_ast_json(source_c, Values.TARGET_REQUIRE_MACRO,  regenerate=True)

    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        ast_node_a = Finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = Finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)

        if ast_node_a and ast_node_c:
            node_type_a = ast_node_a['type']
            node_type_c = ast_node_c['type']
            if node_type_a in ["FunctionDecl"] and node_type_c in ["FunctionDecl"]:
                children_a = ast_node_a["children"]
                children_c = ast_node_c["children"]
                if len(children_a) < 1 or len(children_c) < 1 or len(children_a) == len(children_c):
                    continue
                method_name = children_a["identifier"]

                arg_operation = []
                for i in range(1, len(children_a)):
                    node_txt_a = children_a[i]["type"] + "(" + str(children_a[i]["id"]) + ")"
                    if node_txt_a in ast_node_map.keys():
                        node_txt_c = ast_node_map[node_txt_a]
                        node_id_c = int(str(node_txt_c).split("(")[1].split(")")[0])
                        ast_node_c = Finder.search_ast_node_by_id(ast_tree_c, node_id_c)
                        if ast_node_c in children_c:
                            arg_operation.append((Definitions.MATCH, i, children_c.index(ast_node_c)))
                        else:
                            arg_operation.append((Definitions.DELETE, i))
                    else:
                        arg_operation.append((Definitions.DELETE, i))
                for i in range(1, len(children_c)):
                    node_txt_c = children_c[i]["type"] + "(" + str(children_c[i]["id"]) + ")"
                    if node_txt_c not in ast_node_map.values():
                        arg_operation.append((Definitions.INSERT, i, children_c[i]["value"]))

                function_map[method_name] = arg_operation
    return function_map


def extend_method_invocation_map(ast_node_map, source_a, source_c, slice_file_a):
    method_invocation_map = dict()

    ast_tree_a = Generator.get_ast_json(source_a, Values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = Generator.get_ast_json(source_c, Values.TARGET_REQUIRE_MACRO,  regenerate=True)

    for ast_node_txt_a in ast_node_map:
        ast_node_txt_c = ast_node_map[ast_node_txt_a]
        ast_node_id_a = int(str(ast_node_txt_a).split("(")[1].split(")")[0])
        ast_node_id_c = int(str(ast_node_txt_c).split("(")[1].split(")")[0])
        ast_node_a = Finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
        ast_node_c = Finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)

        if ast_node_a and ast_node_c:
            node_type_a = ast_node_a['type']
            node_type_c = ast_node_c['type']
            if node_type_a in ["CallExpr"] and node_type_c in ["CallExpr"]:
                children_a = ast_node_a["children"]
                children_c = ast_node_c["children"]
                if len(children_a) < 1 or len(children_c) < 1 or len(children_a) == len(children_c):
                    continue
                method_name = children_a[0]["value"]

                arg_operation = []
                for i in range(1, len(children_a)):
                    node_txt_a = children_a[i]["type"] + "(" + str(children_a[i]["id"]) + ")"
                    if node_txt_a in ast_node_map.keys():
                        node_txt_c = ast_node_map[node_txt_a]
                        node_id_c = int(str(node_txt_c).split("(")[1].split(")")[0])
                        ast_node_c = Finder.search_ast_node_by_id(ast_tree_c, node_id_c)
                        if ast_node_c in children_c:
                            arg_operation.append((Definitions.MATCH, i, children_c.index(ast_node_c)))
                        else:
                            arg_operation.append((Definitions.DELETE, i))
                    else:
                        arg_operation.append((Definitions.DELETE, i))
                for i in range(1, len(children_c)):
                    node_txt_c = children_c[i]["type"] + "(" + str(children_c[i]["id"]) + ")"
                    if node_txt_c not in ast_node_map.values():
                        arg_operation.append((Definitions.INSERT, i, children_c[i]["value"]))

                method_invocation_map[method_name] = arg_operation
    return method_invocation_map


# adjust the mapping via anti-unification
def extend_mapping(ast_node_map, map_file_name, source_a, source_c):
    ast_tree_a = Generator.get_ast_json(source_a, Values.DONOR_REQUIRE_MACRO, regenerate=True)
    ast_tree_c = Generator.get_ast_json(source_c, Values.TARGET_REQUIRE_MACRO,  regenerate=True)

    with open(map_file_name, 'r') as ast_map:
        line = ast_map.readline().strip()
        while line:
            line = line.split(" ")
            operation = line[0]
            content = " ".join(line[1:])
            if operation == Definitions.MATCH:
                try:
                    node_a, node_c = clean_parse(content, Definitions.TO)
                    ast_node_id_a = int(str(node_a).split("(")[1].split(")")[0])
                    ast_node_id_c = int(str(node_c).split("(")[1].split(")")[0])
                    ast_node_a = Finder.search_ast_node_by_id(ast_tree_a, ast_node_id_a)
                    ast_node_c = Finder.search_ast_node_by_id(ast_tree_c, ast_node_id_c)

                    au_pairs = anti_unification(ast_node_a, ast_node_c)
                    for au_pair_key in au_pairs:
                        au_pair_value = au_pairs[au_pair_key]
                        ast_node_map[au_pair_key] = au_pair_value
                except Exception as exception:
                    error_exit(exception, "Something went wrong in MATCH (AC)", line, operation, content)
            line = ast_map.readline().strip()
    return ast_node_map


def anti_unification(ast_node_a, ast_node_c):
    au_pairs = dict()
    waiting_list_a = [ast_node_a]
    waiting_list_c = [ast_node_c]

    while len(waiting_list_a) != 0 and len(waiting_list_c) != 0:
        current_a = waiting_list_a.pop()
        current_c = waiting_list_c.pop()

        children_a = current_a["children"]
        children_c = current_c["children"]

        # do not support anti-unification with different number of children yet
        if len(children_a) != len(children_c):
            continue

        length = len(children_a)
        for i in range(length):
            child_a = children_a[i]
            child_c = children_c[i]
            if child_a["type"] == child_c["type"]:
                waiting_list_a.append(child_a)
                waiting_list_c.append(child_c)
            else:
                key = child_a["type"] + "(" + str(child_a["id"]) + ")"
                value = child_c["type"] + "(" + str(child_c["id"]) + ")"
                au_pairs[key] = value

    return au_pairs

