#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
from app.tools import builder, db, emitter, logger
from app.common.utilities import error_exit
from app.common import values, definitions


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
        if values.IS_TRAINING:
            db.mark_pair_as_error(values.CONF_COMMIT_B, values.CONF_COMMIT_E)
        emitter.error("Crash during " + description + ", after " + duration + " minutes.")
        error_exit(exception, "Unexpected error during " + description + ".")
    return result


def start():
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    if values.PHASE_SETTING[definitions.PHASE_BUILD]:
        emitter.title("Building Projects")
        safe_exec(builder.build_normal, "building binaries")


