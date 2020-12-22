#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
import json
import os
from tools import logger


def read_json(file_path):
    logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    json_data = dict()
    if os.path.isfile(file_path):
        with open(file_path, 'r') as in_file:
            content = in_file.readline()
            json_data = json.loads(content)
    return json_data

