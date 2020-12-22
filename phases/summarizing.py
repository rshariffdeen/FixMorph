#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import sys
import os
import io
import json
from git import Repo
from common.utilities import execute_command, error_exit, save_current_state, load_state
from common import definitions, values
from ast import ast_vector, ast_parser
import difflib
from tools import logger, emitter, identifier, writer, generator, solver, differ, merger

FILE_EXCLUDED_EXTENSIONS = ""
FILE_EXCLUDED_EXTENSIONS_A = ""
FILE_EXCLUDED_EXTENSIONS_B = ""
FILE_DIFF_C = ""
FILE_DIFF_H = ""
FILE_DIFF_ALL = ""
FILE_AST_SCRIPT = ""
FILE_AST_DIFF_ERROR = ""

ported_diff_info = dict()
original_diff_info = dict()
transplanted_diff_info = dict()


def analyse_source_diff(path_a, path_b):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    differ.diff_files(definitions.FILE_DIFF_ALL,
                      definitions.FILE_DIFF_C,
                      definitions.FILE_DIFF_H,
                      definitions.FILE_EXCLUDED_EXTENSIONS_A,
                      definitions.FILE_EXCLUDED_EXTENSIONS_B,
                      definitions.FILE_EXCLUDED_EXTENSIONS,
                      path_a,
                      path_b)

    emitter.sub_sub_title("analysing untracked files")
    untracked_file_list = generator.generate_untracked_file_list(definitions.FILE_EXCLUDED_EXTENSIONS, path_a)
    emitter.sub_sub_title("analysing header files")
    diff_h_file_list = differ.diff_h_files(definitions.FILE_DIFF_H, path_a, untracked_file_list)
    emitter.sub_sub_title("analysing C/CPP source files")
    diff_c_file_list = differ.diff_c_files(definitions.FILE_DIFF_C, path_b, untracked_file_list)
    emitter.sub_sub_title("analysing changed code lines")
    diff_info_c = differ.diff_line(diff_c_file_list, definitions.FILE_TEMP_DIFF)
    diff_info_h = differ.diff_line(diff_h_file_list, definitions.FILE_TEMP_DIFF)
    diff_info = merger.merge_diff_info(diff_info_c, diff_info_h)
    return diff_info


def analyse_ast_diff(path_a, path_b, diff_info):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if not diff_info:
        error_exit("no files modified in diff")
    updated_diff_info = differ.diff_ast(diff_info,
                                        path_a,
                                        path_b,
                                        definitions.FILE_AST_SCRIPT)
    return updated_diff_info


def load_values():
    global FILE_DIFF_C, FILE_DIFF_H, FILE_DIFF_ALL
    global FILE_AST_SCRIPT, FILE_AST_DIFF_ERROR
    global FILE_EXCLUDED_EXTENSIONS, FILE_EXCLUDED_EXTENSIONS_A, FILE_EXCLUDED_EXTENSIONS_B
    definitions.FILE_ORIG_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/orig-diff-info"
    definitions.FILE_PORT_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/port-diff-info"
    definitions.FILE_TRANSPLANT_DIFF_INFO = definitions.DIRECTORY_OUTPUT + "/transplant-diff-info"
    definitions.FILE_ORIG_DIFF = definitions.DIRECTORY_OUTPUT + "/orig-diff"
    definitions.FILE_PORT_DIFF = definitions.DIRECTORY_OUTPUT + "/port-diff"
    definitions.FILE_TRANSPLANT_DIFF = definitions.DIRECTORY_OUTPUT + "/transplant-diff"



def save_values():
    writer.write_as_json(ported_diff_info, definitions.FILE_PORT_DIFF_INFO)
    writer.write_as_json(original_diff_info, definitions.FILE_ORIG_DIFF_INFO)
    writer.write_as_json(transplanted_diff_info, definitions.FILE_TRANSPLANT_DIFF_INFO)
    file_list_a = set()
    file_list_c = set()
    for path_a in original_diff_info:
        path_a = path_a.split(":")[0]
        file_list_a.add(path_a)
    for path_a in file_list_a:
        path_b = path_a.replace(values.Project_A.path, values.Project_B.path)
        diff_command = "diff -ENZBbwr " + path_a + " " + path_b + " >> " + definitions.FILE_ORIG_DIFF
        execute_command(diff_command)
    for path_c in ported_diff_info:
        path_c = path_c.split(":")[0]
        file_list_c.add(path_c)
    for path_c in file_list_c:
        path_e = path_c.replace(values.Project_C.path, values.Project_E.path)
        diff_command = "diff -ENZBbwr " + path_c + " " + path_e + " >> " + definitions.FILE_PORT_DIFF
        execute_command(diff_command)

    for path_c in file_list_c:
        path_d = path_c.replace(values.Project_C.path, values.Project_D.path)
        diff_command = "diff -ENZBbwr " + path_c + " " + path_d + " >> " + definitions.FILE_TRANSPLANT_DIFF
        execute_command(diff_command)
    save_current_state()


