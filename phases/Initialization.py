#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import time
import subprocess
from common.Utilities import execute_command
from entity import Project
from common import Definitions, Values
from tools import Emitter, Logger


def load_standard_list():
    with open(Definitions.FILE_STANDARD_FUNCTION_LIST, "r") as list_file:
        Values.STANDARD_FUNCTION_LIST = [line.strip() for line in list_file]
    with open(Definitions.FILE_STANDARD_MACRO_LIST, "r") as list_file:
        Values.STANDARD_MACRO_LIST = [line.strip() for line in list_file]


def set_env_value():
    Emitter.normal("\tsetting environment values")
    os.environ["PYTHONPATH"] = "/home/rshariffdeen/workspace/z3/build/python"
    execute_command("export PYTHONPATH=/home/rshariffdeen/workspace/z3/build/python")


def load_values():
    Values.Project_A = Project.Project(Values.PATH_A, "Pa")
    Values.Project_B = Project.Project(Values.PATH_B, "Pb")
    Values.Project_C = Project.Project(Values.PATH_C, "Pc")
    Values.Project_D = Project.Project(Values.PATH_C + "-patch", "Pd")
    if Values.PATH_E:
        Values.Project_E = Project.Project(Values.PATH_E, "Pe")
    load_standard_list()


def create_patch_dir():
    patch_dir = Values.PATH_C + "-patch"
    if not os.path.isdir(patch_dir):
        create_command = "cp -rf " + Values.PATH_C + " " + Values.PATH_C + "-patch"
        execute_command(create_command)


def create_output_dir():
    if not os.path.isdir(Definitions.DIRECTORY_OUTPUT):
        create_command = "mkdir -p " + Definitions.DIRECTORY_OUTPUT
        execute_command(create_command)


def create_log_dir():
    if not os.path.isdir(Definitions.DIRECTORY_LOG):
        create_command = "mkdir -p " + Definitions.DIRECTORY_LOG
        process = subprocess.Popen([create_command], stdout=subprocess.PIPE, shell=True)
        (output, error) = process.communicate()


def create_fuzz_dir():
    input_dir = Definitions.DIRECTORY_OUTPUT + "/fuzz-input"
    output_dir = Definitions.DIRECTORY_OUTPUT + "/fuzz-output"
    if not os.path.isdir(input_dir):
        create_command = "mkdir -p " + input_dir
        execute_command(create_command)
    if not os.path.isdir(output_dir):
        create_command = "mkdir -p " + output_dir
        execute_command(create_command)


def create_directories():
    create_log_dir()
    create_patch_dir()
    create_output_dir()
    create_fuzz_dir()


def create_files():
    Definitions.FILE_PROJECT_A = Definitions.DIRECTORY_OUTPUT + "/project-A"
    open(Definitions.FILE_PROJECT_A, 'a').close()
    Definitions.FILE_PROJECT_B = Definitions.DIRECTORY_OUTPUT + "/project-B"
    open(Definitions.FILE_PROJECT_B, 'a').close()
    Definitions.FILE_PROJECT_C = Definitions.DIRECTORY_OUTPUT + "/project-C"
    open(Definitions.FILE_PROJECT_C, 'a').close()
    Definitions.FILE_PROJECT_D = Definitions.DIRECTORY_OUTPUT + "/project-D"
    open(Definitions.FILE_PROJECT_D, 'a').close()
    if Values.PATH_E:
        Definitions.FILE_PROJECT_E = Definitions.DIRECTORY_OUTPUT + "/project-E"
        open(Definitions.FILE_PROJECT_E, 'a').close()
    Logger.create()


