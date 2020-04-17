#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from common.Utilities import get_code, error_exit
from ast import Generator as ASTGenerator
from tools import Extractor, Oracle, Logger, Filter, Emitter


def slice_source_file(diff_info_list, path_a, path_b):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    source_list = dict()
    for diff_loc in diff_info_list:
        diff_info = diff_info_list[diff_loc]
        source_path = diff_loc.split(":")[0]
        if source_path not in source_list:
            source_list[source_path] = list()
        if path_a in source_path:
            source_list[source_path] = source_list[source_path] + diff_info['old-lines']
        else:
            source_list[source_path] = source_list[source_path] + diff_info['new-lines']


