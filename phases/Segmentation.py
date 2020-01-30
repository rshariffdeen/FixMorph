#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import time
from common.Utilities import error_exit, save_current_state, load_state
from common import Definitions, Values
from tools import Logger, Emitter, Differ, Writer, Merger, Reader

FILE_EXCLUDED_EXTENSIONS = ""
FILE_EXCLUDED_EXTENSIONS_A = ""
FILE_EXCLUDED_EXTENSIONS_B = ""
FILE_DIFF_C = ""
FILE_DIFF_H = ""
FILE_DIFF_ALL = ""
FILE_AST_SCRIPT = ""
FILE_AST_DIFF_ERROR = ""


def segment_code(diff_info):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())


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
    if not Values.diff_info:
        Values.diff_info = Reader.read_json(Definitions.FILE_DIFF_INFO)
        load_state()


def save_values():
    save_current_state()


def segment():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Segmentation of Code")
    load_values()
    if not Values.SKIP_SEGMENT:
        safe_exec(segment_code, "identifying segments")
        save_values()
    else:
        Emitter.special("\n\t-skipping this phase-")



