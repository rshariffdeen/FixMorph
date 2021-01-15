#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import os
from common.utilities import error_exit, execute_command
from tools import logger


SYMBOLIC_CONVERTER = "gen-bout"
BINARY_CONVERTER = "extract-bc"


def convert_cast_expr(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_list = list()
    type_node = ast_node['children'][0]
    type_value = type_node['value']
    data_type = None
    if "data_type" in type_node:
        data_type = str(type_node['data_type'])
    param_node = ast_node['children'][1]
    param_node_type = param_node['type']

    var_name = "(" + type_value + ") " + get_node_value(param_node)

    if only_string:
        return var_name
    return var_name, var_list


def convert_paren_node_to_expr(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_name = ""
    var_list = list()
    value = ""
    child_node = ast_node['children'][0]
    # print(child_node)
    child_node_type = child_node['type']
    value = get_node_value(child_node)
    var_name = "(" + value + ")"
    # print(var_name)
    if only_string:
        return var_name
    return var_name, list(set(var_list))


def convert_unary_node_to_expr(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_name = ""
    var_list = list()
    # print(ast_node)
    child_node = ast_node['children'][0]
    # print(left_child)
    child_value = ""
    child_type = str(child_node['type'])
    if child_type in ["DeclRefExpr", "IntegerLiteral"]:
        child_value = str(child_node['value'])
    elif child_type == "BinaryOperator":
        child_value = convert_binary_node_to_expr(child_node, True)
        # var_list = var_list + child_var_list
    elif child_type == "MemberExpr":
        child_value = convert_member_expr(child_node, True)
        # var_list = var_list + child_var_list
    elif child_type == "ParenExpr":
        child_value = convert_paren_node_to_expr(child_node, True)
        # var_list = var_list + child_var_list
    operation = str(ast_node['value'])
    # print(operation)
    var_name = child_value + operation
    if only_string:
        return var_name
    return var_name, list(set(var_list))


def convert_conditional_op_to_expr(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_name = ""
    condition_exp = convert_binary_node_to_expr(ast_node['children'][0], True)
    true_node = ast_node['children'][1]
    true_node_value = get_node_value(true_node)
    false_node = ast_node['children'][2]
    false_node_value = get_node_value(false_node)
    var_name = condition_exp + " ? " + true_node_value + " : " + false_node_value
    return var_name


def get_node_value(ast_node):
    ast_value = ""
    ast_type = str(ast_node['type'])
    if ast_type in ["DeclRefExpr", "IntegerLiteral", "StringLiteral", "VarDecl"]:
        ast_value = str(ast_node['value'])
    elif ast_type in ["ParmVarDecl", "RecordDecl"]:
        ast_value = ast_node['identifier']
    elif ast_type in ["FieldDecl"]:
        ast_value = ast_node['qualified_identifier'].split("::")[0] + "." + convert_member_expr(ast_node)
    elif ast_type == "FunctionDecl":
        ast_value = ast_node['identifier'] + "("
    elif ast_type == "BinaryOperator":
        ast_value = convert_binary_node_to_expr(ast_node, True)
        # var_list = var_list + left_child_var_list
    elif ast_type == "ParenExpr":
        ast_value = convert_paren_node_to_expr(ast_node, True)
        # var_list = var_list + left_child_var_list
    elif ast_type == "ArraySubscriptExpr":
        ast_value = convert_array_subscript(ast_node, True)
    elif ast_type == "MemberExpr":
        ast_value = convert_member_expr(ast_node, True)
        # var_list = var_list + left_child_var_list
    elif ast_type in ["Macro", "LabelStmt", "TypeLoc"]:
        ast_value = ast_node['value']
    elif ast_type == "CStyleCastExpr":
        ast_value = convert_cast_expr(ast_node, True)
    elif ast_type == "CallExpr":
        ast_value = convert_call_expr(ast_node, True)
    elif ast_type == "UnaryExprOrTypeTraitExpr":
        ast_value = ""
    elif ast_type == "UnaryOperator":
        ast_value = convert_unary_node_to_expr(ast_node, True)
    elif ast_type == "ConditionalOperator":
        ast_value = convert_conditional_op_to_expr(ast_node, True)
    elif ast_type == "PredefinedExpr":
        ast_value = get_node_value(ast_node['children'][0])
    else:
        print(ast_type)
        print(ast_node)
        error_exit("Unhandled node type in convert ast node")

    return ast_value


def convert_binary_node_to_expr(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_name = ""
    var_list = list()
    # print(ast_node)
    left_child = ast_node['children'][0]
    # print(left_child)
    left_child_value = get_node_value(left_child)
    operation = str(ast_node['value'])
    # print(operation)
    right_child = ast_node['children'][1]
    # print(right_child)
    right_child_value = get_node_value(right_child)
    var_name = left_child_value + " " + operation + " " + right_child_value
    if only_string:
        return var_name
    return var_name, list(set(var_list))


def convert_array_iterator(iterator_node, only_string=False):
    iterator_node_type = str(iterator_node['type'])
    var_list = list()
    if iterator_node_type in ["VarDecl", "ParmVarDecl"]:
        iterator_name = str(iterator_node['identifier'])
        iterator_data_type = None
        if "data-type" in iterator_node:
            iterator_data_type = str(iterator_node['data_type'])
        var_list.append((iterator_name, iterator_data_type))
        var_name = "[" + iterator_name + "]"
    elif iterator_node_type in ["Macro"]:
        iterator_value = str(iterator_node['value'])
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type == "DeclRefExpr":
        iterator_name = str(iterator_node['value'])
        iterator_data_type = None
        if "data-type" in iterator_node:
            iterator_data_type = str(iterator_node['data_type'])
        var_list.append((iterator_name, iterator_data_type))
        var_name = "[" + iterator_name + "]"
    elif iterator_node_type in ["IntegerLiteral"]:
        iterator_value = str(iterator_node['value'])
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type in ["BinaryOperator"]:
        iterator_value = convert_binary_node_to_expr(iterator_node, True)
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type in ["UnaryOperator"]:
        iterator_value = convert_unary_node_to_expr(iterator_node, True)
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type in ["MemberExpr"]:
        iterator_value = convert_member_expr(iterator_node, True)
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type == "ParenExpr":
        iterator_value = convert_paren_node_to_expr(iterator_node, True)
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type == "CallExpr":
        iterator_value = convert_call_expr(iterator_node, True)
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type == "ArraySubscriptExpr":
        iterator_value = convert_array_subscript(iterator_node, True)
        var_name = "[" + iterator_value + "]"
    elif iterator_node_type == "CStyleCastExpr":
        iterator_value = convert_cast_expr(iterator_node, True)
        var_name = "[" + iterator_value + "]"
    else:
        print(iterator_node)
        error_exit("Unknown iterator type for convert_array_iterator")
    if only_string:
        return var_name
    return var_name, var_list


def convert_array_subscript(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_list = list()
    var_name = ""
    var_data_type = ""
    # print(ast_node)
    array_node = ast_node['children'][0]
    array_type = str(array_node['type'])
    if array_type == "DeclRefExpr":
        array_name = str(array_node['value'])
        array_data_type = None
        if 'data_type' in array_node.keys():
            array_data_type = str(array_node['data_type'])
        var_data_type = array_data_type.split("[")[0]
        iterator_node = ast_node['children'][1]
        iterator_node_type = str(iterator_node['type'])
        iterator_name = convert_array_iterator(iterator_node, True)
        var_name = array_name + iterator_name
    elif array_type == "MemberExpr":
        array_name = str(array_node['value'])
        array_data_type = None
        if 'data_type' in array_node.keys():
            array_data_type = str(array_node['data_type'])
        if len(ast_node['children']) > 1:
            iterator_node = ast_node['children'][1]
            array_name = convert_member_expr(array_node, True)
            iterator_name = convert_array_iterator(iterator_node, True)
            var_name = array_name + iterator_name
    elif array_type == "ParenExpr":
        array_name = convert_paren_node_to_expr(array_node, True)
        var_data_type = None
        if 'data_type' in array_node.keys():
            var_data_type = str(array_node['data_type'])
        iterator_node = ast_node['children'][1]
        iterator_name = convert_array_iterator(iterator_node, True)
        var_name = array_name + iterator_name
    elif array_type == "Macro":
        var_data_type = None
        iterator_node = ast_node['children'][1]
        array_name = str(array_node['value'])
        iterator_name = convert_array_iterator(iterator_node, True)
        var_name = array_name + iterator_name
    elif array_type == "ArraySubscriptExpr":
        array_name = convert_array_subscript(array_node, True)
        iterator_node = ast_node['children'][1]
        iterator_name = convert_array_iterator(iterator_node, True)
        var_name = array_name + iterator_name
    else:
        print(array_type)
        print(array_node)
        print(ast_node)
        error_exit("Unknown data type for array_subscript")
    if only_string:
        return var_name
    return var_name, var_data_type, var_list


def convert_call_expr(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_name = ""
    function_name = ""
    operand_list = list()
    var_list = list()
    call_function_node = ast_node['children'][0]
    call_function_node_type = str(call_function_node['type'])
    call_function_node_ref_type = str(call_function_node['ref_type'])
    if call_function_node_type == "DeclRefExpr" and call_function_node_ref_type == "FunctionDecl":
        function_name = str(call_function_node['value'])
    else:
        print(ast_node)
        error_exit("unknown decl tyep in convert_call_expr")

    operand_count = len(ast_node['children'])
    for i in range(1, operand_count):
        operand_node = ast_node['children'][i]
        operand_node_type = str(operand_node['type'])
        if operand_node_type == "CallExpr":
            operand_var_name = convert_call_expr(operand_node, True)
            operand_list.append(operand_var_name)
            # var_list = var_list + operand_var_list
        elif operand_node_type == "DeclRefExpr":
            operand_var_name = str(operand_node['value'])
            operand_list.append(operand_var_name)
        elif operand_node_type == "MemberExpr":
            operand_var_name = convert_member_expr(operand_node, True)
            operand_list.append(operand_var_name)
        elif operand_node_type == "Macro":
            operand_var_name = str(operand_node['value'])
            if "?" in operand_var_name:
                continue
            operand_list.append(operand_var_name)
        elif operand_node_type == "IntegerLiteral":
            operand_var_name = str(operand_node['value'])
            operand_list.append(operand_var_name)
        else:
            print(operand_node)
            error_exit("unhandled operand for call expr convert")

    var_name = function_name + "("
    for operand in operand_list:
        var_name += operand
        if operand != operand_list[-1]:
            var_name += ","

    var_name += ")"
    # print(var_name)
    if only_string:
        return var_name
    return var_name, list(set(var_list))


def convert_member_expr(ast_node, only_string=False):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    var_list = list()
    var_name = ""
    var_data_type = ""
    # print(ast_node)
    if 'value' in ast_node.keys():
        node_value = ast_node['value']
        var_name = str(node_value.split(":")[-1])
        # print(var_name)
        var_data_type = str(ast_node['data_type'])
        if "isArrow" not in ast_node.keys():
            var_name = "." + var_name
        else:
            var_name = "->" + var_name
    child_node = ast_node['children'][0]
    while child_node:
        child_node_type = child_node['type']
        if child_node_type == "DeclRefExpr":
            var_name = str(child_node['value']) + var_name
        elif child_node_type == "ArraySubscriptExpr":
            # array_var_name, array_var_data_type, \
            # iterating_var_list = convert_array_subscript(child_node)
            # var_list = var_list + iterating_var_list
            # if var_name[:2] == "->":
            #     var_name = "." + var_name[2:]
            # var_name = array_var_name + var_name
            iterating_var_node = child_node['children'][1]

            # iterating_var_name = iterating_var_node['value']
            # iterating_var_type = iterating_var_node['type']
            # iterating_var_data_type = iterating_var_node['data_type']
            iterating_var_name = convert_array_iterator(iterating_var_node, True)

            # if var_data_type == "":
            #     var_data_type = iterating_var_data_type

            # var_list = var_list + iterating_var_list
            if var_name[:2] == "->":
                var_name = "." + var_name[2:]
            var_name = iterating_var_name + var_name
            # if iterating_var_type == "DeclRefExpr":
            #     iterating_var_ref_type = iterating_var_node['ref_type']
            #     if iterating_var_ref_type in ["VarDecl", "ParmVarDecl"]:
            #         var_list.append((iterating_var_name, iterating_var_data_type))
            #         if var_name[:2] == "->":
            #             var_name = "." + var_name[2:]
            #         var_name = "[" + iterating_var_name + "]" + var_name
        elif child_node_type == "ParenExpr":
            param_node = child_node['children'][0]
            param_node_type = param_node['type']
            param_node_var_name = ""
            param_node_aux_list = list()
            if param_node_type == "MemberExpr":
                param_node_var_name = convert_member_expr(param_node, True)
            elif param_node_type == "CStyleCastExpr":
                param_node_var_name = convert_cast_expr(param_node, True)
            var_list = var_list + param_node_aux_list
            var_name = "(" + param_node_var_name + ")" + var_name
            break
        elif child_node_type == "CStyleCastExpr":
            cast_var_name, cast_data_type = convert_cast_expr(child_node, True)
            # var_list = var_list + cast_node_aux_list
            var_name = cast_var_name + var_name
            break
        elif child_node_type == "MemberExpr":
            child_node_value = child_node['value']
            # var_data_type = str(child_node['data_type'])
            if "isArrow" not in child_node.keys():
                var_name = "." + str(child_node_value.split(":")[-1]) + var_name
            else:
                var_name = "->" + str(child_node_value.split(":")[-1]) + var_name
        elif child_node_type == "CallExpr":
            child_var_name = convert_call_expr(child_node, True)
            # var_list = var_list + child_aux_list
            var_name = child_var_name + var_name
            break

        else:
            print(ast_node)
            error_exit("unhandled exception at membership expr -> str")
        if len(child_node['children']) > 0:
            child_node = child_node['children'][0]
        else:
            child_node = None
    if only_string:
        return var_name
    return var_name, var_data_type, var_list


def convert_poc_to_ktest(poc_path, ktest_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    concrete_file = open(poc_path, 'rb')
    bit_size = os.fstat(concrete_file.fileno()).st_size
    convert_command = SYMBOLIC_CONVERTER + " --sym-file " + poc_path
    execute_command(convert_command)
    move_command = "mv file.bout " + ktest_path
    execute_command(move_command)
    return bit_size


def convert_binary_to_llvm(binary_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    binary_name = str(binary_path).split("/")[-1]
    binary_directory = "/".join(str(binary_path).split("/")[:-1])
    remove_command = "rm " + binary_path + ".bc"
    # print(remove_command)
    execute_command(remove_command)
    extract_command = BINARY_CONVERTER + " " + binary_path
    # print(extract_command)
    execute_command(extract_command)
    return binary_directory, binary_name


def convert_node_to_str(ast_node):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    node_str = ""
    node_type = str(ast_node['type'])
    if node_type in ["DeclStmt", "DeclRefExpr", "VarDecl"]:
        node_str = str(ast_node['value'])
    if str(ast_node['type']) == "BinaryOperator":
        operator = str(ast_node['value'])
        right_operand = convert_node_to_str(ast_node['children'][1])
        left_operand = convert_node_to_str(ast_node['children'][0])
        return left_operand + " " + operator + " " + right_operand
    return node_str


def convert_macro_list_to_dict(string_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    macro_list = dict()
    for macro_def in string_list:
        macro_name = str(macro_def).split(" ")[1]
        macro_name = macro_name.split("(")[0]
        macro_list[macro_name] = macro_def
    return macro_list
