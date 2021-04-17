#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
import os
import traceback
import signal
from tools import emitter, logger, configuration
from phases import building, differencing, detection, mapping, extraction, translation, \
    evolution, weaving, verify, summarizing, slicing, comparison, reversing
from common import definitions, values, utilities

time_info = {
    definitions.KEY_DURATION_INITIALIZATION: '0', definitions.KEY_DURATION_BUILD_ANALYSIS: '0',
    definitions.KEY_DURATION_DIFF_ANALYSIS: '0', definitions.KEY_DURATION_CLONE_ANALYSIS: '0',
    definitions.KEY_DURATION_SLICE: '0', definitions.KEY_DURATION_EXTRACTION: '0',
    definitions.KEY_DURATION_MAP_GENERATION: '0', definitions.KEY_DURATION_TRANSLATION: '0',
    definitions.KEY_DURATION_EVOLUTION: '0', definitions.KEY_DURATION_TRANSPLANTATION: '0',
    definitions.KEY_DURATION_VERIFICATION: '0', definitions.KEY_DURATION_COMPARISON: '0',
    definitions.KEY_DURATION_SUMMARIZATION: '0', definitions.KEY_DURATION_TOTAL: '0'
             }

start_time = 0


def set_env_value():
    emitter.normal("setting environment values")
    os.environ["PYTHONPATH"] = "/home/rshariffdeen/workspace/z3/build/python"
    utilities.execute_command("export PYTHONPATH=/home/rshariffdeen/workspace/z3/build/python")


def timeout_handler(signum, frame):
    emitter.error("TIMEOUT Exception")
    raise Exception("end of time")


def clean_data():
    temp_dir = definitions.DIRECTORY_TMP
    if os.path.isdir(temp_dir):
        clean_command = "rm -rf " + temp_dir + "/*"
        utilities.execute_command(clean_command)


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
    definitions.FILE_SOURCE_MAP_STORE = definitions.DIRECTORY_OUTPUT + "/source-map-store"
    open(definitions.FILE_SOURCE_MAP_STORE, 'a').close()
    definitions.FILE_MISSING_FUNCTIONS = definitions.DIRECTORY_OUTPUT + "/missing-functions"
    open(definitions.FILE_MISSING_FUNCTIONS, 'a').close()
    definitions.FILE_MISSING_HEADERS = definitions.DIRECTORY_OUTPUT + "/missing-headers"
    open(definitions.FILE_MISSING_HEADERS, 'a').close()
    definitions.FILE_MISSING_MACROS = definitions.DIRECTORY_OUTPUT + "/missing-macros"
    open(definitions.FILE_MISSING_MACROS, 'a').close()
    definitions.FILE_MISSING_TYPES = definitions.DIRECTORY_OUTPUT + "/missing-types"
    open(definitions.FILE_MISSING_TYPES, 'a').close()

    if values.CONF_PATH_E:
        definitions.FILE_PROJECT_E = definitions.DIRECTORY_OUTPUT + "/project-E"
        open(definitions.FILE_PROJECT_E, 'a').close()


def bootstrap(arg_list):
    emitter.title("Starting " + values.TOOL_NAME + " - Automated Code Transfer")
    emitter.sub_title("Loading Configurations")
    configuration.read_conf(arg_list)
    if values.FILE_CONFIGURATION:
        configuration.read_conf_file()
    configuration.update_configuration()
    configuration.update_phase_configuration(arg_list)
    configuration.print_configuration()
    set_env_value()
    utilities.clean_files()


def create_directories():
    if not os.path.isdir(definitions.DIRECTORY_LOG_BASE):
        os.makedirs(definitions.DIRECTORY_LOG_BASE)

    if not os.path.isdir(definitions.DIRECTORY_OUTPUT_BASE):
        os.makedirs(definitions.DIRECTORY_OUTPUT_BASE)

    if not os.path.isdir(definitions.DIRECTORY_BACKUP):
        os.makedirs(definitions.DIRECTORY_BACKUP)


def run(arg_list):
    global time_info, start_time
    create_directories()
    create_files()
    logger.create()
    start_time = time.time()

    time_check = time.time()
    bootstrap(arg_list)
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_INITIALIZATION] = str(duration)

    time_check = time.time()
    building.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_BUILD_ANALYSIS] = str(duration)

    time_check = time.time()
    differencing.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_DIFF_ANALYSIS] = str(duration)

    time_check = time.time()
    detection.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_CLONE_ANALYSIS] = str(duration)

    time_check = time.time()
    slicing.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_SLICE] = str(duration)

    time_check = time.time()
    extraction.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_EXTRACTION] = str(duration)

    time_check = time.time()
    mapping.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_MAP_GENERATION] = str(duration)

    time_check = time.time()
    translation.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_TRANSLATION] = str(duration)

    # time_check = time.time()
    # Reversing.start()
    # duration = format((time.time() - time_check) / 60, '.3f')
    # time_info[Definitions.KEY_DURATION_REVERSE] = str(duration)

    time_check = time.time()
    evolution.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_EVOLUTION] = str(duration)

    time_check = time.time()
    weaving.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_TRANSPLANTATION] = str(duration)

    time_check = time.time()
    verify.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_VERIFICATION] = str(duration)

    time_check = time.time()
    if values.CONF_PATH_E:
        comparison.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_COMPARISON] = str(duration)

    time_check = time.time()
    if values.CONF_PATH_E:
        summarizing.start()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_SUMMARIZATION] = str(duration)


def main():
    import sys
    is_error = False
    signal.signal(signal.SIGALRM, timeout_handler)
    try:
        run(sys.argv[1:])
    except KeyboardInterrupt as e:
        emitter.error("Program Interrupted by User")
        logger.error(traceback.format_exc())
        is_error = True
    except Exception as e:
        emitter.error("Runtime Error")
        emitter.error(str(e))
        logger.error(traceback.format_exc())
        is_error = True
    finally:
        # Final running time and exit message
        utilities.restore_slice_source()
        total_duration = format((time.time() - start_time) / 60, '.3f')
        time_info[definitions.KEY_DURATION_TOTAL] = str(total_duration)
        emitter.end(time_info, is_error)
        logger.end(time_info, is_error)
        logger.store()

