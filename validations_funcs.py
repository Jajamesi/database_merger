import pandas as pd
import pydataprocessing as dp

import streamlit as st

import os

def validate_folder(path: str):
    if not os.path.exists(path):
        return False
    return True


def check_var_existence(var_name, var_names):
    if var_name in var_names:
        return True
    return False


def check_df_empty(df):
    return df.empty