def read_conf():
    Emitter.normal("\treading configuration values")
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if Definitions.ARG_DEBUG in arg:
                Values.DEBUG = True
            elif Definitions.ARG_SKIP_ANALYSE in arg:
                Values.SKIP_DIFF = True
            elif Definitions.ARG_SKIP_SEGMENT in arg:
                Values.SKIP_SEGMENT = True
            elif Definitions.ARG_SKIP_DETECTION in arg:
                Values.SKIP_DETECTION = True
            elif Definitions.ARG_SKIP_VEC_GEN in arg:
                Values.SKIP_VEC_GEN = True
            elif Definitions.ARG_SKIP_EXTRACTION in arg:
                Values.SKIP_EXTRACTION = True
            elif Definitions.ARG_SKIP_MAPPING in arg:
                Values.SKIP_MAPPING = True
            elif Definitions.ARG_SKIP_WEAVE in arg:
                Values.SKIP_WEAVE = True
            elif Definitions.ARG_SKIP_VERIFY in arg:
                Values.SKIP_VERIFY = True
            elif Definitions.ARG_SKIP_ANALYSE in arg:
                Values.SKIP_ANALYSE = True
            elif Definitions.ARG_SKIP_TRANSLATION in arg:
                Values.SKIP_TRANSLATION = True
            elif Definitions.ARG_SKIP_RESTORE in arg:
                Values.SKIP_RESTORE = True
            elif Definitions.ARG_BACKPORT in arg:
                Values.BACKPORT = True
            elif Definitions.ARG_FORK in arg:
                Values.FORK = True
            elif Definitions.ARG_CONF_FILE in arg:
                Values.FILE_CONFIGURATION = str(arg).replace(Definitions.ARG_CONF_FILE, '')
            elif Definitions.ARG_ONLY_VERIFY in arg:
                Values.ONLY_VERIFY = True
                Values.SKIP_RESTORE = True
                Values.SKIP_BUILD = True
                Values.SKIP_WEAVE = True
                Values.SKIP_DIFF = True
                Values.SKIP_MAPPING = True
                Values.SKIP_EXTRACTION = True
                Values.SKIP_TRANSLATION = True
                Values.SKIP_DETECTION = True
                Values.SKIP_SEGMENT = True
            elif Definitions.ARG_ONLY_BUILD in arg:
                Values.SKIP_VERIFY = True
                Values.SKIP_WEAVE = True
                Values.SKIP_DIFF = True
                Values.SKIP_MAPPING = True
                Values.SKIP_EXTRACTION = True
                Values.SKIP_TRANSLATION = True
                Values.SKIP_DETECTION = True
                Values.SKIP_SEGMENT = True
            elif Definitions.ARG_ONLY_ANALYSE in arg:
                Values.ONLY_ANALYSE = True
                Values.SKIP_VERIFY = True
                Values.SKIP_RESTORE = True
                Values.SKIP_DIFF = True
                Values.SKIP_MAPPING = True
                Values.SKIP_EXTRACTION = True
                Values.SKIP_TRANSLATION = True
                Values.SKIP_DETECTION = True
                Values.SKIP_WEAVE = True
                Values.SKIP_SEGMENT = True
            elif Definitions.ARG_ONLY_WEAVE in arg:
                Values.SKIP_VERIFY = True
                Values.SKIP_RESTORE = True
                Values.SKIP_BUILD = True
                Values.SKIP_DIFF = True
                Values.SKIP_MAPPING = True
                Values.SKIP_EXTRACTION = True
                Values.SKIP_TRANSLATION = True
                Values.SKIP_DETECTION = True
                Values.SKIP_SEGMENT = True
            elif Definitions.ARG_SKIP_BUILD in arg:
                Values.SKIP_BUILD = True
            elif Definitions.ARG_LINUX_KERNEL in arg:
                Values.IS_LINUX_KERNEL = True
            elif "Crochet.py" in arg:
                continue
            else:
                Emitter.normal("Invalid argument: " + arg)
                Emitter.help()
                exit()
    else:
        Emitter.help()
        exit()

    if not os.path.exists(Values.FILE_CONFIGURATION):
        Emitter.normal("[NOT FOUND] Configuration file " + Values.FILE_CONFIGURATION)
        exit()

    with open(Values.FILE_CONFIGURATION, 'r') as conf_file:
        configuration_list = [i.strip() for i in conf_file.readlines()]

    # create log files and other directories
    conf_file_name = Values.FILE_CONFIGURATION.split("/")[-1]
    project_name = Values.FILE_CONFIGURATION.split("/")[-3]
    dir_name = project_name + "-" + conf_file_name.replace(".conf", "")

    Definitions.DIRECTORY_OUTPUT = Definitions.DIRECTORY_OUTPUT_BASE + "/" + dir_name
    Definitions.DIRECTORY_LOG = Definitions.DIRECTORY_LOG_BASE + "/" + dir_name
    Definitions.FILE_ERROR_LOG = Definitions.DIRECTORY_LOG + "/log-error"
    Definitions.FILE_LAST_LOG = Definitions.DIRECTORY_LOG + "/log-latest"
    Definitions.FILE_MAKE_LOG = Definitions.DIRECTORY_LOG + "/log-make"
    Definitions.FILE_COMMAND_LOG = Definitions.DIRECTORY_LOG + "/log-command"
    log_file_name = "log-" + str(time.time())
    log_file_path = Definitions.DIRECTORY_LOG + "/" + log_file_name
    Definitions.FILE_MAIN_LOG = log_file_path

    for configuration in configuration_list:
        if Definitions.CONF_PATH_A in configuration:
            Values.PATH_A = configuration.replace(Definitions.CONF_PATH_A, '')
            if "$HOME$" in Values.PATH_A:
                Values.PATH_A = Values.PATH_A.replace("$HOME$", Definitions.DIRECTORY_MAIN)
        elif Definitions.CONF_PATH_B in configuration:
            Values.PATH_B = configuration.replace(Definitions.CONF_PATH_B, '')
            if "$HOME$" in Values.PATH_B:
                Values.PATH_B = Values.PATH_B.replace("$HOME$", Definitions.DIRECTORY_MAIN)
        elif Definitions.CONF_PATH_C in configuration:
            Values.PATH_C = configuration.replace(Definitions.CONF_PATH_C, '')
            if "$HOME$" in Values.PATH_C:
                Values.PATH_C = Values.PATH_C.replace("$HOME$", Definitions.DIRECTORY_MAIN)
            if str(Values.PATH_C)[-1] == "/":
                Values.PATH_C = Values.PATH_C[:-1]
        elif Definitions.CONF_PATH_E in configuration:
            Values.PATH_E = configuration.replace(Definitions.CONF_PATH_E, '')
            if "$HOME$" in Values.PATH_E:
                Values.PATH_E = Values.PATH_E.replace("$HOME$", Definitions.DIRECTORY_MAIN)
            if str(Values.PATH_E)[-1] == "/":
                Values.PATH_E = Values.PATH_E[:-1]
        elif Definitions.CONF_PATH_POC in configuration:
            Values.PATH_POC = configuration.replace(Definitions.CONF_PATH_POC, '')
            if "$HOME$" in Values.PATH_POC:
                Values.PATH_POC = Values.PATH_POC.replace("$HOME$", Definitions.DIRECTORY_MAIN)
        elif Definitions.CONF_FLAGS_A in configuration:
            Values.BUILD_FLAGS_A = configuration.replace(Definitions.CONF_FLAGS_A, '')
        elif Definitions.CONF_FLAGS_C in configuration:
            Values.BUILD_FLAGS_C = configuration.replace(Definitions.CONF_FLAGS_C, '')
        elif Definitions.CONF_CONFIG_COMMAND_A in configuration:
            Values.CONFIG_COMMAND_A = configuration.replace(Definitions.CONF_CONFIG_COMMAND_A, '')
        elif Definitions.CONF_CONFIG_COMMAND_C in configuration:
            Values.CONFIG_COMMAND_C = configuration.replace(Definitions.CONF_CONFIG_COMMAND_C, '')
        elif Definitions.CONF_BUILD_COMMAND_A in configuration:
            Values.BUILD_COMMAND_A = configuration.replace(Definitions.CONF_BUILD_COMMAND_A, '')
        elif Definitions.CONF_BUILD_COMMAND_C in configuration:
            Values.BUILD_COMMAND_C = configuration.replace(Definitions.CONF_BUILD_COMMAND_C, '')
        elif Definitions.CONF_ASAN_FLAG in configuration:
            Values.ASAN_FLAG = configuration.replace(Definitions.CONF_ASAN_FLAG, '')
        elif Definitions.CONF_KLEE_FLAGS_A in configuration:
            Values.KLEE_FLAG_A = configuration.replace(Definitions.CONF_KLEE_FLAGS_A, '')
        elif Definitions.CONF_KLEE_FLAGS_C in configuration:
            Values.KLEE_FLAG_C = configuration.replace(Definitions.CONF_KLEE_FLAGS_C, '')
        elif Definitions.CONF_DIFF_SIZE in configuration:
            Values.AST_DIFF_SIZE = configuration.replace(Definitions.CONF_DIFF_SIZE, '')
        elif Definitions.CONF_EXPLOIT_C in configuration:
            Values.EXPLOIT_C = configuration.replace(Definitions.CONF_EXPLOIT_C, '')
        elif Definitions.CONF_VC in configuration:
            Values.VC = configuration.replace(Definitions.CONF_VC, '')


def initialize():
    Emitter.title("Initializing project for Transfer")
    Emitter.sub_title("loading configuration")
    load_values()
    create_directories()
    create_files()
    Emitter.sub_title("set environment")
    set_env_value()

