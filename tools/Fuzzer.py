#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from tools import Logger, Emitter
from common.utilities import execute_command


def generate_files(poc_path, output_directory):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    count = 100
    file_extension = poc_path.split(".")[-1]
    Emitter.normal("\tgenerating fuzzed inputs")
    for i in range(0, 100):
        generate_command = "radamsa " + str(poc_path) + " > " + output_directory + "/" + str(i) + "." + file_extension
        execute_command(generate_command)
    Emitter.normal("\t\t[completed] generating 100 fuzzed input files")
    return file_extension
