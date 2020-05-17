# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import pickle
from tools import Logger, Emitter, Writer, Reader
from common import Definitions, Values


def execute_command(command, show_output=True):
    # Print executed command and execute it in console
    Emitter.command(command)
    command = "{ " + command + " ;} 2> " + Definitions.FILE_ERROR_LOG
    if not show_output:
        command += " > /dev/null"
    # print(command)
    process = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    (output, error) = process.communicate()
    # out is the output of the command, and err is the exit value
    return str(process.returncode)


def save_current_state():
    pickle.dump(Values.Project_A, open(Definitions.FILE_PROJECT_A, 'wb'))
    pickle.dump(Values.Project_B, open(Definitions.FILE_PROJECT_B, 'wb'))
    pickle.dump(Values.Project_C, open(Definitions.FILE_PROJECT_C, 'wb'))
    pickle.dump(Values.Project_D, open(Definitions.FILE_PROJECT_D, 'wb'))


def load_state():
    Values.Project_A = pickle.load(open(Definitions.FILE_PROJECT_A, 'rb'))
    Values.Project_B = pickle.load(open(Definitions.FILE_PROJECT_B, 'rb'))
    Values.Project_C = pickle.load(open(Definitions.FILE_PROJECT_C, 'rb'))
    Values.Project_D = pickle.load(open(Definitions.FILE_PROJECT_D, 'rb'))


def create_base_directories():
    if not os.path.isdir(Definitions.DIRECTORY_LOG_BASE):
        os.makedirs(Definitions.DIRECTORY_LOG_BASE)

    if not os.path.isdir(Definitions.DIRECTORY_OUTPUT_BASE):
        os.makedirs(Definitions.DIRECTORY_OUTPUT_BASE)

    if not os.path.isdir(Definitions.DIRECTORY_BACKUP):
        os.makedirs(Definitions.DIRECTORY_BACKUP)


def error_exit(*args):
    print("\n")
    for i in args:
        Logger.error(i)
        Emitter.error(i)
    raise Exception("Error. Exiting...")


def find_files(src_path, extension, output, regex):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    # Save paths to all files in src_path with extension extension to output
    find_command = "find " + src_path + " -name '" + extension + "' "
    if regex is not None:
        find_command += " | grep '" + regex + "' "
    find_command += " > " + output
    execute_command(find_command)


def clean_files():
    # Remove other residual files stored in ./output/
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.information("Removing other residual files...")
    if os.path.isdir("output"):
        clean_command = "rm -rf " + Definitions.DIRECTORY_OUTPUT
        execute_command(clean_command)


def get_file_extension_list(src_path, output_file_name):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
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
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    backup_command = "cp " + file_path + " " + Definitions.DIRECTORY_BACKUP + "/" + backup_name
    execute_command(backup_command)


def restore_file(file_path, backup_name):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    restore_command = "cp " + Definitions.DIRECTORY_BACKUP + "/" + backup_name + " " + file_path
    execute_command(restore_command)


def reset_git(source_directory):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    reset_command = "cd " + source_directory + ";git reset --hard HEAD"
    execute_command(reset_command)


def show_partial_diff(source_path_a, source_path_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.highlight("\tTransplanted Code")
    output_file = Definitions.FILE_PARTIAL_PATCH
    diff_command = "diff -ENZBbwr " + source_path_a + " " + source_path_b + " > " + output_file
    execute_command(diff_command)
    with open(output_file, 'r', encoding='utf8', errors="ignore") as diff_file:
        diff_line = diff_file.readline().strip()
        while diff_line:
            Emitter.special("\t\t\t" + diff_line)
            diff_line = diff_file.readline().strip()


def is_intersect(start_a, end_a, start_b, end_b):
    return not (end_b < start_a or start_b > end_a)


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
    backup_command = "cp " + file_path + " " + file_path + ".orig"
    execute_command(backup_command)


def replace_file(file_a, file_b):
    replace_command = "cp " + file_a + " " + file_b
    execute_command(replace_command)


def restore_file_orig(file_path):
    restore_command = "cp " + file_path + ".orig " + file_path
    execute_command(restore_command)


def get_source_name_from_slice(slice_path):
    if ".c." in slice_path:
        source_path = slice_path.split(".c.")[0] + ".c"
    else:
        source_path = slice_path.split(".h.")[0] + ".h"
    return source_path

