#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import time
import shutil
import subprocess
from common.utilities import execute_command
from entity import Project
from common import definitions, values
from tools import Emitter, Logger


def load_standard_list():
    with open(definitions.FILE_STANDARD_FUNCTION_LIST, "r") as list_file:
        values.STANDARD_FUNCTION_LIST = [line.strip() for line in list_file]
    with open(definitions.FILE_STANDARD_MACRO_LIST, "r") as list_file:
        values.STANDARD_MACRO_LIST = [line.strip() for line in list_file]


def set_env_value():
    Emitter.normal("\tsetting environment values")
    os.environ["PYTHONPATH"] = "/home/rshariffdeen/workspace/z3/build/python"
    execute_command("export PYTHONPATH=/home/rshariffdeen/workspace/z3/build/python")


def load_file_defs():
    definitions.FILE_AST_SCRIPT = definitions.DIRECTORY_TMP + "/ast-script"
    definitions.FILE_TEMP_DIFF = definitions.DIRECTORY_TMP + "/temp_diff"
    definitions.FILE_AST_MAP = definitions.DIRECTORY_TMP + "/ast-map"
    definitions.FILE_AST_DIFF_ERROR = definitions.DIRECTORY_TMP + "/errors_ast_diff"
    definitions.FILE_PARTIAL_PATCH = definitions.DIRECTORY_TMP + "/gen-patch"
    definitions.FILE_EXCLUDED_EXTENSIONS = definitions.DIRECTORY_TMP + "/excluded-extensions"
    definitions.FILE_EXCLUDED_EXTENSIONS_A = definitions.DIRECTORY_TMP + "/excluded-extensions-a"
    definitions.FILE_EXCLUDED_EXTENSIONS_B = definitions.DIRECTORY_TMP + "/excluded-extensions-b"
    definitions.FILE_GIT_UNTRACKED_FILES = definitions.DIRECTORY_TMP + "/untracked-list"
    definitions.FILE_DIFF_C = definitions.DIRECTORY_TMP + "/diff_C"
    definitions.FILE_DIFF_H = definitions.DIRECTORY_TMP + "/diff_H"
    definitions.FILE_DIFF_ALL = definitions.DIRECTORY_TMP + "/diff_all"
    definitions.FILE_FIND_RESULT = definitions.DIRECTORY_TMP + "/find_tmp"
    definitions.FILE_TEMP_TRANSFORM = definitions.DIRECTORY_TMP + "/temp-transform"


def load_values():
    values.Project_A = Project.Project(values.PATH_A, "Pa")
    values.Project_B = Project.Project(values.PATH_B, "Pb")
    values.Project_C = Project.Project(values.PATH_C, "Pc")
    values.Project_D = Project.Project(values.PATH_C + "-patch", "Pd")
    if values.PATH_E:
        values.Project_E = Project.Project(values.PATH_E, "Pe")
    load_standard_list()
    load_file_defs()


def create_patch_dir():
    patch_dir = values.PATH_C + "-patch"
    if os.path.isdir(patch_dir):
        if definitions.DIRECTORY_TESTS in patch_dir:
            shutil.rmtree(patch_dir)
    if not os.path.isdir(patch_dir):
        create_command = "cp -rf " + values.PATH_C + " " + values.PATH_C + "-patch"
        execute_command(create_command)



def create_output_dir():
    if not os.path.isdir(definitions.DIRECTORY_OUTPUT):
        create_command = "mkdir -p " + definitions.DIRECTORY_OUTPUT
        execute_command(create_command)
    if not os.path.isdir(definitions.DIRECTORY_TMP):
        os.makedirs(definitions.DIRECTORY_TMP)


def create_log_dir():
    if not os.path.isdir(definitions.DIRECTORY_LOG):
        create_command = "mkdir -p " + definitions.DIRECTORY_LOG
        process = subprocess.Popen([create_command], stdout=subprocess.PIPE, shell=True)
        (output, error) = process.communicate()


