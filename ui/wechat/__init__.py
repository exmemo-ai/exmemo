import os

if 'TEST' not in os.environ:
    from .exmemo import *
