#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.utilities import error_exit, execute_command
from common import values, definitions
from tools import Logger, Emitter, Verifier, Fuzzer


DIR_FUZZ_INPUT = ""
DIR_FUZZ_OUTPUT_LOG = ""
FILE_EXPLOIT_OUTPUT = ""
ITERATION_COUNT = 5


def verify_compilation():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Verifier.run_compilation()


def verify_exploit():
    global FILE_EXPLOIT_OUTPUT
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Verifier.run_exploit(values.Project_C.path,
                         values.EXPLOIT_C,
                         values.Project_D.path,
                         values.PATH_POC,
                         FILE_EXPLOIT_OUTPUT,
                         definitions.crash_word_list
                         )


def commit_changes():
    commit_command = "cd " + values.Project_D.path + ";"
    commit_command += "git add *.c;"
    commit_command += "git add *.h;"
    commit_command += "git commit -m 'committing transplantation'"
    execute_command(commit_command)


def verify_behavior():
    global ITERATION_COUNT
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    total_errors = 0
    total_fixes = 0
    for i in range(0, ITERATION_COUNT):
        Emitter.sub_sub_title("Iteration " + str(i+1))
        file_extension = Fuzzer.generate_files(values.PATH_POC, DIR_FUZZ_INPUT)
        fixes, errors = Verifier.differential_test(file_extension, DIR_FUZZ_INPUT, values.EXPLOIT_C,
                                                   values.PATH_C, values.Project_D.path, DIR_FUZZ_OUTPUT_LOG)
        total_errors += errors
        total_fixes += fixes

    Emitter.sub_sub_title("Summary")
    Emitter.statistics("\t\tTotal test: " + str(100 * int(ITERATION_COUNT)))
    Emitter.statistics("\t\tTotal test that passed only in Pd: " + str(total_fixes))
    Emitter.statistics("\t\tTotal test that failed only in Pd: " + str(total_errors))
    Emitter.statistics("\t\tAverage test that passed only in Pd: " + str(total_fixes/int(ITERATION_COUNT)))
    Emitter.statistics("\t\tAverage test that failed only in Pd: " + str(total_errors/int(ITERATION_COUNT)))


def safe_exec(function_def, title, *args):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    Emitter.sub_title(title + "...")
    description = title[0].lower() + title[1:]
    try:
        Logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        Emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def set_values():
    global DIR_FUZZ_INPUT, DIR_FUZZ_OUTPUT_LOG, FILE_EXPLOIT_OUTPUT
    DIR_FUZZ_INPUT = definitions.DIRECTORY_OUTPUT + "/fuzz-input"
    DIR_FUZZ_OUTPUT_LOG = definitions.DIRECTORY_OUTPUT + "/fuzz-output"
    FILE_EXPLOIT_OUTPUT = definitions.DIRECTORY_OUTPUT + "/program-output"


def verify():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Patch Verification")
    set_values()

    if values.PHASE_SETTING[definitions.PHASE_VERIFY]:
        if not values.MODIFIED_SOURCE_LIST:
            error_exit("no modified sources to verify")
        safe_exec(verify_compilation, "verifying compilation")
        if values.PATH_POC:
            safe_exec(verify_exploit, "verifying exploit")
            safe_exec(verify_behavior, "verifying differential behavior")
        safe_exec(commit_changes, "committing changes to git")
    else:
        Emitter.special("\n\t-skipping this phase-")
