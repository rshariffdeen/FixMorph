import sys
import json
import subprocess
import os


KEY_CATEGORY = "category"
KEY_DONOR = "donor"
KEY_TARGET = "target"
KEY_BUG_NAME = "bug_name"
KEY_POC_PATH = "poc"
KEY_CVE_ID = "cve"

ARG_DATA_PATH = "--data-dir="
ARG_TOOL_PATH = "--tool-path="
ARG_TOOL_NAME = "--tool-name="
ARG_TOOL_PARAMS = "--tool-param="
ARG_DEBUG_MODE = "--debug"
ARG_SKIP_SETUP = "--skip-setup"
ARG_ONLY_SETUP = "--only-setup"

CONF_DATA_PATH = "/data"
CONF_TOOL_PATH = "/crochet"
CONF_TOOL_PARAMS = " --backport --linux-kernel"
CONF_TOOL_NAME = "python3 Crochet.py"
CONF_DEBUG = False
CONF_SKIP_SETUP = False
CONF_ONLY_SETUP = False


FILE_META_DATA = "meta-data"
FILE_ERROR_LOG = "error-log"


DIR_MAIN = os.getcwd()
DIR_LOGS = DIR_MAIN + "/logs"
DIR_SCRIPT = DIR_MAIN + "/scripts"
DIR_CONF = DIR_MAIN + "/configuration"


EXPERIMENT_ITEMS = list()
REPO_URL = "https://kernel.googlesource.com/pub/scm/linux/kernel/git/stable/linux-stable"
REPO_PATH = "/linux-stable"


def create_directories():
    create_command = "mkdir " + DIR_LOGS
    execute_command(create_command)


def execute_command(command):
    if CONF_DEBUG:
        print("\t[COMMAND]" + command)
    process = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    (output, error) = process.communicate()


def setup(base_dir_path, bug_id, commit_id_list):
    global FILE_ERROR_LOG, CONF_DATA_PATH
    print("\t[INFO] creating directories for experiment")
    postfix_list = ['a', 'b', 'c']
    bug_dir = base_dir_path + "/" + str(bug_id)
    if not os.path.isdir(bug_dir):
        dir_command = "mkdir -p " + bug_dir
        execute_command(dir_command)
        for i in range(0, 3):
            dir_path = bug_dir + "/p" + postfix_list[i]
            copy_command = "cp -rf " + REPO_PATH + " " + dir_path
            execute_command(copy_command)
            checkout_command = "cd " + dir_path + ";"
            checkout_command += "git checkout " + commit_id_list[i] + " > /dev/null"
            execute_command(checkout_command)


def evaluate(conf_path):
    global CONF_TOOL_PARAMS, CONF_TOOL_PATH, CONF_TOOL_NAME, DIR_LOGS
    print("\t[INFO]running evaluation")
    tool_command = "{ cd " + CONF_TOOL_PATH + ";" + CONF_TOOL_NAME + " --conf=" + conf_path + " "+ CONF_TOOL_PARAMS + ";} 2> " + FILE_ERROR_LOG
    execute_command(tool_command)


def clone_repo():
    global REPO_URL
    clone_command = "git clone " + REPO_URL + " " + REPO_PATH + " > /dev/null"
    if not os.path.isdir(REPO_PATH):
        print("[DRIVER] Cloning remote repository\n")
        execute_command(clone_command)


def write_conf_file(base_dir_path, bug_id, module_a, module_c):
    print("\t[INFO] creating configuration")
    conf_file_name = str(bug_id) + ".conf"
    dir_path = base_dir_path + "/" + str(bug_id)
    conf_file_path = dir_path + "/" + conf_file_name
    with open(conf_file_path, "w") as conf_file:
        content = "path_a:" + dir_path + "/pa\n"
        content += "path_b:" + dir_path + "/pb\n"
        content += "path_c:" + dir_path + "/pc\n"
        content += "config_command_a:no | make oldconfig; make prepare; make modules_prepare\n"
        content += "config_command_c:no | make oldconfig; make prepare; make modules_prepare\n"
        if module_a is None:
            content += "build_command_a:skip\n"
            content += "build_command_c:skip\n"
        else:
            content += "build_command_a:make M=" + module_a + "\n"
            if module_c is None:
                content += "build_command_c:make M=" + module_a + "\n"
            else:
                content += "build_command_c:make M=" + module_c + "\n"
        conf_file.write(content)
    return conf_file_path


