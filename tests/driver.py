import sys
import json
import subprocess
import os
import shutil
import git


DIR_TEST = os.getcwd()
CONF_DATA_PATH = "/data"
CONF_TOOL_PATH = "/fixmorph"
CONF_TOOL_PARAMS = " --backport --linux-kernel --skip-summary"
CONF_TOOL_NAME = "python3 FixMorph.py"
CONF_DEBUG = False
CONF_SKIP_SETUP = False
CONF_ONLY_SETUP = False
CONF_START_ID = None
CONF_END_ID = None
CONF_BUG_ID = None
CONF_BUG_ID_LIST = None
CONF_UPDATE_TEST = False
CONF_ANALYSIS_MODE = False

operation_mode_list = [0, 1, 2, 3]

test_case_list = {
    "insert": [
        "different-context", "different-line", "for_loop", "method_call", "missing_dependency", "simple"
    ],
    "update": [
        "assignment", "different-context", "different-line", "if_condition", "macro_definition", "macro_use",
        "method_arg", "method_call", "simple", "two_neighborhood"
    ]
}


def execute_command(command):
    if CONF_DEBUG:
        print("\t[COMMAND]" + command)
    process = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    (output, error) = process.communicate()
    return str(process.returncode)


def setup_each(base_dir_path, bug_id, commit_id_list):
    global FILE_ERROR_LOG, CONF_DATA_PATH, CONF_UPDATE_TEST
    print("\t[INFO] creating directories for experiment")
    postfix_list = ['a', 'b', 'c', 'e']
    bug_dir = base_dir_path + "/" + str(bug_id)
    if not os.path.isdir(bug_dir) or CONF_UPDATE_TEST:
        # dir_command = "mkdir -p " + bug_dir
        # execute_command(dir_command)
        os.makedirs(bug_dir)
    for i in range(0, 4):
        dir_path = bug_dir + "/p" + postfix_list[i]
        if not os.path.isdir(dir_path):
            shutil.copytree(REPO_PATH, dir_path)
            # copy_command = "cp -rf " + REPO_PATH + " " + dir_path
            # execute_command(copy_command)
        repo = git.Repo(dir_path)
        repo.git.reset("--hard")
        repo.git.checkout(commit_id_list[i])
        # checkout_command = "cd " + dir_path + ";"
        # checkout_command += "git checkout " + commit_id_list[i] + " > /dev/null"
        # execute_command(checkout_command)
    if not CONF_ANALYSIS_MODE:
        if os.path.isdir(bug_dir + "/pc-patch"):
            shutil.rmtree(bug_dir + "/pc-patch")
            # delete_command = "rm -rf " + bug_dir + "/pc-patch"
            # execute_command(delete_command)


def check_word_exist(file_path, keyword):
    with open(file_path, "r") as log_file:
        content = log_file.readlines()
        content_str = ''.join(content)
        if keyword in content_str:
            return True
    return False


def analyse_result(bug_id, log_file_path):
    global COUNT_SUCCESS, COUNT_FAILURES, COUNT_TRANSFORM_FAILED
    global COUNT_VERIFY_FAILED, COUNT_BUILD_FAILED, COUNT_RUNTIME_ERRORS

    is_build_failed = check_word_exist(log_file_path, "BUILD FAILED")
    is_verify = check_word_exist(log_file_path, "verifying compilation")
    is_success = check_word_exist(log_file_path, "FixMorph finished successfully")
    is_failed = check_word_exist(log_file_path, "exited with an error")
    is_runtime_error = not check_word_exist(log_file_path, "FAILED") and is_failed
    is_transform_failure = check_word_exist(log_file_path, "transformation FAILED")

    if is_success:
        COUNT_SUCCESS = COUNT_SUCCESS + 1
        list_success.append(bug_id)
    elif is_build_failed and is_verify:
        COUNT_VERIFY_FAILED = COUNT_VERIFY_FAILED + 1
        list_verify_failed.append(bug_id)
    elif is_build_failed and not is_verify:
        COUNT_BUILD_FAILED = COUNT_BUILD_FAILED + 1
        list_build_failed.append(bug_id)
    elif is_failed and not is_runtime_error:
        COUNT_FAILURES = COUNT_FAILURES + 1
    elif is_failed and is_runtime_error:
        COUNT_RUNTIME_ERRORS = COUNT_RUNTIME_ERRORS + 1
    elif is_transform_failure:
        COUNT_TRANSFORM_FAILED = COUNT_TRANSFORM_FAILED + 1
    else:
        list_other_failed.append(bug_id)


def evaluate(conf_path, tool_params):
    global CONF_TOOL_PARAMS, CONF_TOOL_PATH, CONF_TOOL_NAME, DIR_LOGS, COUNT_SUCCESS
    tool_command = "{ cd " + CONF_TOOL_PATH + ";" + CONF_TOOL_NAME + " --conf=" + conf_path + " " + tool_params + ";} "
    ret_code = execute_command(tool_command)
    return ret_code


def run():
    global test_case_list, operation_mode_list
    repo = git.Repo(DIR_TEST + "/..")
    dash = "-" * 80
    print(dash)
    print("{:>4s} {:<10s} {:>30s} {:<8s} {:<8s}".format("MODE", "ACTION", "SCENARIO", "STATUS", "RESULT"))
    print(dash)
    for operation_mode in operation_mode_list:
        repo.git.reset("--hard")
        for test_action in test_case_list:
            scenario_list = test_case_list[test_action]
            for scenario in scenario_list:
                conf_path = DIR_TEST + "/" + test_action + "/" + scenario + "/repair.conf"
                tool_param = "--mode=" + str(operation_mode)
                status_code = evaluate(conf_path, tool_param)
                result = False
                if int(status_code) != 0:
                    print("[ERROR] Something went wrong!!")
                    exit()
                print("{:>4s} {:<10s} {:>30s} {:<8s} {:<8s}".format(str(operation_mode), test_action, scenario,
                                                                    str(status_code), str(result)))


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt as e:
        print("[TEST DRIVER] Program Interrupted by User")
        exit()