def clear_values(project):
    project.header_list = dict()
    project.function_list = dict()
    project.struct_list = dict()
    project.macro_list = dict()
    project.def_list = dict()
    project.enum_list = dict()


def safe_exec(function_def, title, *args):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    emitter.sub_title(title)
    description = title[0].lower() + title[1:]
    try:
        logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def get_source_line_numbers(path_a):
    number_list = list()
    if values.CONF_PATH_A in path_a:
        path_b = path_a.replace(values.CONF_PATH_A, values.CONF_PATH_B)
    else:
        path_b = path_a.replace(values.CONF_PATH_C, values.CONF_PATH_E)

    file_a = open(path_a, "rt").readlines()
    file_b = open(path_b, "rt").readlines()
    differ = difflib.Differ()
    diff_list = differ.compare(file_a, file_b)

    # TODO: implement to get the changed line numbers

    return number_list


def get_ast_line_numbers(file_path):
    number_list = list()
    return number_list


def get_ast_json(file_path):
    json_file = file_path + ".AST"
    dump_command = "crochet-diff -ast-dump-json " + file_path
    if file_path[-1] == 'h':
        dump_command += " --"
    error_file = definitions.DIRECTORY_OUTPUT + "/errors_AST_dump"
    dump_command += " 2> " + error_file + " > " + json_file
    if os.stat(json_file).st_size == 0:
        return None
    with io.open(json_file, 'r', encoding='utf8', errors="ignore") as f:
        ast_json = json.loads(f.read())
    return ast_json['root']


def get_variable_list(path_a):
    var_list = list()
    if values.CONF_PATH_A in path_a:
        path_b = path_a.replace(values.CONF_PATH_A, values.CONF_PATH_B)
    else:
        path_b = path_a.replace(values.CONF_PATH_C, values.CONF_PATH_E)

    ast_script = get_ast_script(path_a, path_b)
    ast_a = get_ast_json(path_a)
    ast_b = get_ast_json(path_b)


    return var_list


def get_macro_list():
    macro_list = list()
    return macro_list


def get_header_files():
    file_list = list()
    return file_list


def get_function_call_list():
    call_list = list()
    return call_list


def get_ast_script(source_a, source_b):
    ast_script = list()
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    generate_command = "crochet-diff "
    generate_command += source_a + " " + source_b
    if source_a[-1] == 'h':
        generate_command += " --"
    generate_command += " > " + definitions.FILE_AST_SCRIPT
    execute_command(generate_command, False)
    with open(definitions.FILE_AST_SCRIPT, "r") as script_file:
        ast_script = script_file.readlines()
    return ast_script


def get_diff_files(project_path):
    repo = Repo(project_path)
    patch_commit = repo.head.commit
    parent_commit = patch_commit.parents[0]
    diff_list = parent_commit.diff(patch_commit)
    file_list = list()
    for diff in diff_list:
        file_list.append(project_path + "/" + diff.a_path)
    return file_list


def is_file_path_change(file_list_a, file_list_b, project_path_a, project_path_b):
    relative_path_list_a = set()
    relative_path_list_b = set()
    for path_a in file_list_a:
        relative_path_list_a.add(path_a.replace(project_path_a, ""))
    for path_b in file_list_b:
        relative_path_list_b.add(path_b.replace(project_path_b, ""))
    return not (relative_path_list_b == relative_path_list_a)


# check if AST is covering all the changes (check for macros in play)
def is_coverage(file_list_a, file_list_b):
    for file_path in file_list_a:
        source_line_numbers = get_source_line_numbers(file_path)
        ast_line_numbers = get_ast_line_numbers(file_path)
        if ast_line_numbers != source_line_numbers:
            return False
    for file_path in file_list_b:
        source_line_numbers = get_source_line_numbers(file_path)
        ast_line_numbers = get_ast_line_numbers(file_path)
        if ast_line_numbers != source_line_numbers:
            return False
    return True


def has_namespace_changed(file_list_a, file_list_b):
    var_list_a = list()
    var_list_b = list()
    for file_path in file_list_a:
        var_list = get_variable_list(file_path)
        var_list_a = var_list_a + var_list
    var_list_a = set(var_list_a)
    for file_path in file_list_b:
        var_list = get_variable_list(file_path)
        var_list_b = var_list_b + var_list
    var_list_b = set(var_list_b)
    return not (var_list_a == var_list_b)


