#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from tools import emitter, logger
from phases import initialization, building, differencing, detection, mapping, extraction, translation, \
    evolution, weaving, verify, summarizing, slicing, comparison, evaluation, reversing
from common import definitions
from common.utilities import error_exit, create_base_directories


def run():
    create_base_directories()
    emitter.start()
    start_time = time.time()
    time_info = dict()

    time_check = time.time()
    initialization.initialize()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_INITIALIZATION] = str(duration)

    time_check = time.time()
    building.build()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_BUILD_ANALYSIS] = str(duration)

    time_check = time.time()
    differencing.diff()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_DIFF_ANALYSIS] = str(duration)

    time_check = time.time()
    detection.detect()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_CLONE_ANALYSIS] = str(duration)

    time_check = time.time()
    slicing.slice()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_SLICE] = str(duration)

    time_check = time.time()
    extraction.extract()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_EXTRACTION] = str(duration)

    time_check = time.time()
    mapping.map()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_MAP_GENERATION] = str(duration)

    time_check = time.time()
    translation.translate()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_TRANSLATION] = str(duration)

    # time_check = time.time()
    # Reversing.reverse()
    # duration = format((time.time() - time_check) / 60, '.3f')
    # time_info[Definitions.KEY_DURATION_REVERSE] = str(duration)

    time_check = time.time()
    evolution.evolve()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_EVOLUTION] = str(duration)

    time_check = time.time()
    weaving.weave()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_TRANSPLANTATION] = str(duration)

    time_check = time.time()
    verify.verify()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[definitions.KEY_DURATION_VERIFICATION] = str(duration)

    # time_check = time.time()
    # Evaluation.evaluate()
    # duration = format((time.time() - time_check) / 60, '.3f')
    # time_info[Definitions.KEY_DURATION_EVALUATION] = str(duration)
    #
    # time_check = time.time()
    # Comparison.compare()
    # duration = format((time.time() - time_check) / 60, '.3f')
    # time_info[Definitions.KEY_DURATION_COMPARISON] = str(duration)
    #
    # time_check = time.time()
    # Summarizing.summarize()
    # duration = format((time.time() - time_check) / 60, '.3f')
    # time_info[Definitions.KEY_DURATION_SUMMARIZATION] = str(duration)

    # Final running time and exit message
    duration = format((time.time() - start_time) / 60, '.3f')
    time_info[definitions.KEY_DURATION_TOTAL] = str(duration)
    emitter.end(time_info)
    logger.end(time_info)
    
    
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt as e:
        error_exit("Program Interrupted by User")
