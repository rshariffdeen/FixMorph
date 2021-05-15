# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import pickle
import shutil
from app.tools import emitter, logger
from app.common import definitions, values


def id_from_string(simplestring):
    return int(simplestring.split("(")[-1][:-1])


def get_id(node_ref):
    return int(node_ref.split("(")[-1][:-1])


def get_type(node_ref):
    return node_ref.split("(")[0]


def inst_comp(i):
    return definitions.order.index(i)


def execute_command(command, show_output=True):
    # Print executed command and execute it in console
    emitter.command(command)
    command = "{ " + command + " ;} 2> " + definitions.FILE_ERROR_LOG
    if not show_output:
        command += " > /dev/null"
    # print(command)
    process = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    (output, error) = process.communicate()
    # out is the output of the command, and err is the exit value
    return str(process.returncode)


def save_current_state():
    pickle.dump(values.Project_A, open(definitions.FILE_PROJECT_A, 'wb'))
    pickle.dump(values.Project_B, open(definitions.FILE_PROJECT_B, 'wb'))
    pickle.dump(values.Project_C, open(definitions.FILE_PROJECT_C, 'wb'))
    pickle.dump(values.Project_D, open(definitions.FILE_PROJECT_D, 'wb'))

    segment_state = [values.IS_STRUCT, values.IS_ENUM, values.IS_MACRO, values.IS_TYPEDEC, values.IS_FUNCTION]
    pickle.dump(segment_state, open(definitions.FILE_SEGMENT_STATE, 'wb'))
    pickle.dump(values.data_type_map, open(definitions.FILE_DATATYPE_MAP, 'wb'))
    pickle.dump(values.map_namespace_global, open(definitions.FILE_VAR_MAP_STORE, 'wb'))
    pickle.dump(values.VECTOR_MAP, open(definitions.FILE_VEC_MAP_STORE, 'wb'))
    pickle.dump(values.SOURCE_MAP, open(definitions.FILE_SOURCE_MAP_STORE, 'wb'))
    pickle.dump(values.missing_header_list, open(definitions.FILE_MISSING_HEADERS, 'wb'))
    pickle.dump(values.missing_macro_list, open(definitions.FILE_MISSING_MACROS, 'wb'))
    pickle.dump(values.missing_function_list, open(definitions.FILE_MISSING_FUNCTIONS, 'wb'))
    pickle.dump(values.missing_data_type_list, open(definitions.FILE_MISSING_TYPES, 'wb'))


def load_state():
    values.Project_A = pickle.load(open(definitions.FILE_PROJECT_A, 'rb'))
    values.Project_B = pickle.load(open(definitions.FILE_PROJECT_B, 'rb'))
    values.Project_C = pickle.load(open(definitions.FILE_PROJECT_C, 'rb'))
    values.Project_D = pickle.load(open(definitions.FILE_PROJECT_D, 'rb'))
    values.map_namespace_global = pickle.load(open(definitions.FILE_VAR_MAP_STORE, 'rb'))
    values.VECTOR_MAP = pickle.load(open(definitions.FILE_VEC_MAP_STORE, 'rb'))
    values.SOURCE_MAP = pickle.load(open(definitions.FILE_SOURCE_MAP_STORE, 'rb'))
    values.missing_function_list = pickle.load(open(definitions.FILE_MISSING_FUNCTIONS, 'rb'))
    values.missing_data_type_list = pickle.load(open(definitions.FILE_MISSING_TYPES, 'rb'))
    values.missing_macro_list = pickle.load(open(definitions.FILE_MISSING_MACROS, 'rb'))
    values.missing_header_list = pickle.load(open(definitions.FILE_MISSING_HEADERS, 'rb'))
    values.data_type_map = pickle.load(open(definitions.FILE_DATATYPE_MAP, 'rb'))
    segment_state = pickle.load(open(definitions.FILE_SEGMENT_STATE, 'rb'))
    values.IS_STRUCT = segment_state[0]
    values.IS_ENUM = segment_state[1]
    values.IS_MACRO = segment_state[2]
    values.IS_TYPEDEC = segment_state[3]
    values.IS_FUNCTION = segment_state[4]


def error_exit(*args):
    emitter.error("Transformation Failed")
    for arg in args:
        emitter.error(str(arg))
    raise Exception("Error. Exiting...")


def find_files(src_path, extension, output, regex):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # Save paths to all files in src_path with extension extension to output
    find_command = "find " + src_path + " -name '" + extension + "' "
    if regex is not None:
        find_command += " | grep '" + regex + "' "
    find_command += " > " + output
    execute_command(find_command)


def find_file_using_path(src_path, partial_path, output, regex):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # Save paths to all files in src_path with extension extension to output
    find_command = "find " + src_path + " -path '" + partial_path + "' "
    if regex is not None:
        find_command += " | grep '" + regex + "' "
    find_command += " > " + output
    execute_command(find_command)


