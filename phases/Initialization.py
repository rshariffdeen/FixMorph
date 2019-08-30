#! /usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import sys
from common.Utilities import err_exit, clean
from entity import Project
from common import Definitions
import tools.Emitter


def initialize():

    tools.Emitter.title("Initializing project for Transplantation")
    if len(sys.argv) > 1:
        Definitions.CONF_FILE_NAME = sys.argv[1]

    with open(Definitions.CONF_FILE_NAME, 'r', errors='replace') as conf_file:
        args = [i.strip() for i in conf_file.readlines()]

    if len(args) < 3:
        err_exit("Insufficient arguments: Pa, Pb, and Pc source paths required.")

    Definitions.Pa = Project.Project(args[0], "Pa")
    Definitions.Pb = Project.Project(args[1], "Pb")
    Definitions.Pc = Project.Project(args[2], "Pc")

    if len(args) >= 4:
        if os.path.isfile(args[3]):
            if len(args[3]) >= 4 and args[3][:-3] == ".sh":
                crash = args[3]
            else:
                tools.Emitter.warning("Script must be path to a shell (.sh) file. Running anyway.")
        else:
            tools.Emitter.warning("No script for crash provided. Running anyway.")
    else:
        tools.Emitter.warning("No script for crash provided. Running anyway.")
    clean()
