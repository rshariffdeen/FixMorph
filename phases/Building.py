#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
from tools import Emitter, Builder, Logger
from common.Utilities import error_exit
from common import Values, Definitions


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


def build():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Emitter.title("Building Projects")
    if Values.PHASE_SETTING[Definitions.PHASE_BUILD]:
        safe_exec(Builder.build_normal, "building binaries")
    else:
        Emitter.special("\n\t-skipping this phase-")

