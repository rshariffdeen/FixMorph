#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
import time
import shutil
import subprocess
from common.utilities import execute_command
from entity import project
from common import definitions, values
from tools import emitter, logger


def read_conf_file():
    emitter.normal("\treading configuration file")
    if not os.path.exists(values.FILE_CONFIGURATION):
        emitter.normal("[NOT FOUND] Configuration file " + values.FILE_CONFIGURATION)
        exit()

    with open(values.FILE_CONFIGURATION, 'r') as conf_file:
        configuration_list = [i.strip() for i in conf_file.readlines()]

    for configuration in configuration_list:
        if definitions.CONF_PATH_A in configuration:
            values.CONF_PATH_A = configuration.replace(definitions.CONF_PATH_A, '')
            if "$HOME$" in values.CONF_PATH_A:
                values.CONF_PATH_A = values.CONF_PATH_A.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_B in configuration:
            values.CONF_PATH_B = configuration.replace(definitions.CONF_PATH_B, '')
            if "$HOME$" in values.CONF_PATH_B:
                values.CONF_PATH_B = values.CONF_PATH_B.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_PATH_C in configuration:
            values.CONF_PATH_C = configuration.replace(definitions.CONF_PATH_C, '')
            if "$HOME$" in values.CONF_PATH_C:
                values.CONF_PATH_C = values.CONF_PATH_C.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if str(values.CONF_PATH_C)[-1] == "/":
                values.CONF_PATH_C = values.CONF_PATH_C[:-1]
        elif definitions.CONF_PATH_E in configuration:
            values.CONF_PATH_E = configuration.replace(definitions.CONF_PATH_E, '')
            if "$HOME$" in values.CONF_PATH_E:
                values.CONF_PATH_E = values.CONF_PATH_E.replace("$HOME$", definitions.DIRECTORY_MAIN)
            if str(values.CONF_PATH_E)[-1] == "/":
                values.CONF_PATH_E = values.CONF_PATH_E[:-1]

        elif definitions.CONF_COMMIT_A in configuration:
            values.CONF_COMMIT_A = configuration.replace(definitions.CONF_COMMIT_A, '')
        elif definitions.CONF_COMMIT_B in configuration:
            values.CONF_COMMIT_B = configuration.replace(definitions.CONF_COMMIT_B, '')
        elif definitions.CONF_COMMIT_C in configuration:
            values.CONF_COMMIT_C = configuration.replace(definitions.CONF_COMMIT_C, '')
        elif definitions.CONF_COMMIT_E in configuration:
            values.CONF_COMMIT_E = configuration.replace(definitions.CONF_COMMIT_E, '')

        elif definitions.CONF_PATH_POC in configuration:
            values.CONF_PATH_POC = configuration.replace(definitions.CONF_PATH_POC, '')
            if "$HOME$" in values.CONF_PATH_POC:
                values.CONF_PATH_POC = values.CONF_PATH_POC.replace("$HOME$", definitions.DIRECTORY_MAIN)
        elif definitions.CONF_FLAGS_A in configuration:
            values.CONF_BUILD_FLAGS_A = configuration.replace(definitions.CONF_FLAGS_A, '')
        elif definitions.CONF_FLAGS_C in configuration:
            values.CONF_BUILD_FLAGS_C = configuration.replace(definitions.CONF_FLAGS_C, '')
        elif definitions.CONF_CONFIG_COMMAND_A in configuration:
            values.CONF_CONFIG_COMMAND_A = configuration.replace(definitions.CONF_CONFIG_COMMAND_A, '')
        elif definitions.CONF_CONFIG_COMMAND_C in configuration:
            values.CONF_CONFIG_COMMAND_C = configuration.replace(definitions.CONF_CONFIG_COMMAND_C, '')
        elif definitions.CONF_BUILD_COMMAND_A in configuration:
            values.CONF_BUILD_COMMAND_A = configuration.replace(definitions.CONF_BUILD_COMMAND_A, '')
        elif definitions.CONF_BUILD_COMMAND_C in configuration:
            values.CONF_BUILD_COMMAND_C = configuration.replace(definitions.CONF_BUILD_COMMAND_C, '')
        elif definitions.CONF_ASAN_FLAG in configuration:
            values.CONF_ASAN_FLAG = configuration.replace(definitions.CONF_ASAN_FLAG, '')
        elif definitions.CONF_DIFF_SIZE in configuration:
            values.CONF_AST_DIFF_SIZE = configuration.replace(definitions.CONF_DIFF_SIZE, '')
        elif definitions.CONF_EXPLOIT_C in configuration:
            values.CONF_EXPLOIT_C = configuration.replace(definitions.CONF_EXPLOIT_C, '')
        elif definitions.CONF_VC in configuration:
            values.CONF_VC = configuration.replace(definitions.CONF_VC, '')
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




def read_conf():
    emitter.normal("\treading configuration values")
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
                values.CONF_USE_CACHE = True
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
                emitter.normal("Invalid argument: " + arg)
                emitter.help()
                exit()
    else:
        emitter.help()
        exit()

    read_conf_file()




def initialize():
    emitter.title("Initializing project for Transfer")
    emitter.sub_title("loading configuration")
    read_conf()
    create_directories()
    load_values()
    create_files()
    emitter.sub_title("set environment")
    set_env_value()

