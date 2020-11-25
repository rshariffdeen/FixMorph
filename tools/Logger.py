# -*- coding: utf-8 -*-

import time
import datetime
import os
from common import Definitions
from shutil import copyfile


def create():
    with open(Definitions.FILE_MAIN_LOG, 'w+') as log_file:
        log_file.write("[Start] Crochet started at " + str(datetime.datetime.now()) + "\n")
    if os.path.exists(Definitions.FILE_LAST_LOG):
        os.remove(Definitions.FILE_LAST_LOG)
    if os.path.exists(Definitions.FILE_ERROR_LOG):
        os.remove(Definitions.FILE_ERROR_LOG)
    if os.path.exists(Definitions.FILE_COMMAND_LOG):
        os.remove(Definitions.FILE_COMMAND_LOG)
    with open(Definitions.FILE_LAST_LOG, 'w+') as last_log:
        last_log.write("[Start] Crochet started at " + str(datetime.datetime.now()) + "\n")


def log(log_message):
    if "COMMAND" in log_message:
        # if os.path.isfile(Definitions.FILE_COMMAND_LOG):
        with open(Definitions.FILE_COMMAND_LOG, 'a') as log_file:
            log_file.write(log_message)
    # if os.path.isfile(Definitions.FILE_MAIN_LOG):
    with open(Definitions.FILE_MAIN_LOG, 'a') as log_file:
        log_file.write(log_message)
    # if os.path.isfile(Definitions.FILE_LAST_LOG):
    with open(Definitions.FILE_LAST_LOG, 'a') as log_file:
        log_file.write(log_message)


def information(message):
    message = "[INFO]: " + str(message) + "\n"
    log(message)


def trace(function_name, arguments):
    message = "[TRACE]: " + function_name + ": " + str(arguments.keys()) + "\n"
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


def end(time_duration):
    output("[END] Crochet ended at " + str(datetime.datetime.now()) + "\n\n")
    output("\nTime duration\n----------------------\n\n")
    output("Initialization: " + time_duration[Definitions.KEY_DURATION_INITIALIZATION] + " minutes")
    output("Build: " + time_duration[Definitions.KEY_DURATION_BUILD_ANALYSIS] + " minutes")
    output("Diff Analysis: " + time_duration[Definitions.KEY_DURATION_DIFF_ANALYSIS] + " minutes")
    output("Slicing: " + time_duration[Definitions.KEY_DURATION_SLICE] + " minutes")
    output("Clone Analysis: " + time_duration[Definitions.KEY_DURATION_CLONE_ANALYSIS] + " minutes")
    output("AST Analysis: " + time_duration[Definitions.KEY_DURATION_EXTRACTION] + " minutes")
    output("Map Generation: " + time_duration[Definitions.KEY_DURATION_MAP_GENERATION] + " minutes")
    output("Translation: " + time_duration[Definitions.KEY_DURATION_TRANSLATION] + " minutes")
    output("Evolution: " + time_duration[Definitions.KEY_DURATION_EVOLUTION] + " minutes")
    output("Transplantation: " + time_duration[Definitions.KEY_DURATION_TRANSPLANTATION] + " minutes")
    output("Verification: " + time_duration[Definitions.KEY_DURATION_VERIFICATION] + " minutes")
    # output("Reverse Transplantation: " + time_duration[Definitions.KEY_DURATION_REVERSE] + " minutes")
    # output("Evaluation: " + time_duration[Definitions.KEY_DURATION_EVALUATION] + " minutes")
    # output("Comparison: " + time_duration[Definitions.KEY_DURATION_COMPARISON] + " minutes")
    # output("Summarizing: " + time_duration[Definitions.KEY_DURATION_SUMMARIZATION] + " minutes")
    output("\nCrochet finished successfully after " + time_duration[Definitions.KEY_DURATION_TOTAL] + " minutes\n")
    copyfile(Definitions.FILE_MAIN_LOG, Definitions.DIRECTORY_OUTPUT + "/main-log")

