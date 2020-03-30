#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import time
from tools import Emitter, Logger
from phases import Initialization, Building, Differencing, Segmentation, Detection, Mapping, Extraction, Translation, Weaving, Verify, Analysis
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

    time_start = time.time()
    Initialization.initialize()
    time_info[Definitions.KEY_DURATION_INITIALIZATION] = str(time.time() - time_start)

    time_start = time.time()
    Building.build()
    time_info[Definitions.KEY_DURATION_BUILD_ANALYSIS] = str(time.time() - time_start)

    time_start = time.time()
    Differencing.diff()
    time_info[Definitions.KEY_DURATION_DIFF_ANALYSIS] = str(time.time() - time_start)

    time_start = time.time()
    Analysis.analyse()
    time_info[Definitions.KEY_DURATION_CLASSIFICATION] = str(time.time() - time_start)

    time_start = time.time()
    Segmentation.segment()
    time_info[Definitions.KEY_DURATION_SEGMENTATION] = str(time.time() - time_start)

    time_start = time.time()
    Detection.detect()
    time_info[Definitions.KEY_DURATION_CLONE_ANALYSIS] = str(time.time() - time_start)

    time_start = time.time()
    Extraction.extract()
    time_info[Definitions.KEY_DURATION_EXTRACTION] = str(time.time() - time_start)

    time_start = time.time()
    Mapping.map()
    time_info[Definitions.KEY_DURATION_MAP_GENERATION] = str(time.time() - time_start)

    time_start = time.time()
    Translation.translate()
    time_info[Definitions.KEY_DURATION_TRANSLATION] = str(time.time() - time_start)

    time_start = time.time()
    Weaving.weave()
    time_info[Definitions.KEY_DURATION_TRANSPLANTATION] = str(time.time() - time_start)

    time_check = time.time()
    Verify.verify()
    time_info[Definitions.KEY_DURATION_VERIFICATION] = str(time.time() - time_check)

    # Final running time and exit message
    time_info[Definitions.KEY_DURATION_TOTAL] = str(time.time() - start_time)
    Emitter.end(time_info)
    Logger.end(time_info)
    
    
if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt as e:
        error_exit("Program Interrupted by User")
