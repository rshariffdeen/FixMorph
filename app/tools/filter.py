#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from app.tools import merger, oracle
from app.tools import converter, emitter, finder, extractor, logger
from app.common import values
from app.common.utilities import error_exit
from app.ast import ast_generator
import collections


def filter_trace_list_by_loc(trace_list, estimate_loc):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\t\tfiltering trace based on estimation point")
    # print(trace_list)
    # print(estimate_loc)
    if estimate_loc is None:
        return trace_list
    source_path, line_number, count_instant = estimate_loc.split(":")
    count_instant = int(count_instant)
    estimate_loc = source_path + ":" + str(line_number)

    estimated_div_point = 0
    for n in range(0, len(trace_list), 1):
        if estimate_loc == trace_list[n]:
            if values.IS_BACKPORT:
                estimated_div_point = n
            else:
                estimated_div_point = n
                if count_instant == 1:
                    return trace_list[n:]
                else:
                    count_instant = count_instant - 1

    return trace_list[estimated_div_point:]


def filter_function_list_using_trace(source_function_map, trace_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\t\textracting function list from trace ...")
    trace_function_info = collections.OrderedDict()
    unique_trace_list = extractor.extract_unique_in_order(trace_list)
    for trace_line in unique_trace_list:
        source_path, line_number = str(trace_line).split(":")
        function_list = source_function_map[source_path]
        for function_name, begin_line, finish_line in function_list:
            if int(line_number) in range(begin_line, finish_line):
                function_id = source_path + ":" + function_name
                if function_id not in trace_function_info.keys():
                    trace_function_info[function_id] = dict()
                    trace_function_info[function_id]['start'] = begin_line
                    trace_function_info[function_id]['end'] = finish_line
                    trace_function_info[function_id]['last'] = int(line_number)
                    trace_function_info[function_id]['begin'] = int(line_number)
                    trace_function_info[function_id]['lines'] = list()
                    trace_function_info[function_id]['lines'].append(line_number)
                else:
                    if line_number not in trace_function_info[function_id]['lines']:
                        trace_function_info[function_id]['lines'].append(line_number)
                    if trace_function_info[function_id]['last'] < line_number:
                        trace_function_info[function_id]['last'] = line_number
                    if trace_function_info[function_id]['begin'] > line_number:
                        trace_function_info[function_id]['begin'] = line_number
                break

    # source_line_map = Extractor.extract_source_lines_from_trace(trace_list)
    # for source_path in source_line_map:
    #     # print(source_path)
    #     function_list = source_function_map[source_path]
    #     trace_line_list = source_line_map[source_path]
    #     for line_number in trace_line_list:
    #         order = 1
    #         for function_name, begin_line, finish_line in function_list:
    #             if line_number in range(begin_line, finish_line):
    #                 function_id = source_path + ":" + function_name
    #                 # print(function_id)
    #                 if function_id not in trace_function_info.keys():
    #                     trace_function_info[function_id] = dict()
    #                     trace_function_info[function_id]['start'] = begin_line
    #                     trace_function_info[function_id]['end'] = finish_line
    #                     trace_function_info[function_id]['last'] = int(line_number)
    #                     trace_function_info[function_id]['begin'] = int(line_number)
    #                     trace_function_info[function_id]['lines'] = list()
    #                     trace_function_info[function_id]['order'] = order
    #                     trace_function_info[function_id]['lines'].append(line_number)
    #                     order += 1
    #                 else:
    #                     if line_number not in trace_function_info[function_id]['lines']:
    #                         trace_function_info[function_id]['lines'].append(line_number)
    #                     if trace_function_info[function_id]['last'] < line_number:
    #                         trace_function_info[function_id]['last'] = line_number
    #                     if trace_function_info[function_id]['begin'] > line_number:
    #                         trace_function_info[function_id]['begin'] = line_number
    #                 break
    return trace_function_info


def filter_ast_script(ast_script, info_a, info_b, mapping_ba):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfiltering AST script by merging and grouping")
    source_path_a, line_range_a, ast_node_a = info_a
    source_path_b, line_range_b, ast_node_b = info_b
    filtered_ast_script = list()
    line_range_start_a, line_range_end_a = line_range_a
    line_numbers_a = set(range(int(line_range_start_a), int(line_range_end_a) + 1))
    if line_range_b is not None:
        line_range_start_b, line_range_end_b = line_range_b
        line_numbers_b = set(range(int(line_range_start_b), int(line_range_end_b) + 1))

    # print(ast_script)
    merged_ast_script = merger.merge_ast_script(ast_script, ast_node_a, ast_node_b, mapping_ba)
    if merged_ast_script is None:
        return None
    # print(merged_ast_script)
    for script_line in merged_ast_script:
        if "Insert" in script_line and line_range_b is not None:
            node_id_b = int(((script_line.split(" into ")[0]).split("(")[1]).split(")")[0])
            node_b = finder.search_ast_node_by_id(ast_node_b, node_id_b)
            node_type_b = node_b['type']
            node_line_start = int(node_b['start line'])
            node_line_end = int(node_b['end line']) + 1
            node_line_numbers = set(range(node_line_start, node_line_end))

            intersection = line_numbers_b.intersection(node_line_numbers)
            if intersection:
                filtered_ast_script.append(script_line)
        elif "Delete" in script_line:
            node_id_a = int((script_line.split("(")[1]).split(")")[0])
            node_a = finder.search_ast_node_by_id(ast_node_a, node_id_a)
            node_line_start = int(node_a['start line'])
            node_line_end = int(node_a['end line']) + 1
            node_line_numbers = set(range(node_line_start, node_line_end))
            intersection = line_numbers_a.intersection(node_line_numbers)
            if intersection:
                filtered_ast_script.append(script_line)
        elif "Replace" in script_line and line_range_b is not None:
            node_id_a = int(((script_line.split(" with ")[0]).split("(")[1]).split(")")[0])
            node_a = finder.search_ast_node_by_id(ast_node_a, node_id_a)
            node_line_start = int(node_a['start line'])
            node_line_end = int(node_a['end line']) + 1
            node_line_numbers = set(range(node_line_start, node_line_end))
            intersection = line_numbers_a.intersection(node_line_numbers)
            if intersection:
                filtered_ast_script.append(script_line)
    return filtered_ast_script


def filter_ast_script_by_skip_line(ast_script, ast_node_a, ast_node_b, skip_lines):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfiltering AST script using skip lines")
    filtered_ast_script = list()
    for script_line in ast_script:
        if "Insert" in script_line:
            node_id_b = int(((script_line.split(" into ")[0]).split("(")[1]).split(")")[0])
            node_b = finder.search_ast_node_by_id(ast_node_b, node_id_b)
            node_type_b = node_b['type']
            node_line_start = int(node_b['start line'])
            node_line_end = int(node_b['end line']) + 1
            target_node_type = str((script_line.split(" into ")[1]).split("(")[0])
            # print(node_line_start)
            if node_line_start in skip_lines:
                continue
            if node_type_b in ["IfStmt"]:
                body_node = node_b['children'][1]
                condition_node = node_b['children'][0]
                condition_node_start = condition_node['start line']
                condition_node_end = condition_node['end line']
                if str(body_node['type']) != "CompoundStmt":
                    if int(body_node['start line']) not in skip_lines:
                        filtered_ast_script.append(script_line)
                else:
                    count = 0
                    for child_node in body_node['children']:
                        if int(child_node['start line']) not in skip_lines:
                            count = count + 1
                    if count != 0:
                        filtered_ast_script.append(script_line)
            elif target_node_type in ["IfStmt"]:
                insert_position = int((script_line.split(" into ")[1]).split(" at ")[1])
                # print(insert_position)
                if insert_position == 0:
                    target_node = finder.search_node_by_loc(ast_node_b, node_line_start)
                    body_node = target_node['children'][1]
                    count = 0
                    for child_node in body_node['children']:
                        if int(child_node['start line']) not in skip_lines:
                            count = count + 1
                    if count != 0:
                        filtered_ast_script.append(script_line)
            else:
                filtered_ast_script.append(script_line)
        else:
            filtered_ast_script.append(script_line)
    return filtered_ast_script


def filter_ast_script_by_node_type(ast_script, ast_node_a, ast_node_b, trace_list, source_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.normal("\t\tfiltering AST script using node types")
    filtered_ast_script = list()
    for script_line in ast_script:
        if "Insert" in script_line:
            node_id_b = int(((script_line.split(" into ")[0]).split("(")[1]).split(")")[0])
            node_b = finder.search_ast_node_by_id(ast_node_b, node_id_b)
            node_type_b = node_b['type']
            target_node_id = int((((script_line.split(" into ")[1]).split(" at ")[0]).split("(")[1]).split(")")[0])
            target_node = finder.search_ast_node_by_id(ast_node_b, target_node_id)
            target_node_type = target_node['type']
            node_line_start = int(node_b['start line'])
            node_line_end = int(node_b['end line']) + 1
            # print(node_line_start)
            if node_type_b == "LabelStmt":
                continue
            elif node_type_b == "ReturnStmt":
                continue
            elif node_type_b == "NullStmt":
                continue
            elif node_type_b == "GotoStmt":
                continue
            elif node_type_b == "TypeLoc":
                continue
            elif node_type_b == "BreakStmt":
                continue
            elif node_type_b == "Macro":
                node_value = node_b['value']
                if "assert(" in node_value:
                    continue
                elif target_node_type == "TypeLoc":
                    if not oracle.is_node_in_function(ast_node_b, target_node):
                        continue
                    else:
                        filtered_ast_script.append(script_line)
                else:
                    filtered_ast_script.append(script_line)
            elif node_type_b == "IfStmt":
                body_node = node_b['children'][1]
                count = 0
                if str(body_node['type']) != "CompoundStmt":
                    line_number = int(body_node['start line'])
                    source_loc = source_path + ":" + str(line_number)
                    if source_loc in trace_list:
                        filtered_ast_script.append(script_line)
                else:
                    for child_node in body_node['children']:
                        line_number = int(child_node['start line'])
                        source_loc = source_path + ":" + str(line_number)
                        if source_loc in trace_list:
                            count = count + 1
                    if count != 0:
                        filtered_ast_script.append(script_line)
            else:
                filtered_ast_script.append(script_line)
        else:
            filtered_ast_script.append(script_line)
    return filtered_ast_script


def filter_best_candidate_function(function_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    best_candidate = None
    if not function_list:
        emitter.error("No candidate function")
        error_exit("no suitable function to insert")
    # min_order = 1000
    # for function_id in function_list:
    #     info = function_list[function_id]
    #     order = info['order']
    #     if min_order > order:
    #         min_order = order
    #         best_candidate = function_id
    return function_list.keys()[0]


def filter_best_candidate_loc(loc_list, best_score):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    best_candidate = 0
    for loc in loc_list:
        # print(loc)
        score = loc_list[loc]
        if score == best_score:
            if best_candidate == 0:
                best_candidate = int(loc)
            else:
                if best_candidate > loc:
                    best_candidate = int(loc)
    return best_candidate


def filter_line_range(initial_range, skip_list):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_loc, end_loc = initial_range
    filtered_start = start_loc
    filtered_end = end_loc
    for num in range(start_loc, end_loc + 1, 1):
        if num in skip_list:
            continue
        else:
            filtered_start = num
            break

    for num in range(end_loc, start_loc - 1, -1):
        if num in skip_list:
            continue
        else:
            filtered_end = num
            break

    # print(filtered_start, filtered_end)
    return filtered_start, filtered_end


def filter_new_variables(var_map, ast_node_a, ast_node_b):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    filtered_map = dict()
    dec_node_list_a = extractor.extract_decl_node_list(ast_node_a)
    dec_node_list_b = extractor.extract_decl_node_list(ast_node_b)
    for var_name in var_map:
        if (var_name in dec_node_list_b.keys()) and (var_name not in dec_node_list_a.keys()):
            continue
        filtered_map[var_name] = var_map[var_name]
    return filtered_map


def filter_namespace_map(namespace_map, edit_script, source_b):
    filtered_namespace_map = dict()
    ast_tree_b = ast_generator.get_ast_json(source_b, values.DONOR_REQUIRE_MACRO, True)
    node_list = list()
    # print(namespace_map)
    for transformation_rule in edit_script:
        if "Insert" in transformation_rule:
            node_b_str = transformation_rule.split(" ")[1]
        elif "Update" in transformation_rule:
            node_b_str = transformation_rule.split(" ")[-1]
        elif "Replace" in transformation_rule:
            node_b_str = transformation_rule.split(" ")[-1]
        else:
            continue
        node_b_id = int(node_b_str.split("(")[-1].split(")")[0])
        node_b = finder.search_ast_node_by_id(ast_tree_b, node_b_id)
        node_type = node_b['type']
        if node_type in values.map_allow_type_list:
            node_list.append(node_b)
        ref_node_list = extractor.extract_reference_node_list(node_b)
        for ref_node in ref_node_list:
            ref_node_type = ref_node['type']
            if ref_node_type in values.map_allow_type_list:
                node_list.append(ref_node)

    for node in node_list:
        node_type = node['type']
        node_value = converter.get_node_value(node)

        if node_value:
            if node_type in ["MemberExpr", "FieldDecl"]:
                node_value = "." + node_value
            elif node_type in ["LabelStmt", "GotoStmt"]:
                node_value = node_value + "."
            elif node_type == "DeclRefExpr":
                if "ref_type" in node:
                    if node['ref_type'] == "FunctionDecl":
                        node_value = node_value + "("
            elif node_type == "Macro":
                if "(" in node_value:
                    node_value = node_value.split("(")[0] + "("
            if node_value in namespace_map:
                mapped_value = namespace_map[node_value]
                if "." not in node_value and "." in mapped_value:
                    mapped_value = mapped_value[1:]
                filtered_namespace_map[node_value] = mapped_value
                if node_type in ["MemberExpr", "FieldDecl"]:
                    struct_node = node
                    while struct_node['type'] != "DeclRefExpr":
                        field_name_b = node['value'].replace(":", ".")
                        if field_name_b in namespace_map:
                            field_name_c = namespace_map[field_name_b]
                            filtered_namespace_map[field_name_b] = field_name_c
                        if 'children' not in struct_node.keys() or len(struct_node['children']) == 0:
                            break
                        struct_node = struct_node['children'][0]
            else:
                if node_type in ["MemberExpr", "FieldDecl"]:
                    struct_node = node['children'][0]
                    while struct_node['type'] != "DeclRefExpr":
                        struct_node = struct_node['children'][0]
                        if 'children' not in struct_node:
                            break
                    if "data_type" in struct_node:
                        struct_name = struct_node['data_type'].replace("struct ", "").split(" ")[0]
                        node_value = "." + struct_name + node['value'].replace(":", ".")
                        if node_value in namespace_map:
                            field_name_c = "." + namespace_map[node_value].split(".")[-1]
                            field_name_b = "." + node_value.split(".")[-1]
                            filtered_namespace_map[field_name_b] = field_name_c

    # print(filtered_namespace_map)
    return filtered_namespace_map
