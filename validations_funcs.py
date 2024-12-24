import pandas as pd
import pydataprocessing as dp

import streamlit as st

import os

def validate_folder(path: str):
    if not os.path.exists(path):
        return False
    return True