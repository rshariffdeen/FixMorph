#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.Utilities import error_exit
from common import Values, Definitions
from tools import Logger, Emitter, Verifier


DIR_FUZZ_INPUT = ""
DIR_FUZZ_OUTPUT_LOG = ""


def verify_compilation():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Verifier.run_compilation()


# def verify_exploit():
#     Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
#     target_trace_info = Exploit.target_exit_code, Exploit.target_crashed, Exploit.FILE_EXPLOIT_OUTPUT_C
#     Verifier.run_exploit(target_trace_info,
#                          Values.EXPLOIT_C,
#                          Values.Project_D.path,
#                          Values.PATH_POC,
#                          Exploit.FILE_EXPLOIT_OUTPUT_D,
#                          Definitions.crash_word_list,
#                          Trace.crash_location_c
#                          )


# def verify_behavior():
#     Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
#     target_trace_info = Exploit.target_exit_code, Exploit.target_crashed, Exploit.FILE_EXPLOIT_OUTPUT_C
#     file_extension = Fuzzer.generate_files(Values.PATH_POC, DIR_FUZZ_INPUT)
#     Verifier.differential_test(file_extension, DIR_FUZZ_INPUT, Values.EXPLOIT_C,
#                                Values.PATH_C, Values.Project_D.path, DIR_FUZZ_OUTPUT_LOG)


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
        duration = str(time.time() - start_time)
        Emitter.success("\n\tSuccessful " + description + ", after " + duration + " seconds.")
    except Exception as exception:
        duration = str(time.time() - start_time)
        Emitter.error("Crash during " + description + ", after " + duration + " seconds.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def set_values():
    global DIR_FUZZ_INPUT, DIR_FUZZ_OUTPUT_LOG
    DIR_FUZZ_INPUT = Definitions.DIRECTORY_OUTPUT + "/fuzz-input"
    DIR_FUZZ_OUTPUT_LOG = Definitions.DIRECTORY_OUTPUT + "/fuzz-output"


def verify():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Patch Verification")
    set_values()
    if not Values.SKIP_VERIFY:
        safe_exec(verify_compilation, "verifying compilation")
    # safe_exec(verify_exploit, "verifying exploit")
    # safe_exec(verify_behavior, "verifying differential behavior")
