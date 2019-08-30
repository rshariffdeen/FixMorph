#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
from common import Definitions, Values
from tools import Emitter, Builder, Logger, Collector, Oracle, Identifier
from common.Utilities import error_exit

FILE_EXPLOIT_OUTPUT_A = ""
FILE_EXPLOIT_OUTPUT_B = ""
FILE_EXPLOIT_OUTPUT_C = ""
FILE_EXPLOIT_OUTPUT_D = ""

donor_exit_code = ""
target_exit_code = ""
donor_crashed = False
target_crashed = False

target_suspect_line_list = list()
donor_suspect_line_list = dict()
donor_fixed_error_list = list()


def test_exploits():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    global donor_exit_code, target_exit_code, donor_crashed, target_crashed

    exploit_command = Values.EXPLOIT_A
    project_path = Values.PATH_A
    poc_path = Values.PATH_POC
    return_code, program_crashed, output = Exploiter.run_exploit(exploit_command,
                                                                 project_path,
                                                                 poc_path,
                                                                 FILE_EXPLOIT_OUTPUT_A)

    exploit_command = Values.EXPLOIT_A
    project_path = Values.PATH_B
    poc_path = Values.PATH_POC
    return_code, program_crashed, output = Exploiter.run_exploit(exploit_command,
                                                                 project_path,
                                                                 poc_path,
                                                                 FILE_EXPLOIT_OUTPUT_B)

    exploit_command = Values.EXPLOIT_C
    project_path = Values.PATH_C
    poc_path = Values.PATH_POC
    return_code, program_crashed, output = Exploiter.run_exploit(exploit_command,
                                                                 project_path,
                                                                 poc_path,
                                                                 FILE_EXPLOIT_OUTPUT_C)


def collect_exploit_info():
    global donor_exit_code, target_exit_code
    global donor_crashed, target_crashed
    global donor_suspect_line_list, target_suspect_line_list
    global donor_fixed_error_list

    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())

    Emitter.sub_sub_title(Values.PATH_A)
    donor_exit_code = Collector.collect_exploit_return_code(FILE_EXPLOIT_OUTPUT_A)
    donor_output = Collector.collect_exploit_output(FILE_EXPLOIT_OUTPUT_A)
    donor_crashed = Oracle.did_program_crash(donor_output)
    donor_suspect_line_list = Collector.collect_suspicious_points(FILE_EXPLOIT_OUTPUT_A)

    donor_fixed_output = Collector.collect_exploit_output(FILE_EXPLOIT_OUTPUT_B)
    donor_fixed_error_list = Identifier.identify_fixed_errors(donor_output, donor_fixed_output)

    Emitter.special("\tFixed Errors")
    Emitter.program_output(donor_fixed_error_list)

    Emitter.sub_sub_title(Values.PATH_C)
    target_exit_code = Collector.collect_exploit_return_code(FILE_EXPLOIT_OUTPUT_C)
    target_output = Collector.collect_exploit_output(FILE_EXPLOIT_OUTPUT_C)
    target_crashed = Oracle.did_program_crash(target_output)
    target_suspect_line_list = Collector.collect_suspicious_points(FILE_EXPLOIT_OUTPUT_C)
    # print(target_crashed, donor_crashed)
    # print(target_exit_code, donor_exit_code)
    # print(donor_output)
    # print(target_output)
    can_fix = False
    for error_fixed in donor_fixed_error_list:
        for output_line in target_output:
            if error_fixed in output_line:
                can_fix = True

    if not can_fix:
        Emitter.warning("Warning: No fixed error which is common")


def safe_exec(function_def, title, *args):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    Emitter.sub_title(title)
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
    global FILE_EXPLOIT_OUTPUT_A, FILE_EXPLOIT_OUTPUT_B
    global FILE_EXPLOIT_OUTPUT_C, FILE_EXPLOIT_OUTPUT_D
    FILE_EXPLOIT_OUTPUT_A = Definitions.DIRECTORY_OUTPUT + "/exploit-log-a"
    FILE_EXPLOIT_OUTPUT_B = Definitions.DIRECTORY_OUTPUT + "/exploit-log-b"
    FILE_EXPLOIT_OUTPUT_C = Definitions.DIRECTORY_OUTPUT + "/exploit-log-c"
    FILE_EXPLOIT_OUTPUT_D = Definitions.DIRECTORY_OUTPUT + "/exploit-log-d"


def exploit():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Exploiting vulnerability")
    set_values()
    if not Values.SKIP_EXPLOIT:
        if Values.ASAN_FLAG == "":
            safe_exec(Builder.build_normal, "building binaries")
        else:
            safe_exec(Builder.build_asan, "building binaries")
        safe_exec(test_exploits, "testing exploit case")

    safe_exec(collect_exploit_info, "collecting exploit information")