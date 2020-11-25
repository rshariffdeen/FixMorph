#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from tools import Emitter, Logger
from phases import Initialization, Building, Differencing, Detection, Mapping, Extraction, Translation, \
    Evolution, Weaving, Verify, Summarizing, Slicing, Comparison, Evaluation, Reversing
from common import Definitions
from common.Utilities import error_exit, create_base_directories


def first_run_check():
    create_base_directories()
    Initialization.read_conf()
    Initialization.create_directories()


def run():
    first_run_check()
    Emitter.start()
    start_time = time.time()
    time_info = dict()

    time_check = time.time()
    Initialization.initialize()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_INITIALIZATION] = str(duration)

    time_check = time.time()
    Building.build()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_BUILD_ANALYSIS] = str(duration)

    time_check = time.time()
    Differencing.diff()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_DIFF_ANALYSIS] = str(duration)

    time_check = time.time()
    Detection.detect()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_CLONE_ANALYSIS] = str(duration)

    time_check = time.time()
    Slicing.slice()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_SLICE] = str(duration)

    time_check = time.time()
    Extraction.extract()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_EXTRACTION] = str(duration)

    time_check = time.time()
    Mapping.map()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_MAP_GENERATION] = str(duration)

    time_check = time.time()
    Translation.translate()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_TRANSLATION] = str(duration)

    # time_check = time.time()
    # Reversing.reverse()
    # duration = format((time.time() - time_check) / 60, '.3f')
    # time_info[Definitions.KEY_DURATION_REVERSE] = str(duration)

    time_check = time.time()
    Evolution.evolve()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_EVOLUTION] = str(duration)

    time_check = time.time()
    Weaving.weave()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_TRANSPLANTATION] = str(duration)

    time_check = time.time()
    Verify.verify()
    duration = format((time.time() - time_check) / 60, '.3f')
    time_info[Definitions.KEY_DURATION_VERIFICATION] = str(duration)

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
    time_info[Definitions.KEY_DURATION_TOTAL] = str(duration)
    Emitter.end(time_info)
    Logger.end(time_info)
    
    
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt as e:
        error_exit("Program Interrupted by User")