def load_experiment():
    global EXPERIMENT_ITEMS
    print("[DRIVER] Loading experiment data\n")
    with open(FILE_META_DATA, 'r') as in_file:
        json_data = json.load(in_file)
        EXPERIMENT_ITEMS = json_data


def read_arg():
    global CONF_DATA_PATH, CONF_TOOL_NAME, CONF_TOOL_PARAMS
    global CONF_TOOL_PATH, CONF_DEBUG, CONF_SKIP_SETUP, CONF_ONLY_SETUP
    print("[DRIVER] Reading configuration values")
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if ARG_DATA_PATH in arg:
                CONF_DATA_PATH = str(arg).replace(ARG_DATA_PATH, "")
            elif ARG_TOOL_NAME in arg:
                CONF_TOOL_NAME = str(arg).replace(ARG_TOOL_NAME, "")
            elif ARG_TOOL_PATH in arg:
                CONF_TOOL_PATH = str(arg).replace(ARG_TOOL_PATH, "")
            elif ARG_TOOL_PARAMS in arg:
                CONF_TOOL_PARAMS = str(arg).replace(ARG_TOOL_PARAMS, "")
            elif ARG_DEBUG_MODE in arg:
                CONF_DEBUG = True
            elif ARG_SKIP_SETUP in arg:
                CONF_SKIP_SETUP = True
            elif ARG_ONLY_SETUP in arg:
                CONF_ONLY_SETUP = True
            elif "driver.py" in arg:
                continue
            else:
                print("Usage: python driver [OPTIONS] ")
                print("Options are:")
                print("\t" + ARG_DATA_PATH + "\t| " + "directory for experiments")
                print("\t" + ARG_TOOL_NAME + "\t| " + "name of the tool")
                print("\t" + ARG_TOOL_PATH + "\t| " + "path of the tool")
                print("\t" + ARG_TOOL_PARAMS + "\t| " + "parameters for the tool")
                print("\t" + ARG_DEBUG_MODE + "\t| " + "enable debug mode")
                exit()


def run():
    global EXPERIMENT_ITEMS, DIR_MAIN, CONF_DATA_PATH, CONF_TOOL_PARAMS
    print("[DRIVER] Running experiment driver")
    read_arg()
    clone_repo()
    load_experiment()
    create_directories()
    index = 1
    DIR_EXPERIMENT = CONF_DATA_PATH + "/backport/linux"

    for experiment_item in EXPERIMENT_ITEMS:
        experiment_name = "Experiment-" + str(index) + "\n-----------------------------"
        print(experiment_name)

        fix_parent = str(experiment_item['pa'])
        fix_commit = str(experiment_item['pb'])
        target_commit = str(experiment_item['pc'])
        module_a = None
        module_c = None
        if 'ma' in experiment_item.keys():
            module_a = str(experiment_item['ma'])
        if 'mc' in experiment_item.keys():
            module_c = str(experiment_item['mc'])
        commit_list = (fix_parent, fix_commit, target_commit)

        print("\t[META-DATA] Pa: " + fix_parent)
        print("\t[META-DATA] Pb: " + fix_commit)
        print("\t[META-DATA] Pc: " + target_commit)
        if module_a is not None:
            print("\t[META-DATA] Module-a: " + module_a)
        if module_c is not None:
            print("\t[META-DATA] Module-c: " + module_c)

        conf_file_path = ''

        if not CONF_SKIP_SETUP:
            setup(DIR_EXPERIMENT, index, commit_list)
            conf_file_path = write_conf_file(DIR_EXPERIMENT, index, module_a, module_c)

        if not CONF_ONLY_SETUP:
            evaluate(conf_file_path)
        index = index + 1


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt as e:
        print("[DRIVER] Program Interrupted by User")
        exit()
