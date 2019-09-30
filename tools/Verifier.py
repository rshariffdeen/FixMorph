#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import sys
from tools import Logger, Builder


def run_compilation():
    Logger.trace(__name__ + ":" + sys._getframe().f_code.co_name, locals())
    Builder.build_verify()