def create_fuzz_dir():
    input_dir = definitions.DIRECTORY_OUTPUT + "/fuzz-input"
    output_dir = definitions.DIRECTORY_OUTPUT + "/fuzz-output"
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
    definitions.FILE_PROJECT_A = definitions.DIRECTORY_OUTPUT + "/project-A"
    open(definitions.FILE_PROJECT_A, 'a').close()
    definitions.FILE_PROJECT_B = definitions.DIRECTORY_OUTPUT + "/project-B"
    open(definitions.FILE_PROJECT_B, 'a').close()
    definitions.FILE_PROJECT_C = definitions.DIRECTORY_OUTPUT + "/project-C"
    open(definitions.FILE_PROJECT_C, 'a').close()
    definitions.FILE_PROJECT_D = definitions.DIRECTORY_OUTPUT + "/project-D"
    open(definitions.FILE_PROJECT_D, 'a').close()
    definitions.FILE_VAR_MAP_STORE = definitions.DIRECTORY_OUTPUT + "/var-map-store"
    open(definitions.FILE_VAR_MAP_STORE, 'a').close()
    definitions.FILE_VEC_MAP_STORE = definitions.DIRECTORY_OUTPUT + "/vec-map-store"
    open(definitions.FILE_VEC_MAP_STORE, 'a').close()

    definitions.FILE_MISSING_FUNCTIONS = definitions.DIRECTORY_OUTPUT + "/missing-functions"
    open(definitions.FILE_MISSING_FUNCTIONS, 'a').close()
    definitions.FILE_MISSING_HEADERS = definitions.DIRECTORY_OUTPUT + "/missing-headers"
    open(definitions.FILE_MISSING_HEADERS, 'a').close()
    definitions.FILE_MISSING_MACROS = definitions.DIRECTORY_OUTPUT + "/missing-macros"
    open(definitions.FILE_MISSING_MACROS, 'a').close()
    definitions.FILE_MISSING_TYPES = definitions.DIRECTORY_OUTPUT + "/missing-types"
    open(definitions.FILE_MISSING_TYPES, 'a').close()

    if values.PATH_E:
        definitions.FILE_PROJECT_E = definitions.DIRECTORY_OUTPUT + "/project-E"
        open(definitions.FILE_PROJECT_E, 'a').close()
    Logger.create()


def read_conf_file():
    Emitter.normal("\treading configuration file")
    if not os.path.exists(values.FILE_CONFIGURATION):
        Emitter.normal("[NOT FOUND] Configuration file " + values.FILE_CONFIGURATION)
        exit()

    with open(values.FILE_CONFIGURATION, 'r') as conf_file:
        configuration_list = [i.strip() for i in conf_file.readlines()]

    for configuration in configuration_list:
        if definitions.CONF_PATH_A in configuration:
            values.PATH_A = configuration.replace(definitions.CONF_PATH_A, '')
            if "$HOME$" in values.PATH_A:
                values.PATH_A = values.PATH_A.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_B in configuration:
            values.PATH_B = configuration.replace(definitions.CONF_PATH_B, '')
            if "$HOME$" in values.PATH_B:
                values.PATH_B = values.PATH_B.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_C in configuration:
            values.PATH_C = configuration.replace(definitions.CONF_PATH_C, '')
            if "$HOME$" in values.PATH_C:
                values.PATH_C = values.PATH_C.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if str(values.PATH_C)[-1] == "/":
                values.PATH_C = values.PATH_C[:-1]
        elif definitions.CONF_PATH_E in configuration:
            values.PATH_E = configuration.replace(definitions.CONF_PATH_E, '')
            if "$HOME$" in values.PATH_E:
                values.PATH_E = values.PATH_E.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if str(values.PATH_E)[-1] == "/":
                values.PATH_E = values.PATH_E[:-1]

        elif definitions.CONF_COMMIT_A in configuration:
            values.COMMIT_A = configuration.replace(definitions.CONF_COMMIT_A, '')
        elif definitions.CONF_COMMIT_B in configuration:
            values.COMMIT_B = configuration.replace(definitions.CONF_COMMIT_B, '')
        elif definitions.CONF_COMMIT_C in configuration:
            values.COMMIT_C = configuration.replace(definitions.CONF_COMMIT_C, '')
        elif definitions.CONF_COMMIT_E in configuration:
            values.COMMIT_E = configuration.replace(definitions.CONF_COMMIT_E, '')

        elif definitions.CONF_PATH_POC in configuration:
            values.PATH_POC = configuration.replace(definitions.CONF_PATH_POC, '')
            if "$HOME$" in values.PATH_POC:
                values.PATH_POC = values.PATH_POC.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_FLAGS_A in configuration:
            values.BUILD_FLAGS_A = configuration.replace(definitions.CONF_FLAGS_A, '')
        elif definitions.CONF_FLAGS_C in configuration:
            values.BUILD_FLAGS_C = configuration.replace(definitions.CONF_FLAGS_C, '')
        elif definitions.CONF_CONFIG_COMMAND_A in configuration:
            values.CONFIG_COMMAND_A = configuration.replace(definitions.CONF_CONFIG_COMMAND_A, '')
        elif definitions.CONF_CONFIG_COMMAND_C in configuration:
            values.CONFIG_COMMAND_C = configuration.replace(definitions.CONF_CONFIG_COMMAND_C, '')
        elif definitions.CONF_BUILD_COMMAND_A in configuration:
            values.BUILD_COMMAND_A = configuration.replace(definitions.CONF_BUILD_COMMAND_A, '')
        elif definitions.CONF_BUILD_COMMAND_C in configuration:
            values.BUILD_COMMAND_C = configuration.replace(definitions.CONF_BUILD_COMMAND_C, '')
        elif definitions.CONF_ASAN_FLAG in configuration:
            values.ASAN_FLAG = configuration.replace(definitions.CONF_ASAN_FLAG, '')
        elif definitions.CONF_DIFF_SIZE in configuration:
            values.AST_DIFF_SIZE = configuration.replace(definitions.CONF_DIFF_SIZE, '')
        elif definitions.CONF_EXPLOIT_C in configuration:
            values.EXPLOIT_C = configuration.replace(definitions.CONF_EXPLOIT_C, '')
        elif definitions.CONF_VC in configuration:
            values.VC = configuration.replace(definitions.CONF_VC, '')
        elif definitions.CONF_LINUX_KERNEL in configuration:
            value = configuration.replace(definitions.CONF_LINUX_KERNEL, '')
            if "true" in value:
                values.IS_LINUX_KERNEL = True
            else:
                values.IS_LINUX_KERNEL = False
        elif definitions.CONF_BACKPORT in configuration:
            value = configuration.replace(definitions.CONF_BACKPORT, '')
            if "true" in value:
                values.BACKPORT = True
            else:
                values.BACKPORT = False


