# SaaS Core — Package Root
import os
__path__ = [os.path.dirname(os.path.abspath(__file__))]
from .app import create_app
