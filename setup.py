# -*- coding: utf-8 -*-
#
# pyshell setup script
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

from setuptools import setup


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(name='pyshell',
      version='0.1',
      description='Wrapper class for executing shell/git commands with logger support.',
      long_description=readme,
      classifiers=[
        'Development Status :: 1 - Planning',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2.7',
        'Topic :: Text Processing :: Linguistic',
      ],
      keywords='python git pyshell shell linux',
      url='https://github.com/knsathya/pyshell.git',
      author='Kuppuswamy Sathyanarayanan',
      author_email='sathyaosid@gmail.com',
      license='GPLv2',
      packages=['pyshell'],
      install_requires=[

      ],
      test_suite='tests',
      tests_require=[
          ''
      ],
      entry_points={
          'console_scripts': [''],
      },
      include_package_data=True,
      zip_safe=False)