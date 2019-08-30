import time
from common import Common
from common.Utils import exec_com, err_exit
import Print

file_index = 1
backup_file_list = dict()


def apply_patch(file_a, file_b, file_c, instruction_list):

    # Check for an edit script
    script_file_name = "output/" + str(file_index) + "_script"
    syntax_error_file_name = "output/" + str(file_index) + "_syntax_errors"
    with open(script_file_name, 'w', errors='replace') as script_file:
        for instruction in instruction_list:
            script_file.write(instruction + "\n")

    output_file = "output/" + str(file_index) + "_temp." + file_c[-1]
    c = ""
    # We add file_c into our dict (changes) to be able to backup and copy it
    if file_c not in backup_file_list.keys():
        filename = file_c.split("/")[-1]
        backup_file = str(file_index) + "_" + filename
        backup_file_list[file_c] = backup_file
        c += "cp " + file_c + " Backup_Folder/" + backup_file + "; "

    # We apply the patch using the script and crochet-patch
    c += Common.PATCH_COMMAND + " -s=" + Common.PATCH_SIZE + \
         " -script=" + script_file_name + " -source=" + file_a + \
         " -destination=" + file_b + " -target=" + file_c
    if file_c[-1] == "h":
        c += " --"
    c += " 2> output/errors > " + output_file + "; "
    c += "cp " + output_file + " " + file_c
    #Print.grey(c)
    exec_com(c)
    # We fix basic syntax errors that could have been introduced by the patch
    c2 = Common.SYNTAX_CHECK_COMMAND + "-fixit " + file_c
    if file_c[-1] == "h":
        c2 += " --"
    c2 += " 2>" + syntax_error_file_name
    exec_com(c2)
    # We check that everything went fine, otherwise, we restore everything
    try:
        c3 = Common.SYNTAX_CHECK_COMMAND + file_c + " 2>" + syntax_error_file_name
        if file_c[-1] == "h":
            c3 += " --"
        exec_com(c3)
    except Exception as e:
        Print.error("Clang-check could not repair syntax errors.")
        restore_files()
        err_exit(e, "Crochet failed.")
    # We format the file to be with proper spacing (needed?)
    c4 = Common.STYLE_FORMAT_COMMAND + file_c
    if file_c[-1] == "h":
        c4 += " --"
    c4 += " > " + output_file + "; "
    exec_com(c4)
    show_patch(file_a, file_b, "Backup_Folder/" + backup_file, output_file, str(file_index))
    c5 = "cp " + output_file + " " + file_c + ";"
    exec_com(c5)
    Print.success("\n\tSuccessful transformation")


def restore_files():
    global backup_file_list
    Print.warning("Restoring files...")
    for file in backup_file_list.keys():
        backup_file = backup_file_list[file]
        c = "cp Backup_Folder/" + backup_file + " " + file
        exec_com(c)
    Print.warning("Files restored")


def show_patch(file_a, file_b, file_c, file_d, index):
    Print.rose("Original Patch")
    original_patch_file_name = "output/" + index + "-original-patch"
    generated_patch_file_name = "output/" + index + "-generated-patch"
    diff_command = "diff -ENZBbwr " + file_a + " " + file_b + " > " + original_patch_file_name
    exec_com(diff_command)
    with open(original_patch_file_name, 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Print.white("\t" + diff_line)
            diff_line = diff.readline().strip()

    Print.rose("Generated Patch")
    diff_command = "diff -ENZBbwr " + file_c + " " + file_d + " > " + generated_patch_file_name
    exec_com(diff_command)
    with open(generated_patch_file_name, 'r', errors='replace') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Print.white("\t" + diff_line)
            diff_line = diff.readline().strip()


def safe_exec(function_def, title, *args):
    start_time = time.time()
    Print.sub_title("Starting " + title + "...")
    description = title[0].lower() + title[1:]
    try:
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = str(time.time() - start_time)
        Print.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Print.error("Crash during " + description + ", after " + duration + " seconds.")
        err_exit(exception, "Unexpected error during " + description + ".")
    return result


def weave():
    global file_index
    Print.title("Applying transformation")
    for file_list, generated_data in Common.translated_script_for_files.items():
        Print.sub_title("Transforming file " + file_list[2])
        Print.rose("Original AST script")
        original_script = generated_data[1]
        for instruction in original_script:
            Print.white(instruction)
        Print.rose("Generated AST script")
        translated_script = generated_data[0]
        for instruction in translated_script:
            Print.white(instruction)
        apply_patch(file_list[0], file_list[1], file_list[2], translated_script)
        file_index += 1
