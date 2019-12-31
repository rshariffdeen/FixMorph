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

CONF_DATA_PATH = ""
CONF_TOOL_PATH = ""
CONF_TOOL_PARAMS = ""
CONF_TOOL_NAME = ""

FILE_META_DATA = "meta-data"
FILE_ERROR_LOG = "error-log"

DIR_SCRIPT = "scripts"
DIR_CONF = "conf"
DIR_MAIN = os.getcwd()

EXPERIMENT_ITEMS = list()


def setup(script_path, script_name, deploy_path):
    global FILE_ERROR_LOG
    print("\t[INFO]creating setup")
    command = "{ cd " + script_path + "; bash " + script_name + " " + deploy_path + ";} 2> " + FILE_ERROR_LOG
    # print(command)
    process = subprocess.Popen([command], stdout=subprocess.PIPE, shell=True)
    (output, error) = process.communicate()


def evaluate():
    print("\t[INFO]running evaluation")


def load_experiment():
    global EXPERIMENT_ITEMS
    print("[DRIVER] Loading experiment data")
    with open(FILE_META_DATA, 'r') as in_file:
        json_data = json.load(in_file)
        EXPERIMENT_ITEMS = json_data


def read_arg():
    global CONF_DATA_PATH, CONF_TOOL_NAME, CONF_TOOL_PARAMS, CONF_TOOL_PATH
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

    else:
        print("Usage: python driver [OPTIONS] ")
        print("Options are:")
        print("\t" + ARG_DATA_PATH + "\t| " + "directory for experiments")
        print("\t" + ARG_TOOL_NAME + "\t| " + "name of the tool")
        print("\t" + ARG_TOOL_PATH + "\t| " + "path of the tool")
        print("\t" + ARG_TOOL_PARAMS + "\t| " + "parameters for the tool")
        exit()


def run():
    global EXPERIMENT_ITEMS, DIR_MAIN, CONF_DATA_PATH
    print("[DRIVER] Running experiment driver")
    read_arg()
    load_experiment()
    for experiment_item in EXPERIMENT_ITEMS:
        directory_name = str(experiment_item[KEY_DONOR])
        script_name = str(experiment_item[KEY_BUG_NAME]) + ".sh"
        category = experiment_item[KEY_CATEGORY]
        if category == "cross-program":
            directory_name = str(experiment_item[KEY_DONOR]) + "-" + str(experiment_item[KEY_TARGET])
        script_path = DIR_MAIN + "/" + DIR_SCRIPT + "/" + str(category) + "/" + str(directory_name)
        setup(script_path, script_name, CONF_DATA_PATH)


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt as e:
        print("[DRIVER] Program Interrupted by User")
        exit()
