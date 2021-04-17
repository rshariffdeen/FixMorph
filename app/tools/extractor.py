import sys
import re
from app.tools import converter, emitter, finder, logger
from app.common.utilities import execute_command, get_file_list, error_exit, is_intersect, definitions
import os
from app.common import values
from app.ast import ast_generator


def extract_child_id_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
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
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.information("\t\t[info] extracting macro definitions from\n\t\t" + str(source_path))
    pre_macro_list = extract_pre_macro_list(source_path, True)
    extract_command = "clang -E -dD -dM "
    for pre_macro in pre_macro_list:
        extract_command += " -D " + pre_macro.strip().replace("\n", "") + " "
    extract_command += source_path + " > " + definitions.FILE_MACRO_DEF
    execute_command(extract_command)
    macro_def_list = []
    with open(definitions.FILE_MACRO_DEF, "r") as macro_file:
        result_list = macro_file.readlines()
        macro_def = None
        for line in result_list:
            if "#define" in line:
                if macro_def:
                    macro_def_list.append(macro_def)
                macro_def = line
            else:
                macro_def = macro_def + line
    return macro_def_list


def extract_complete_function_node(function_def_node, source_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # print(source_path)
    source_dir = "/".join(source_path.split("/")[:-1])
    # print(source_dir)
    if len(function_def_node['children']) > 1:
        if values.IS_LINUX_KERNEL:
            source_file_loc = values.CONF_PATH_B + "/" + function_def_node['file']
        else:
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
        project_path = extract_project_path(header_file_loc)
        if not project_path:
            header_file_loc = values.CONF_PATH_B + "/" + header_file_loc
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
                if search_dir in [values.CONF_PATH_A, values.CONF_PATH_B, values.CONF_PATH_C]:
                    return None, None
                search_dir = os.path.dirname(search_dir)

        ast_tree = ast_generator.get_ast_json(source_file_loc)
        function_node = finder.search_function_node_by_name(ast_tree, function_name)
        return function_node, source_file_loc


def extract_call_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    call_expr_list = list()
    node_type = str(ast_node["type"])
    if node_type == "CallExpr":
        call_expr_list.append(ast_node)
    else:
        if len(ast_node['children']) > 0:
            for child_node in ast_node['children']:
                child_call_list = extract_call_node_list(child_node)
                call_expr_list = call_expr_list + child_call_list
    return call_expr_list


def extract_label_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    label_stmt_list = dict()
    node_type = str(ast_node["type"])
    if node_type == "LabelStmt":
        node_value = ast_node['value']
        label_stmt_list[node_value] = ast_node
    else:
        if len(ast_node['children']) > 0:
            for child_node in ast_node['children']:
                child_label_list = extract_label_node_list(child_node)
                label_stmt_list.update(child_label_list)
    return label_stmt_list


def extract_goto_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    goto_stmt_list = list()
    node_type = str(ast_node["type"])
    if node_type == "GotoStmt":
        goto_stmt_list.append(ast_node)
    else:
        if len(ast_node['children']) > 0:
            for child_node in ast_node['children']:
                child_goto_list = extract_goto_node_list(child_node)
                goto_stmt_list = goto_stmt_list + child_goto_list
    return goto_stmt_list


def extract_function_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    function_node_list = dict()
    for child_node in ast_node['children']:
        node_type = str(child_node["type"])
        if node_type in ["FunctionDecl"]:
            identifier = str(child_node['identifier'])
            function_node_list[identifier] = child_node
    return function_node_list


def extract_reference_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ref_node_list = list()
    node_type = str(ast_node["type"])
    if node_type in ["Macro", "DeclRefExpr", "MemberExpr", "GotoStmt"]:
        ref_node_list.append(ast_node)

    if len(ast_node['children']) > 0:
        for child_node in ast_node['children']:
            child_ref_list = extract_reference_node_list(child_node)
            ref_node_list = ref_node_list + child_ref_list
    return ref_node_list


def extract_initialization_node_list(ast_node, ref_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    init_node_list = list()
    node_type = str(ast_node["type"])
    if node_type == "BinaryOperator":
        node_value = str(ast_node['value'])
        if node_value == "=":
            assign_node = ast_node['children'][0]
            if assign_node['type'] == "DeclRefExpr":
                if assign_node['value'] == ref_node['identifier']:
                    init_node_list.append(ast_node)
    else:
        if len(ast_node['children']) > 0:
            for child_node in ast_node['children']:
                child_init_list = extract_initialization_node_list(child_node, ref_node)
                init_node_list = init_node_list + child_init_list
    return init_node_list


def extract_decl_list(ast_node, ref_type=None):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    dec_list = list()
    node_type = str(ast_node["type"])
    if ref_type:
        if node_type == ref_type:
            identifier = str(ast_node['identifier'])
            dec_list.append(identifier)
    else:
        if node_type in ["FunctionDecl", "VarDecl", "ParmVarDecl", "RecordDecl"]:
            identifier = str(ast_node['identifier'])
            dec_list.append(identifier)

    if len(ast_node['children']) > 0:
        for child_node in ast_node['children']:
            child_dec_list = extract_decl_list(child_node, ref_type)
            dec_list = dec_list + child_dec_list
    return list(set(dec_list))


def extract_decl_node_list(ast_node, ref_type=None):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    dec_list = dict()
    if not ast_node:
        return dec_list
    node_type = str(ast_node["type"])
    if ref_type:
        if node_type == ref_type:
            identifier = str(ast_node['identifier'])
            dec_list[identifier] = ast_node
    else:
        if node_type in ["FunctionDecl", "VarDecl", "ParmVarDecl", "RecordDecl"]:
            identifier = str(ast_node['identifier'])
            dec_list[identifier] = ast_node

    if len(ast_node['children']) > 0:
        for child_node in ast_node['children']:
            child_dec_list = extract_decl_node_list(child_node, ref_type)
            dec_list.update(child_dec_list)
    return dec_list


def extract_decl_node_list_global(ast_tree):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    dec_list = dict()
    if not ast_tree:
        return dec_list
    if len(ast_tree['children']) > 0:
        for child_node in ast_tree['children']:
            child_node_type = child_node['type']
            if child_node_type in ["FunctionDecl", "VarDecl", "ParmVarDecl"]:
                identifier = str(child_node['identifier'])
                dec_list[identifier] = child_node
    return dec_list


def extract_enum_node_list(ast_tree):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    dec_list = dict()
    node_type = str(ast_tree["type"])
    if node_type in ["EnumConstantDecl"]:
        identifier = str(ast_tree['identifier'])
        dec_list[identifier] = ast_tree

    if len(ast_tree['children']) > 0:
        for child_node in ast_tree['children']:
            child_dec_list = extract_enum_node_list(child_node)
            dec_list.update(child_dec_list)
    return dec_list


def extract_global_var_node_list(ast_tree):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    dec_list = list()
    for ast_node in ast_tree:
        node_type = str(ast_node["type"])
        if node_type in ["VarDecl"]:
            dec_list.append(ast_node)
    return dec_list


def extract_data_type_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    data_type_list = list()
    node_type = str(ast_node["type"])
    if "data_type" in ast_node.keys():
        data_type = str(ast_node['data_type'])
        data_type_list.append(data_type)
    if len(ast_node['children']) > 0:
        for child_node in ast_node['children']:
            child_data_type_list = extract_data_type_list(child_node)
            data_type_list = data_type_list + child_data_type_list
    return list(set(data_type_list))


def extract_typedef_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    typedef_node_list = dict()
    node_type = str(ast_node["type"])
    if node_type in ["TypedefDecl", "RecordDecl"]:
        identifier = str(ast_node['identifier'])
        typedef_node_list[identifier] = ast_node

    if len(ast_node['children']) > 0:
        for child_node in ast_node['children']:
            child_typedef_node_list = extract_typedef_node_list(child_node)
            typedef_node_list.update(child_typedef_node_list)
    return typedef_node_list


def extract_typeloc_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    typeloc_node_list = dict()
    node_type = str(ast_node["type"])
    if node_type in ["TypeLoc"]:
        identifier = str(ast_node['value'])
        typeloc_node_list[identifier] = ast_node

    if len(ast_node['children']) > 0:
        for child_node in ast_node['children']:
            child_typeloc_node_list = extract_typeloc_node_list(child_node)
            # print(child_typeloc_node_list)
            typeloc_node_list.update(child_typeloc_node_list)
    return typeloc_node_list


def extract_macro_definition(ast_node, source_file, target_file):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.information("\t\t[info]extracting macro definitions")
    macro_list = dict()
    node_type = str(ast_node['type'])
    # print(ast_node)
    # print(node_type)
    if node_type == "Macro":
        identifier = None
        if 'value' in ast_node:
            identifier = str(ast_node['value'])
            if "(" in identifier:
                identifier = identifier.split("(")[0] + "("
            # identifier = identifier.split("(")[0]
            # print(identifier)
            if identifier in values.STANDARD_MACRO_LIST:
                return macro_list
            else:
                start_line = int(ast_node['start line'])
                node_child_count = len(ast_node['children'])

                # print(node_child_count)
                if node_child_count > 0:
                    for child_node in ast_node['children']:
                        if 'value' not in child_node:
                            continue
                        identifier = str(child_node['value'])
                        # identifier = identifier.split("(")[0]
                        # print(identifier)
                        if "(" in identifier:
                            identifier = identifier.split("(")[0] + "("

                        if str(identifier).isdigit():
                            continue
                        if identifier in values.STANDARD_MACRO_LIST:
                            continue

                        if identifier not in macro_list.keys():
                            info = dict()
                            info['source'] = source_file
                            info['target'] = target_file
                            macro_list[identifier] = info
                        else:
                            info = macro_list[identifier]
                            if info['source'] != source_file or info['target'] != target_file:
                                error_exit("MACRO REQUIRED MULTIPLE TIMES!!")
                else:
                    if identifier not in macro_list.keys():
                        info = dict()
                        info['source'] = source_file
                        info['target'] = target_file
                        macro_list[identifier] = info
                    else:
                        info = macro_list[identifier]
                        if info['source'] != source_file or info['target'] != target_file:
                            error_exit("MACRO REQUIRED MULTIPLE TIMES!!")

    return macro_list


def extract_macro_node_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    macro_node_list = list()
    node_type = str(ast_node["type"])
    if node_type in ["Macro"]:
        macro_node_list.append(ast_node)
    else:
        if len(ast_node['children']) > 0:
            for child_node in ast_node['children']:
                child_ref_list = extract_macro_node_list(child_node)
                macro_node_list = macro_node_list + child_ref_list
    return macro_node_list


def extract_macro_ref_list(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    macro_node_list = extract_macro_node_list(ast_node)
    macro_ref_list = set()
    for macro_node in macro_node_list:
        if "value" in macro_node:
            macro_name = macro_node['value'].strip().replace("\n", "")
            if "(" in macro_name:
                macro_name = macro_name.split("(")[0] + "("
            macro_ref_list.add(macro_name)
    return list(macro_ref_list)


def extract_def_node_list(ast_tree):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    macro_node_list = dict()
    for ast_node in ast_tree['children']:
        node_type = str(ast_node["type"])
        if node_type in ["Macro", "FunctionDecl"]:
            if "identifier" in ast_node:
                identifier = ast_node['identifier']
                if "(" in identifier:
                    identifier = identifier.split("(")[0]
                macro_node_list[identifier] = ast_node
    return macro_node_list


def extract_var_dec_list(ast_node, start_line, end_line, only_in_range):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_list = list()
    child_count = len(ast_node['children'])
    node_start_line = int(ast_node['start line'])
    node_end_line = int(ast_node['end line'])
    start_column = int(ast_node['start column'])
    end_column = int(ast_node['end column'])
    node_type = ast_node['type']

    if only_in_range:
        if not is_intersect(node_start_line, node_end_line, start_line, end_line):
            return var_list

    if node_type in ["ParmVarDecl"]:
        var_name = str(ast_node['identifier'])
        var_type = str(ast_node['data_type'])
        line_number = int(ast_node['end line'])
        var_list.append((var_name, line_number, var_type))
        return var_list

    if node_type in ["VarDecl"]:
        child_count = len(ast_node['children'])
        if only_in_range and child_count < 2:
            return var_list
        var_name = str(ast_node['identifier'])
        var_type = str(ast_node['data_type'])
        line_number = int(ast_node['end line'])
        var_list.append((var_name, line_number, var_type))
        return var_list

    if child_count:
        for child_node in ast_node['children']:
            var_list = var_list + list(set(extract_var_dec_list(child_node, start_line, end_line, only_in_range)))
    return list(set(var_list))



def extract_var_ref_list(ast_node, start_line, end_line, only_in_range):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_list = list()
    child_count = len(ast_node['children'])
    node_start_line = int(ast_node['start line'])
    node_end_line = int(ast_node['end line'])
    start_column = int(ast_node['start column'])
    end_column = int(ast_node['end column'])
    node_type = ast_node['type']
    if only_in_range:
        if not is_intersect(node_start_line, node_end_line, start_line, end_line):
            return var_list

    if node_type in ["ReturnStmt"]:
        return var_list
    if node_type == "BinaryOperator":
        insert_line_number = int(ast_node['end line'])
        node_value = ast_node['value']
        if node_value == "=":
            left_side = ast_node['children'][0]
            right_side = ast_node['children'][1]
            right_var_list = extract_var_ref_list(right_side, start_line, end_line, only_in_range)
            left_var_list = extract_var_ref_list(left_side, start_line, end_line, only_in_range)
            operands_var_list = right_var_list + left_var_list
            for var_name, line_number, var_type in operands_var_list:
                var_list.append((str(var_name), insert_line_number, str(var_type)))
            return var_list
    if node_type == "UnaryOperator":
        insert_line_number = int(ast_node['end line'])
        node_value = ast_node['value']
        if node_value == "&":
            child_node = ast_node['children'][0]
            child_var_list = extract_var_ref_list(child_node, start_line, end_line, only_in_range)
            for var_name, line_number, var_type in child_var_list:
                var_list.append(("&" + str(var_name), insert_line_number, var_type))
            return var_list
    if node_type == "DeclRefExpr":
        line_number = int(ast_node['start line'])
        if "ref_type" in ast_node.keys():
            ref_type = str(ast_node['ref_type'])
            if ref_type == "FunctionDecl":
                return var_list
        var_name = str(ast_node['value'])
        # print(ast_node)
        if 'data_type' in ast_node.keys():
            var_type = str(ast_node['data_type'])
        else:
            var_type = "macro"
        var_list.append((var_name, line_number, var_type))
    if node_type == "ArraySubscriptExpr":
        var_name, var_type, auxilary_list = converter.convert_array_subscript(ast_node)
        line_number = int(ast_node['start line'])
        var_list.append((str(var_name), line_number, var_type))
        for aux_var_name, aux_var_type in auxilary_list:
            var_list.append((str(aux_var_name), line_number, aux_var_type))
        return var_list
    if node_type in ["MemberExpr"]:
        var_name, var_type, auxilary_list = converter.convert_member_expr(ast_node)
        line_number = int(ast_node['start line'])
        var_list.append((str(var_name), line_number, var_type))
        for aux_var_name, aux_var_type in auxilary_list:
            var_list.append((str(aux_var_name), line_number, aux_var_type))
        return var_list
    if node_type in ["ForStmt", "WhileStmt"]:
        body_node = ast_node['children'][child_count - 1]
        insert_line = body_node['start line']
        for i in range(0, child_count - 1):
            condition_node = ast_node['children'][i]
            condition_node_var_list = extract_var_ref_list(condition_node, start_line, end_line, only_in_range)
            for var_name, line_number, var_type in condition_node_var_list:
                var_list.append((str(var_name), insert_line, var_type))
        var_list = var_list + extract_var_ref_list(body_node, start_line, end_line, only_in_range)
        return var_list
    # if node_type in ["CaseStmt"]:
    #     return var_list
    if node_type in ["IfStmt"]:
        condition_node = ast_node['children'][0]
        body_node = ast_node['children'][1]
        insert_line = body_node['start line']
        condition_node_var_list = extract_var_ref_list(condition_node, start_line, end_line, only_in_range)
        for var_name, line_number, var_type in condition_node_var_list:
            var_list.append((str(var_name), insert_line, var_type))
        var_list = var_list + extract_var_ref_list(body_node, start_line, end_line, only_in_range)
        return var_list
    if node_type in ["SwitchStmt"]:
        condition_node = ast_node['children'][0]
        body_node = ast_node['children'][1]
        insert_line = body_node['start line']
        condition_node_var_list = extract_var_ref_list(condition_node, start_line, end_line, only_in_range)
        for var_name, line_number, var_type in condition_node_var_list:
            var_list.append((str(var_name), insert_line, var_type))
        var_list = var_list + extract_var_ref_list(body_node, start_line, end_line, only_in_range)
        return var_list
    if node_type in ["CallExpr"]:
        line_number = ast_node['end line']
        if line_number <= end_line:
            for child_node in ast_node['children']:
                child_node_type = child_node['type']
                if child_node_type == "DeclRefExpr":
                    if "ref_type" in child_node.keys():
                        ref_type = child_node['ref_type']
                        if ref_type == "VarDecl":
                            var_name = str(child_node['value'])
                            # print(ast_node)
                            var_type = str(child_node['data_type'])
                            var_list.append((var_name, line_number, var_type))
                elif child_node_type == "MemberExpr":
                    var_name, var_type, auxilary_list = converter.convert_member_expr(child_node)
                    var_list.append((str(var_name), line_number, var_type))
                    for aux_var_name, aux_var_type in auxilary_list:
                        var_list.append((str(aux_var_name), line_number, aux_var_type))
                elif child_node_type == "Macro":
                    var_name = str(child_node['value'])
                    if "?" in var_name:
                        continue
                    if "+" in var_name:
                        continue
                    var_type = "int"
                    var_list.append((str(var_name), line_number, var_type))
                else:
                    child_var_list = extract_var_ref_list(child_node, start_line, end_line, only_in_range)
                    for var_name, child_line, var_type in child_var_list:
                        var_list.append((var_name, line_number, var_type))
        return var_list
    if child_count:
        for child_node in ast_node['children']:
            var_list = var_list + list(set(extract_var_ref_list(child_node, start_line, end_line, only_in_range)))
    return list(set(var_list))


def extract_variable_list(source_path, start_line, end_line, only_in_range):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # print(source_path, start_line, end_line)
    emitter.normal("\t\t\t\tgenerating variable(available) list")
    variable_list = list()
    ast_map = ast_generator.get_ast_json(source_path)
    func_node = finder.search_function_node_by_loc(ast_map, int(end_line), source_path)
    if func_node is None:
        return variable_list
    # print(source_path, start_line, end_line)
    compound_node = func_node['children'][1]
    if not only_in_range:
        param_node = func_node['children'][0]
        line_number = compound_node['start line']
        for child_node in param_node['children']:
            child_node_type = child_node['type']
            if child_node_type == "ParmVarDecl":
                var_name = str(child_node['identifier'])
                # print(child_node)
                var_type = str(child_node['data_type'])
                if var_name not in variable_list:
                    variable_list.append((var_name, line_number, var_type))

    for child_node in compound_node['children']:
        child_node_type = child_node['type']
        # print(child_node_type)
        child_node_start_line = int(child_node['start line'])
        child_node_end_line = int(child_node['end line'])
        filter_declarations = False
        # print(child_node_start_line, child_node_end_line)
        child_var_dec_list = extract_var_dec_list(child_node, start_line, end_line, only_in_range)
        # print(child_var_dec_list)
        child_var_ref_list = extract_var_ref_list(child_node, start_line, end_line, only_in_range)
        # print(child_var_ref_list)
        if child_node_start_line <= int(end_line) <= child_node_end_line:
            variable_list = list(set(variable_list + child_var_ref_list + child_var_dec_list))
            break
        #
        # if child_node_type in ["IfStmt", "ForStmt", "CaseStmt", "SwitchStmt", "DoStmt"]:
        #     # print("Inside")
        #     if not is_intersect(start_line, end_line, child_node_start_line, child_node_end_line):
        #         continue
        #     filter_var_ref_list = list()
        #     for var_ref in child_var_ref_list:
        #         if var_ref in child_var_dec_list:
        #             child_var_ref_list.remove(var_ref)
        #         elif "->" in var_ref:
        #             var_name = var_ref.split("->")[0]
        #             if var_name in child_var_dec_list:
        #                 filter_var_ref_list.append(var_ref)
        #     child_var_ref_list = list(set(child_var_ref_list) - set(filter_var_ref_list))
        #     variable_list = list(set(variable_list + child_var_ref_list))
        # else:
        variable_list = list(set(variable_list + child_var_ref_list + child_var_dec_list))
    # print(variable_list)
    filtered_list = list()
    # print(str(start_line), str(end_line))
    for var in variable_list:
        var_name, line_num, var_type = var
        if only_in_range:
            for dec_var in child_var_dec_list:
                dec_var_name, dec_line_num, dec_var_type = dec_var
                if dec_var_name == var_name:
                    continue
        if int(start_line) <= int(line_num) <= int(end_line):
            filtered_list.append(var)

    # print(variable_list)
    # print(filtered_list)
    return filtered_list


def extract_unique_in_order(list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    seen_set = set()
    seen_add = seen_set.add
    return [x for x in list if not (x in seen_set or seen_add(x))]


def extract_project_path(source_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if values.CONF_PATH_A + "/" in source_path:
        return values.CONF_PATH_A
    elif values.CONF_PATH_B in source_path:
        return values.CONF_PATH_B
    elif values.Project_D.path in source_path:
        return values.Project_D.path
    elif values.CONF_PATH_C in source_path:
        return values.CONF_PATH_C
    elif values.CONF_PATH_E in source_path:
        return values.CONF_PATH_E
    else:
        return None


def extract_header_list(source_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    header_list = list()
    output_file_path = definitions.DIRECTORY_TMP + "/header-list"
    extract_command = "cat " + source_path + " | grep '#include' > " + output_file_path
    execute_command(extract_command)
    with open(output_file_path, 'r') as output_file:
        header_list = output_file.readlines()
    return header_list


def extract_pre_macro_list(source_file, only_if=False):
    result_file = definitions.DIRECTORY_TMP + "/result"
    cat_command = "cat " + source_file + " | grep '#if' > " + result_file
    if only_if:
        cat_command = "cat " + source_file + " | grep '#ifdef' > " + result_file
    execute_command(cat_command)
    pre_macro_list = set()
    with open(result_file, 'r') as log_file:
        read_lines = log_file.readlines()
        for line in read_lines:
            line = line.replace("\t", " ").replace("\n", "")
            if "ifdef" in line:
                pre_macro_list.add(line.split(" ")[-1])
            elif "ifndef" in line:
                pre_macro_list.add(line.split(" ")[-1])
            elif "defined(" in line:
                token_list = line.split("defined")
                for token in token_list[1:]:
                    macro = re.findall(r'\(([^]]*)\)', token)[0]
                    pre_macro_list.add(macro.replace(")", "").replace("(", ""))
            elif "defined" in line:
                token_list = line.split(" defined ")
                for token in token_list[1:]:
                    macro = token.split(" ")[0]
                    pre_macro_list.add(macro.replace(")", "").replace("(", ""))
    return pre_macro_list


def extract_pre_macro_command(source_file):
    macro_command = ""
    pre_macro_list = extract_pre_macro_list(source_file)
    if values.CONF_PATH_A in source_file or values.CONF_PATH_B in source_file:
        pre_process_arg = " --extra-arg-a=\"-D {}=1 \" "
    else:
        pre_process_arg = " --extra-arg-c=\"-D {}=1 \" "
    # pre_process_arg = " --extra-arg=\"-D {}=1 \" "
    for macro in pre_macro_list:
        macro_command = macro_command + pre_process_arg.format(macro)
    return macro_command


def extract_neighborhood(source_path, segment_code, segment_identifier, use_macro=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    ast_tree = ast_generator.get_ast_json(source_path, use_macro, True)
    segment_type = values.segment_map[segment_code]
    ast_script = list()
    segment_found = False
    for ast_node in ast_tree['children']:
        node_id = ast_node['id']
        node_type = ast_node['type']
        if node_type == segment_type:
            node_identifier = ast_node['identifier']
            if node_identifier == segment_identifier:
                if node_type == "FunctionDecl":
                    if len(ast_node['children']) > 1:
                        if ast_node['children'][1]['type'] == "CompoundStmt":
                            return ast_node
                else:
                    return ast_node


def extract_mapping(ast_node_a, ast_node_c, value_score):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    identifier_a = None
    identifier_c = None
    node_type_a = None
    node_type_c = None
    # skip_type_list = ["ReturnStmt", "CompoundStmt", "IntegerLiteral", "TypeLoc", "WhileStmt",
                      # "ForStmt", "DeclStmt", "IfStmt", "ForStmt"]

    if ast_node_a:
        node_type_a = ast_node_a['type']
        if node_type_a in values.map_allow_type_list:
            identifier_a = converter.get_node_value(ast_node_a).replace(":", "")
            if node_type_a in ["MemberExpr", "FieldDecl"]:
                identifier_a = "." + identifier_a
            elif node_type_a == "DeclRefExpr":
                if ast_node_a['ref_type'] == "FunctionDecl":
                    identifier_a = identifier_a + "("
            elif node_type_a == "LabelStmt":
                identifier_a = identifier_a + "."
            if ast_node_c:
                node_type_c = ast_node_c['type']
                if node_type_c in values.map_allow_type_list:
                    identifier_c = converter.get_node_value(ast_node_c).replace(":", "")
                    if node_type_c in ["MemberExpr", "FieldDecl"]:
                        identifier_c = "." + identifier_c
                    elif node_type_c == "DeclRefExpr":
                        if ast_node_c['ref_type'] == "FunctionDecl":
                            identifier_c = identifier_c + "("
                    elif node_type_c == "LabelStmt":
                        identifier_c = identifier_c + "."

        #
        # elif node_type_a in ["CallExpr"]:
        #     children_a = ast_node_a["children"]
        #     children_c = ast_node_c["children"]
        #     if len(children_a) > 1 and len(children_c) > 1:
        #         if 'value' in children_a[0].keys() and "value" in children_c[0].keys():
        #             method_name_a = children_a[0]["value"]
        #             method_name_c = children_c[0]["value"]
        #             identifier_a = method_name_a + "("
        #             identifier_c = method_name_c + "("

    return identifier_a, identifier_c, value_score, node_type_a, node_type_c


def extract_method_invocations(ast_node_map, call_node_a, call_node_c, method_name_a):
    arg_operation = []
    method_name_c = call_node_c['children'][0]["value"]
    parameter_list_a = call_node_a["children"][1:]
    parameter_list_c = call_node_c["children"][1:]

    for i in range(0, len(parameter_list_a)):
        param_node_txt_a = parameter_list_a[i]["type"] + "(" + str(parameter_list_a[i]["id"]) + ")"
        if param_node_txt_a in ast_node_map.keys():
            param_node_txt_c = ast_node_map[param_node_txt_a]
            param_node_id_c = int(str(param_node_txt_c).split("(")[1].split(")")[0])
            param_ast_node_c = finder.search_ast_node_by_id(call_node_c, param_node_id_c)
            if param_ast_node_c in parameter_list_c:
                arg_operation.append((definitions.MATCH, i, parameter_list_c.index(param_ast_node_c)))
            else:
                arg_operation.append((definitions.DELETE, i))
        else:
            arg_operation.append((definitions.DELETE, i))
    for i in range(0, len(parameter_list_c)):
        param_node_txt_c = parameter_list_c[i]["type"] + "(" + str(parameter_list_c[i]["id"]) + ")"
        if param_node_txt_c not in ast_node_map.values():
            arg_operation.append((definitions.INSERT, i, converter.get_node_value(parameter_list_c[i])))
    return method_name_a, method_name_c, arg_operation


def extract_method_signatures(ast_node_map, func_node_a, func_node_c, method_name_a):
    arg_operation = []
    method_name_c = func_node_c["identifier"]
    method_signature_a = func_node_a['children'][0]
    method_signature_c = func_node_c['children'][0]

    parameter_list_a = method_signature_a['children']
    parameter_list_c = method_signature_c['children']
    for i in range(1, len(parameter_list_a)):
        param_node_txt_a = parameter_list_a[i]["type"] + "(" + str(parameter_list_a[i]["id"]) + ")"
        if param_node_txt_a in ast_node_map.keys():
            param_node_txt_c = ast_node_map[param_node_txt_a]
            param_node_id_c = int(str(param_node_txt_c).split("(")[1].split(")")[0])
            param_ast_node_c = finder.search_ast_node_by_id(func_node_c, param_node_id_c)
            if param_ast_node_c in parameter_list_c:
                arg_operation.append((definitions.MATCH, i, parameter_list_c.index(param_ast_node_c)))
            else:
                arg_operation.append((definitions.DELETE, i))
        else:
            arg_operation.append((definitions.DELETE, i))
    for i in range(1, len(parameter_list_c)):
        param_node_txt_c = parameter_list_c[i]["type"] + "(" + str(parameter_list_c[i]["id"]) + ")"
        if param_node_txt_c not in ast_node_map.values():
            arg_operation.append((definitions.INSERT, i, converter.get_node_value(parameter_list_c[i])))

    return method_name_a, method_name_c, arg_operation


def extract_identifier_list(string_expression):
    identifier_list = []
    if not any(operator in string_expression for operator in ["|", "&&", ">", ">=", "==", "-", "+", "<", "<=", "*", "/"]):
        if "(" in string_expression or str(string_expression.strip()).isnumeric():
            return []
        else:
            return [string_expression.strip()]

    for operator in [">", ">=", "==", "-", "+", "<", "<=", "*", "/"]:
        if operator in string_expression:
            token_list = string_expression.split(operator)
            for token in token_list:
                identifier_list = identifier_list + extract_identifier_list(token)
    return identifier_list


def extract_header_file_list(ast_tree):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    header_file_list = list()
    if "file" in ast_tree:
        file_loc = ast_tree['file']
        if ".h" in file_loc:
            if values.Project_D.path in file_loc:
                file_loc = file_loc.replace(values.Project_D.path + "/", "")
            header_file_list.append(file_loc)
    if len(ast_tree['children']) > 0:
        for child_node in ast_tree['children']:
            child_list = extract_header_file_list(child_node)
            header_file_list = header_file_list + child_list
    return list(set(header_file_list))
