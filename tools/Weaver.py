from common import Definitions, Values
from common.Utilities import execute_command, error_exit
from tools import Emitter

file_index = 1
backup_file_list = dict()


def restore_files():
    global backup_file_list
    Emitter.warning("Restoring files...")
    for b_file in backup_file_list.keys():
        backup_file = backup_file_list[b_file]
        backup_command = "cp backup/" + backup_file + " " + b_file
        execute_command(backup_command)
    Emitter.warning("Files restored")


def show_patch(file_a, file_b, file_c, file_d, index):
    Emitter.special("Original Patch")
    original_patch_file_name = Definitions.DIRECTORY_OUTPUT + index + "-original-patch"
    generated_patch_file_name = Definitions.DIRECTORY_OUTPUT + index + "-generated-patch"
    diff_command = "diff -ENZBbwr " + file_a + " " + file_b + " > " + original_patch_file_name
    execute_command(diff_command)
    with open(original_patch_file_name, 'r') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Emitter.special("\t" + diff_line)
            diff_line = diff.readline().strip()

    Emitter.special("Generated Patch")
    diff_command = "diff -ENZBbwr " + file_c + " " + file_d + " > " + generated_patch_file_name
    # print(diff_command)
    execute_command(diff_command)
    with open(generated_patch_file_name, 'r') as diff:
        diff_line = diff.readline().strip()
        while diff_line:
            Emitter.special("\t" + diff_line)
            diff_line = diff.readline().strip()


def apply_patch(file_a, file_b, file_c, instruction_list):
    # Check for an edit script
    script_file_name = Definitions.DIRECTORY_OUTPUT + str(file_index) + "_script"
    syntax_error_file_name = Definitions.DIRECTORY_OUTPUT + str(file_index) + "_syntax_errors"
    with open(script_file_name, 'w') as script_file:
        for instruction in instruction_list:
            script_file.write(instruction + "\n")

    output_file = Definitions.DIRECTORY_OUTPUT + str(file_index) + "_temp." + file_c[-1]
    backup_command = ""
    # We add file_c into our dict (changes) to be able to backup and copy it
    file_d = str(file_c).replace(Values.Project_C.path, Values.Project_D.path)
    if file_c not in backup_file_list.keys():
        filename = file_c.split("/")[-1]
        backup_file = str(file_index) + "_" + filename
        backup_file_list[file_c] = backup_file
        backup_command += "cp " + file_c + " " + Definitions.DIRECTORY_BACKUP + "/" + backup_file
    # print(backup_command)
    execute_command(backup_command)

    # We apply the patch using the script and crochet-patch
    patch_command = Definitions.PATCH_COMMAND + " -s=" + Definitions.PATCH_SIZE + \
         " -script=" + script_file_name + " -source=" + file_a + \
         " -destination=" + file_b + " -target=" + file_c
    if file_c[-1] == "h":
        patch_command += " --"
    patch_command += " 2> output/errors > " + output_file + "; "
    patch_command += "cp " + output_file + " " + file_d

    # print(patch_command)
    execute_command(patch_command)

    # We fix basic syntax errors that could have been introduced by the patch
    fix_command = Definitions.SYNTAX_CHECK_COMMAND + "-fixit " + file_d
    if file_c[-1] == "h":
        fix_command += " --"
    fix_command += " 2>" + syntax_error_file_name
    execute_command(fix_command)

    # We check that everything went fine, otherwise, we restore everything
    try:
        check_command = Definitions.SYNTAX_CHECK_COMMAND + file_d + " 2>" + syntax_error_file_name
        if file_c[-1] == "h":
            check_command += " --"
        execute_command(check_command)
    except Exception as e:
        Emitter.error("Clang-check could not repair syntax errors.")
        restore_files()
        error_exit(e, "Crochet failed.")

    # # We format the file to be with proper spacing (needed?)
    # format_command = Definitions.STYLE_FORMAT_COMMAND + file_c
    # if file_c[-1] == "h":
    #     format_command += " --"
    # format_command += " > " + output_file + "; "
    # execute_command(format_command)
    show_patch(file_a, file_b, file_c, file_d, str(file_index))
    #
    # c5 = "cp " + output_file + " " + file_c + ";"
    # execute_command(c5)
    Emitter.success("\n\tSuccessful transformation")