def clean_files():
    # Remove other residual files stored in ./output/
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.information("Removing other residual files...")
    definitions.FILE_COMPARISON_RESULT = definitions.DIRECTORY_OUTPUT + "/comparison-result"
    definitions.FILE_TRANSPLANT_DIFF = definitions.DIRECTORY_OUTPUT + "/transplant-diff"
    definitions.FILE_PORT_N = definitions.DIRECTORY_OUTPUT + "/n-port"
    definitions.FILE_TRANS_N = definitions.DIRECTORY_OUTPUT + "/n-trans"
    definitions.FILE_ORIG_N = definitions.DIRECTORY_OUTPUT + "/n-orig"

    if os.path.isfile(definitions.FILE_COMPARISON_RESULT):
        os.remove(definitions.FILE_COMPARISON_RESULT)
    if os.path.isfile(definitions.FILE_ORIG_N):
        os.remove(definitions.FILE_ORIG_N)
    if os.path.isfile(definitions.FILE_PORT_N):
        os.remove(definitions.FILE_PORT_N)
    if os.path.isfile(definitions.FILE_TRANS_N):
        os.remove(definitions.FILE_TRANS_N)
    if os.path.isfile(definitions.FILE_TRANSPLANT_DIFF):
        os.remove(definitions.FILE_TRANSPLANT_DIFF)


def get_file_extension_list(src_path, output_file_name):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    extensions = set()
    find_command = "find " + src_path + " -type f -not -name '*\.c' -not -name '*\.h'" + \
        " > " + output_file_name
    execute_command(find_command)
    with open(output_file_name, 'r') as f:
        a = f.readline().strip()
        while(a):
            a = a.split("/")[-1]
            if "." in a:
                extensions.add("*." + a.split(".")[-1])
            else:
                extensions.add(a)
            a = f.readline().strip()
    return extensions


def backup_file(file_path, backup_name):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    backup_command = "cp " + file_path + " " + definitions.DIRECTORY_BACKUP + "/" + backup_name
    execute_command(backup_command)


def restore_file(file_path, backup_name):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    restore_command = "cp " + definitions.DIRECTORY_BACKUP + "/" + backup_name + " " + file_path
    execute_command(restore_command)


def reset_git(source_directory):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    reset_command = "cd " + source_directory + ";git reset --hard HEAD"
    execute_command(reset_command)


def show_partial_diff(source_path_a, source_path_b):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.highlight("\tTransplanted Code")
    output_file = definitions.FILE_PARTIAL_PATCH
    diff_command = "diff -ENZBbwr "
    if values.DEFAULT_OUTPUT_FORMAT == "unified":
        diff_command += " -u "
    diff_command += source_path_a + " " + source_path_b + " > " + output_file
    execute_command(diff_command)
    with open(output_file, 'r', encoding='utf8', errors="ignore") as diff_file:
        diff_line = diff_file.readline().strip()
        while diff_line:
            emitter.special("\t\t\t" + diff_line)
            diff_line = diff_file.readline().strip()


def is_intersect(start_a, end_a, start_b, end_b):
    return not (end_b < start_a or start_b > end_a)


def clear_values(project):
    project.header_list = dict()
    project.function_list = dict()
    project.struct_list = dict()
    project.macro_list = dict()
    project.def_list = dict()
    project.enum_list = dict()


def get_file_list(dir_name):
    current_file_list = os.listdir(dir_name)
    full_list = list()
    for entry in current_file_list:
        full_path = os.path.join(dir_name, entry)
        if os.path.isdir(full_path):
            full_list = full_list + get_file_list(full_path)
        else:
            full_list.append(full_path)
    return full_list


def get_code(source_path, line_number):
    if os.path.exists(source_path):
        with open(source_path, 'r', encoding='utf8', errors="ignore") as source_file:
            content = source_file.readlines()
            # print(len(content))
            return content[line_number-1]
    return None


def get_code_range(source_path, start_line, end_line):
    if os.path.exists(source_path):
        with open(source_path, 'r', encoding='utf8', errors="ignore") as source_file:
            content = source_file.readlines()
            # print(len(content))
            return content[start_line-1:end_line]
    return None


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
    return [node1.strip(), node2.strip()]


def is_intersect(start, end, start2, end2):
    return not (end2 < start or start2 > end)


def backup_file_orig(file_path):
    # backup_command = "cp " + file_path + " " + file_path + ".orig"
    if os.path.isfile(file_path):
        shutil.copyfile(file_path, file_path + ".orig")
    # os.system(backup_command)
    # execute_command(backup_command)


def replace_file(file_a, file_b):
    # replace_command = "cp " + file_a + " " + file_b
    # os.system(replace_command)
    if os.path.isfile(file_a):
        shutil.copyfile(file_a, file_b)
    # execute_command(replace_command)