def get_summary_of_ast_transformation(ast_script_list):
    summary_info_list = dict()
    for file_path in ast_script_list:
        summary_info = dict()
        ast_script = ast_script_list[file_path]
        for ast_action in ast_script:
            if "Insert" in ast_action:
                transformation = "Insert"
                node_type = ast_action.split(" ")[1].split("(")[0]
                if transformation not in summary_info:
                    summary_info[transformation] = dict()
                    summary_info[transformation]["count"] = 0
                    summary_info[transformation]["list"] = dict()
                summary_info[transformation]["count"] = summary_info[transformation]["count"] + 1
                if node_type not in summary_info[transformation]["list"]:
                    summary_info[transformation]["list"][node_type] = 0
                summary_info[transformation]["list"][node_type] = summary_info[transformation]["list"][node_type] + 1

            elif "Update" in ast_action:
                transformation = "Update"
                node_type = ast_action.split(" ")[1].split("(")[0]
                if transformation not in summary_info:
                    summary_info[transformation] = dict()
                    summary_info[transformation]["count"] = 0
                    summary_info[transformation]["list"] = dict()
                summary_info[transformation]["count"] = summary_info[transformation]["count"] + 1
                if node_type not in summary_info[transformation]["list"]:
                    summary_info[transformation]["list"][node_type] = 0
                summary_info[transformation]["list"][node_type] = summary_info[transformation]["list"][node_type] + 1
            else:
                print(ast_script)
                error_exit("Unimplemented section in summarizing ast")
        summary_info_list[file_path] = summary_info
    return summary_info_list


def compare_ast_summaries(summary_a, summary_b):
    if summary_a == summary_b:
        return False, False, list()
    is_yield = False
    is_prune = False
    summary_list = list()

    for transformation in summary_a:
        count_a = int(summary_a[transformation]['count'])
        count_b = int(summary_b[transformation]['count'])
        if count_a < count_b:
            is_prune = True
        if count_a > count_b:
            is_yield = True
        node_list_a = summary_a[transformation]['list']
        node_list_b = summary_b[transformation]['list']
        node_type_list = list(set(node_list_a.keys() + node_list_b.keys()))
        for node_type in node_type_list:
            if node_type not in node_list_b:
                    summary_list.append("Pruning of " + str(node_type))
            elif node_type not in node_list_a:
                    summary_list.append("Addition of " + str(node_type))
            else:
                node_count_a = node_list_a[node_type]
                node_count_b = node_list_b[node_type]
                if node_count_a < node_count_b:
                    summary_list.append("Addition of " + str(node_type))
                else:
                    summary_list.append("Pruning of " + str(node_type))

    return is_yield, is_prune, summary_list


def has_patch_evolved(file_list_b, file_list_x, path_b, path_x, source_map):
    yielded = False
    pruned = False
    ast_script_list_b = dict()
    ast_script_list_x = dict()
    summary_ast_list = list()
    for file_path_b in file_list_b:
        file_path_a = file_path_b.replace(path_b, values.CONF_PATH_A)
        ast_script_b = get_ast_script(file_path_a, file_path_b)
        ast_script_list_b[file_path_b] = ast_script_b

    for file_path_x in file_list_x:
        file_path_c = file_path_x.replace(path_x, values.CONF_PATH_C)
        ast_script_x = get_ast_script(file_path_c, file_path_x)
        ast_script_list_x[file_path_x] = ast_script_x
    # print(ast_script_list_b)
    # print(ast_script_list_x)

    summary_ast_list_b = get_summary_of_ast_transformation(ast_script_list_b)
    # print(summary_ast_list_b)

    summary_ast_list_x = get_summary_of_ast_transformation(ast_script_list_x)
    # print(summary_ast_list_x)
    for file_b in summary_ast_list_b:
        summary_b = summary_ast_list_b[file_b]
        file_x = source_map[file_b]
        summary_x = summary_ast_list_x[file_x]
        comparison = compare_ast_summaries(summary_b, summary_x)
        any_yield, any_prune, summary = comparison
        yielded = yielded or any_yield
        pruned = pruned or any_prune
        summary_ast_list = summary_ast_list + summary

    return yielded, pruned, summary_ast_list


def extract_header_files(file_path):
    result_file = definitions.DIRECTORY_TMP + "/headers"
    extract_command = "cat " + file_path + " | grep '#include' > " + result_file
    execute_command(extract_command)
    with open(result_file, "r") as result_file:
        header_list = result_file.readlines()
        return header_list


