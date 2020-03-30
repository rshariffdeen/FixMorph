#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.Utilities import error_exit, save_current_state, load_state
from common import Definitions, Values
from tools import Logger, Emitter, Identifier, Writer, Merger, Reader


def segment_code(diff_info):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Identifier.identify_code_segment(diff_info, Values.Project_A)


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


def load_values():
    if not Values.original_diff_info:
        Values.original_diff_info = Reader.read_json(Definitions.FILE_DIFF_INFO)
        load_state()


def save_values():
    save_current_state()


def segment():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Segmentation of Code")
    load_values()
    if not Values.SKIP_SEGMENT:
        safe_exec(segment_code, "identifying segments", Values.original_diff_info)
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")



