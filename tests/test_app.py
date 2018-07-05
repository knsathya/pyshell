# -*- coding: utf-8 -*-
#
# pyshell test script
#
# Copyright (C) 2018 Sathya Kuppuswamy
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# @Author  : Sathya Kupppuswamy(sathyaosid@gmail.com)
# @History :
#            @v0.0 - Initial update
# @TODO    :
#
#

from __future__ import absolute_import

import os
import unittest
import pyshell
import logging
import re

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(message)s')
logger.setLevel(logging.INFO)

class PyShellTest(unittest.TestCase):
    def test_pyshell_ls(self):
        sh = pyshell.PyShell(logger=logger)
        ret = sh.cmd('ls')
        if ret[0] != 0:
            AssertionError("ls command failed\n")
        else:
            logger.info(ret[1])

    def test_pyshell_ps(self):
        sh = pyshell.PyShell(logger=logger)
        ret = sh.cmd('ps', '-aux')
        if ret[0] != 0:
            AssertionError("ps command failed\n")
        else:
            logger.info(ret[1])

    def test_git_version(self):
        git = pyshell.GitShell(logger=logger)
        version = git.cmd('--version')[1]
        if re.match(r'git version \d+\.\d+\.\d+', version):
            logger.info(version)
        else:
            AssertionError("Git version command failed")




if __name__ == '__main__':
    unittest.main()