def check_header_files(file_mapping, path_x):
    is_yielded = False
    is_pruned = False
    summary_list = list()
    for file_b in file_mapping:
        file_x = file_mapping[file_b]
        if file_b[-1] == "c":
            file_a = file_b.replace(values.CONF_PATH_B, values.CONF_PATH_A)
            header_list_a = extract_header_files(file_a)
            header_list_b = extract_header_files(file_b)
            additional_header_list_b = list(set(header_list_b) - set(header_list_a))
            deleted_header_list_b = list(set(header_list_a) - set(header_list_b))
            file_c = file_x.replace(path_x, values.CONF_PATH_C)
            header_list_c = extract_header_files(file_c)
            header_list_x = extract_header_files(file_x)
            additional_header_list_x = list(set(header_list_x) - set(header_list_c))
            deleted_header_list_x = list(set(header_list_c) - set(header_list_x))

            if len(additional_header_list_b) < len(additional_header_list_x):
                header_file_list = list(set(additional_header_list_b) - set(additional_header_list_x))
                is_yielded = True
                for header_file in header_file_list:
                    summary_list.append("additional header file included in " + file_x + ":" + header_file)
            elif len(additional_header_list_b) > len(additional_header_list_x):
                is_pruned = True
                header_file_list = list(set(additional_header_list_x) - set(additional_header_list_b))
                for header_file in header_file_list:
                    summary_list.append("header file inclusion dropped in " + file_x + ":" + header_file)

            if len(deleted_header_list_b) < len(deleted_header_list_x):
                header_file_list = list(set(deleted_header_list_b) - set(deleted_header_list_x))
                is_yielded = True
                for header_file in header_file_list:
                    summary_list.append("additional header file removed in " + file_x + ":" + header_file)
            elif len(deleted_header_list_b) > len(deleted_header_list_x):
                is_pruned = True
                header_file_list = list(set(deleted_header_list_x) - set(deleted_header_list_b))
                for header_file in header_file_list:
                    summary_list.append("header file inclusion retained in " + file_x + ":" + header_file)

    return is_yielded, is_pruned, summary_list


def get_file_name_map(file_list_a, file_list_b):
    mapping = dict()
    for file_a in file_list_a:
        min_distance = 1000
        candidate_mapping = None
        for file_b in file_list_b:
            l_distance = solver.levenshtein_distance(file_a, file_b)
            if l_distance < min_distance:
                min_distance = l_distance
                candidate_mapping = file_b
        mapping[file_a] = candidate_mapping
    return mapping


def classify_porting(path_a, path_b):
    is_yielded = False
    is_pruned = False
    is_translated = False
    summary_list = list()

    orig_file_list = get_diff_files(path_a)
    ported_file_list = get_diff_files(path_b)
    map_file_list = get_file_name_map(orig_file_list, ported_file_list)
    is_path_change = is_file_path_change(orig_file_list, ported_file_list, path_a, path_b)
    print(is_path_change)

    # is_covered = is_coverage(orig_file_list, ported_file_list)
    # print(is_covered)

    evolution_result = has_patch_evolved(orig_file_list, ported_file_list, path_a, path_b, map_file_list)
    any_yield, any_prune, ast_summary = evolution_result
    print(any_yield, any_prune, ast_summary)
    is_yielded = is_yielded or any_yield
    is_pruned = is_pruned or any_prune
    summary_list = summary_list + ast_summary

    header_check_result = check_header_files(map_file_list, path_b)
    any_yield, any_prune, header_summary = header_check_result
    print(any_yield, any_prune, header_summary)
    is_yielded = is_yielded or any_yield
    is_pruned = is_pruned or any_prune
    summary_list = summary_list + header_summary

    is_translated = has_namespace_changed(orig_file_list, ported_file_list)
    print(is_translated)

    print(is_yielded, is_pruned, summary_list)


def segment_code(diff_info, project, out_file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.sub_sub_title("identifying modified definitions")
    identifier.identify_definition_segment(diff_info, project)
    emitter.sub_sub_title("identifying modified segments")
    identifier.identify_code_segment(diff_info, project, out_file_path)


def start():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global original_diff_info, ported_diff_info, transplanted_diff_info
    emitter.title("Ported Patch Analysis")
    load_values()

    if values.PHASE_SETTING[definitions.PHASE_SUMMARIZE]:
        if not values.CONF_PATH_E:
            emitter.special("\n\t-skipping this phase-")
        else:
            # classify_porting(Values.PATH_B, Values.Project_D.path)
            clear_values(values.Project_A)
            original_diff_info = safe_exec(analyse_source_diff, "analysing source diff of Original Patch",
                                           values.CONF_PATH_A, values.CONF_PATH_B)
            segment_code(original_diff_info, values.Project_A, definitions.FILE_ORIG_N)

            clear_values(values.Project_C)
            ported_diff_info = safe_exec(analyse_source_diff, "analysing source diff of Manual Ported Patch",
                                         values.CONF_PATH_C, values.CONF_PATH_E)
            segment_code(ported_diff_info, values.Project_C, definitions.FILE_PORT_N)

        save_values()
    else:
        emitter.special("\n\t-skipping this phase-")
