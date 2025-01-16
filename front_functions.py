import streamlit as st

import os

import back_functions
import constants
import pandas as pd

sss = st.session_state

def create_etln_settings(etln_reg: int, project_name: str):


    # path_to_dir = os.path.join(constants.ROOT, constants.QUANT_DIR, constants.REGIONS_DICT[etln_reg], project_name)
    path_to_dir = back_functions.find_project_dir(os.path.join(constants.ROOT, constants.QUANT_DIR, constants.REGIONS_DICT[etln_reg]), project_name)

    sss["etln_path"] = os.path.join(path_to_dir, f"{etln_reg}.sav")

    if path_to_dir is not None:
        try:
            df = back_functions.create_setting_df(sss["etln_path"])

            settings = st.data_editor(
                data=df,
                hide_index=True,
                column_config={
                    "include": st.column_config.CheckboxColumn(
                        label="Включить",
                        required=True
                    ),
                    "vars": st.column_config.Column(
                        label="Переменные",
                        disabled=True
                    ),
                    "labels": st.column_config.Column(
                        label="Метки переменных",
                        disabled=True
                    ),
                    "is_label_changeable": st.column_config.CheckboxColumn(
                        label="Объединять отличающиеся метки",
                        required =True
                    ),
                    "text_label_changeable": st.column_config.Column(
                        label="Допустимые изменения",
                        disabled=False
                    ),
                    "vals": st.column_config.Column(
                        label="Значения",
                        disabled=True
                    ),
                    "merge_values": st.column_config.CheckboxColumn(
                        label="Объединять отличия в значениях",
                        required=True
                    ),
                    "how_merge": st.column_config.SelectboxColumn(
                        label="Как объединять",
                        options=["По коду", "По метке"]
                    ),
                }
            )

            return settings
        except Exception as e:
            raise (e)
    return pd.DataFrame()