def reading_phase_settings():
    Emitter.normal("\treading phase configuration")


def read_conf():
    Emitter.normal("\treading configuration values")
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if definitions.ARG_DEBUG in arg:
                values.DEBUG = True
            elif definitions.ARG_DEBUG_DATA in arg:
                values.DEBUG_DATA = True
            elif definitions.ARG_SKIP_VEC_GEN in arg:
                values.SKIP_VEC_GEN = True
            elif definitions.ARG_SKIP_RESTORE in arg:
                values.SKIP_RESTORE = True
            elif definitions.ARG_USE_CACHE in arg:
                values.USE_CACHE = True
            elif definitions.ARG_BACKPORT in arg:
                values.BACKPORT = True
            elif definitions.ARG_FORK in arg:
                values.FORK = True
            elif definitions.ARG_CONF_FILE in arg:
                values.FILE_CONFIGURATION = str(arg).replace(definitions.ARG_CONF_FILE, '')
            elif definitions.ARG_LINUX_KERNEL in arg:
                values.IS_LINUX_KERNEL = True
            elif definitions.ARG_BREAK_WEAVE in arg:
                values.BREAK_WEAVE = True
            elif definitions.ARG_ANALYSE_NEIGHBORS in arg:
                values.ANALYSE_N = True
                values.ONLY_RESET = True
                for phase in values.PHASE_SETTING:
                    if phase in [definitions.PHASE_BUILD, definitions.PHASE_DIFF, definitions.PHASE_COMPARE]:
                        values.PHASE_SETTING[phase] = 1
                    else:
                        values.PHASE_SETTING[phase] = 0
            elif definitions.ARG_BUILD_AND_ANALYSE in arg:
                values.ANALYSE_N = True
                for phase in values.PHASE_SETTING:
                    if phase in [definitions.PHASE_BUILD, definitions.PHASE_DIFF, definitions.PHASE_COMPARE]:
                        values.PHASE_SETTING[phase] = 1
                    else:
                        values.PHASE_SETTING[phase] = 0
            elif "--skip" in arg:
                arg_phase = arg.replace("--skip-", "")
                values.PHASE_SETTING[arg_phase] = 0
            elif "--only" in arg:
                arg_phase = arg.replace("--only-", "")
                for phase in values.PHASE_SETTING:
                    if phase == arg_phase:
                        values.PHASE_SETTING[phase] = 1
                    else:
                        values.PHASE_SETTING[phase] = 0
            elif "Crochet.py" in arg:
                continue
            else:
                Emitter.normal("Invalid argument: " + arg)
                Emitter.help()
                exit()
    else:
        Emitter.help()
        exit()

    read_conf_file()

    # create log files and other directories
    conf_file_name = values.FILE_CONFIGURATION.split("/")[-1]
    project_name = values.FILE_CONFIGURATION.split("/")[-3]
    dir_name = project_name + "-" + conf_file_name.replace(".conf", "")

    definitions.DIRECTORY_OUTPUT = definitions.DIRECTORY_OUTPUT_BASE + "/" + dir_name
    definitions.DIRECTORY_TMP = definitions.DIRECTORY_OUTPUT + "/tmp"
    definitions.DIRECTORY_LOG = definitions.DIRECTORY_LOG_BASE + "/" + dir_name


def initialize():
    Emitter.title("Initializing project for Transfer")
    Emitter.sub_title("loading configuration")
    read_conf()
    create_directories()
    load_values()
    create_files()
    Emitter.sub_title("set environment")
    set_env_value()

