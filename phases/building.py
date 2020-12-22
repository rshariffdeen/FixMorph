#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
from tools import emitter, builder, logger
from common.utilities import error_exit
from common import values, definitions


def safe_exec(function_def, title, *args):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    start_time = time.time()
    emitter.sub_title(title)
    description = title[0].lower() + title[1:]
    try:
        logger.information("running " + str(function_def))
        if not args:
            result = function_def()
        else:
            result = function_def(*args)
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.success("\n\tSuccessful " + description + ", after " + duration + " minutes.")
    except Exception as exception:
        duration = format((time.time() - start_time) / 60, '.3f')
        emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def build():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    emitter.title("Building Projects")
    if values.PHASE_SETTING[definitions.PHASE_BUILD]:
        safe_exec(builder.build_normal, "building binaries")
    else:
        emitter.special("\n\t-skipping this phase-")

