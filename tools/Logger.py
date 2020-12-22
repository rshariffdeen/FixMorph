# -*- coding: utf-8 -*-

import time
import datetime
import os
from common import definitions, values
from shutil import copyfile


def create():
    log_file_name = "log-" + str(time.time())
    log_file_path = definitions.DIRECTORY_LOG + "/" + log_file_name
    definitions.FILE_MAIN_LOG = log_file_path
    with open(definitions.FILE_MAIN_LOG, 'w+') as log_file:
        log_file.write("[Start] Crochet started at " + str(datetime.datetime.now()) + "\n")
    if os.path.exists(definitions.FILE_LAST_LOG):
        os.remove(definitions.FILE_LAST_LOG)
    if os.path.exists(definitions.FILE_ERROR_LOG):
        os.remove(definitions.FILE_ERROR_LOG)
    if os.path.exists(definitions.FILE_COMMAND_LOG):
        os.remove(definitions.FILE_COMMAND_LOG)
    with open(definitions.FILE_LAST_LOG, 'w+') as last_log:
        last_log.write("[Start] Crochet started at " + str(datetime.datetime.now()) + "\n")


def log(log_message):
    if "COMMAND" in log_message:
        # if os.path.isfile(Definitions.FILE_COMMAND_LOG):
        with open(definitions.FILE_COMMAND_LOG, 'a') as log_file:
            log_file.write(log_message)
    # if os.path.isfile(Definitions.FILE_MAIN_LOG):
    with open(definitions.FILE_MAIN_LOG, 'a') as log_file:
        log_file.write(log_message)
    # if os.path.isfile(Definitions.FILE_LAST_LOG):
    with open(definitions.FILE_LAST_LOG, 'a') as log_file:
        log_file.write(log_message)


def information(message):
    message = "[INFO]: " + str(message) + "\n"
    log(message)


def trace(function_name, arguments):
    message = "[TRACE]: " + function_name + ": " + str(arguments.keys()) + "\n"
    log(message)


def note(message):
    message = str(message).strip().lower().replace("[note]", "")
    message = "[NOTE]: " + str(message) + "\n"
    log(message)


def command(message):
    message = "[COMMAND]: " + str(message) + "\n"
    log(message)


def error(message):
    message = "[ERROR]: " + str(message) + "\n"
    log(message)


def output(message):
    log(message + "\n")


def warning(message):
    message = "[WARNING]: " + str(message) + "\n"
    log(message)


def data(message, data=None, is_patch=False):
    if values.DEBUG_DATA or is_patch:
        message = str(message).strip()
        message = "[DATA]: " + str(message) + "\n"
        log(message)
        if data:
            data = "[DATA]: " + str(data) + "\n"
            log(data)


def debug(message):
    message = str(message).strip()
    message = "[DEBUG]: " + str(message) + "\n"
    log(message)


def end(time_duration):
    output("[END] Crochet ended at " + str(datetime.datetime.now()) + "\n\n")
    output("\nTime duration\n----------------------\n\n")
    output("Initialization: " + time_duration[definitions.KEY_DURATION_INITIALIZATION] + " minutes")
    output("Build: " + time_duration[definitions.KEY_DURATION_BUILD_ANALYSIS] + " minutes")
    output("Diff Analysis: " + time_duration[definitions.KEY_DURATION_DIFF_ANALYSIS] + " minutes")
    output("Slicing: " + time_duration[definitions.KEY_DURATION_SLICE] + " minutes")
    output("Clone Analysis: " + time_duration[definitions.KEY_DURATION_CLONE_ANALYSIS] + " minutes")
    output("AST Analysis: " + time_duration[definitions.KEY_DURATION_EXTRACTION] + " minutes")
    output("Map Generation: " + time_duration[definitions.KEY_DURATION_MAP_GENERATION] + " minutes")
    output("Translation: " + time_duration[definitions.KEY_DURATION_TRANSLATION] + " minutes")
    output("Evolution: " + time_duration[definitions.KEY_DURATION_EVOLUTION] + " minutes")
    output("Transplantation: " + time_duration[definitions.KEY_DURATION_TRANSPLANTATION] + " minutes")
    output("Verification: " + time_duration[definitions.KEY_DURATION_VERIFICATION] + " minutes")
    # output("Reverse Transplantation: " + time_duration[Definitions.KEY_DURATION_REVERSE] + " minutes")
    # output("Evaluation: " + time_duration[Definitions.KEY_DURATION_EVALUATION] + " minutes")
    # output("Comparison: " + time_duration[Definitions.KEY_DURATION_COMPARISON] + " minutes")
    # output("Summarizing: " + time_duration[Definitions.KEY_DURATION_SUMMARIZATION] + " minutes")
    output("\nCrochet finished successfully after " + time_duration[definitions.KEY_DURATION_TOTAL] + " minutes\n")
    copyfile(definitions.FILE_MAIN_LOG, definitions.DIRECTORY_OUTPUT + "/main-log")

