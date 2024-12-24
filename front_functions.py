import streamlit as st

import os

import back_functions
import constants

sss = st.session_state

def create_etln_settings(etln_reg: int, project_name: str):


    path_to_dir = os.path.join(constants.ROOT, constants.QUANT_DIR, constants.REGIONS_DICT[etln_reg], project_name)
    df = back_functions.create_setting_df(path_to_dir)

    settings = st.data_editor(
        data=df,
        hide_index=True,
        column_config={
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