def restore_file_orig(file_path):
    # restore_command = "cp " + file_path + ".orig " + file_path
    # os.system(restore_command)
    if os.path.isfile(file_path + ".orig"):
        shutil.copyfile(file_path + ".orig", file_path)
    # execute_command(restore_command)


def get_source_name_from_slice(slice_path):
    if ".c." in slice_path:
        source_path = slice_path.split(".c.")[0] + ".c"
    else:
        source_path = slice_path.split(".h.")[0] + ".h"
    return source_path


def get_identifier_from_slice(slice_path):
    if ".c." in slice_path:
        source_path, segment = slice_path.split(".c.")
    else:
        source_path, segment = slice_path.split(".h.")

    segment_identifier = segment.replace(".slice", "").split(".")[1]
    return segment_identifier


def shift_per_slice(slice_file):
    vector_source = get_source_name_from_slice(slice_file)
    backup_file_orig(vector_source)
    replace_file(slice_file, vector_source)


def shift_slice_source(slice_file_a, slice_file_c):
    values.current_slice_tuple = slice_file_a, slice_file_c
    slice_file_b = slice_file_a.replace(values.CONF_PATH_A, values.Project_B.path)
    slice_file_d = slice_file_c.replace(values.CONF_PATH_C, values.Project_D.path)
    shift_per_slice(slice_file_a)
    shift_per_slice(slice_file_b)
    shift_per_slice(slice_file_c)
    shift_per_slice(slice_file_d)

    # vector_source_a = get_source_name_from_slice(slice_file_a)
    # vector_source_b = vector_source_a.replace(values.CONF_PATH_A, values.Project_B.path)
    # vector_source_c = get_source_name_from_slice(slice_file_c)
    # vector_source_d = vector_source_c.replace(values.CONF_PATH_C, values.Project_D.path)
    #
    # backup_file_orig(vector_source_a)
    # backup_file_orig(vector_source_b)
    # backup_file_orig(vector_source_c)
    # backup_file_orig(vector_source_d)
    # replace_file(slice_file_a, vector_source_a)
    # replace_file(slice_file_b, vector_source_b)
    # replace_file(slice_file_c, vector_source_c)
    # replace_file(slice_file_d, vector_source_d)


def restore_per_slice(slice_file):
    vector_source = get_source_name_from_slice(slice_file)
    restore_file_orig(vector_source)


def restore_slice_source():
    if values.current_slice_tuple:
        slice_file_a, slice_file_c = values.current_slice_tuple
        slice_file_b = slice_file_a.replace(values.CONF_PATH_A, values.Project_B.path)
        slice_file_d = slice_file_c.replace(values.CONF_PATH_C, values.Project_D.path)
        restore_per_slice(slice_file_a)
        restore_per_slice(slice_file_b)
        restore_per_slice(slice_file_c)
        restore_per_slice(slice_file_d)

        # vector_source_a = get_source_name_from_slice(slice_file_a)
        # vector_source_b = vector_source_a.replace(values.CONF_PATH_A, values.Project_B.path)
        # vector_source_c = get_source_name_from_slice(slice_file_c)
        # vector_source_d = vector_source_c.replace(values.CONF_PATH_C, values.Project_D.path)

        # restore_file_orig(vector_source_a)
        # restore_file_orig(vector_source_b)
        # restore_file_orig(vector_source_c)
        # restore_file_orig(vector_source_d)


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


def generate_map_gumtree(file_a, file_b, output_file):
    name_a = file_a.split("/")[-1]
    name_b = file_b.split("/")[-1]
    emitter.normal("\tsource: " + file_a)
    emitter.normal("\ttarget: " + file_b)
    emitter.normal("\tgenerating ast map")
    try:
        extra_arg = ""
        if file_a[-1] == 'h':
            extra_arg = " --"
        generate_command = definitions.DIFF_COMMAND + " -s=" + definitions.DIFF_SIZE + " -dump-matches "
        if values.DONOR_REQUIRE_MACRO:
            generate_command += " " + values.DONOR_PRE_PROCESS_MACRO + " "
            if values.CONF_PATH_B in file_b:
                generate_command += " " + values.DONOR_PRE_PROCESS_MACRO.replace("--extra-arg-a", "--extra-arg-c") + " "
        if values.TARGET_REQUIRE_MACRO:
            if values.CONF_PATH_C in file_b:
                generate_command += " " + values.TARGET_PRE_PROCESS_MACRO + " "
        generate_command += file_a + " " + file_b + extra_arg + " 2> output/errors_clang_diff "
        # command += "| grep '^Match ' "
        generate_command += " > " + output_file
        execute_command(generate_command, False)
    except Exception as e:
        error_exit(e, "Unexpected fail at generating map: " + output_file)