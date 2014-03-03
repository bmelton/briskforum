#!/usr/bin/env python

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
os.environ["DJANGO_SETTINGS_MODULE"] = "brisk.runtests.settings"

import django
from django.conf import settings
from django.test.utils import get_runner

def main():
    # TestRunner = get_runner(settings)
    # test_runner = TestRunner()
    return True

if __name__=="__main__":
    main()
