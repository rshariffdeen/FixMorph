#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import json
from tools import Logger


def read_json(file_path):
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    with open(file_path, 'r') as in_file:
        content = in_file.readline()
        json_data = json.loads(content)
        return json_data

