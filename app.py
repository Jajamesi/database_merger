import six
import streamlit as st
sss = st.session_state

import constants
import front_functions
import back_functions

st.set_page_config(layout="wide")

st.header("Объединение баз")

with st.container(
        border=True):

    st.subheader("Настройки")

    project_name = st.text_input(
        label="Укажите название проекта",
        help="По нему будет осуществляться поиск папки и базы"
    )

    etln_reg = st.selectbox(
        label = "Выберите эталонный регион",
        options = list(constants.REGIONS_DICT.keys()),
        index=None,
        format_func= lambda x: constants.REGIONS_DICT.get(x),
        key = "etln_reg",
        help = "База этого региона будет считаться *правильной* при сравнении с остальными в плане меток и т.д.",
        placeholder="Выберите регион"
    )

    if etln_reg:
        with st.form("form"):
            st.subheader("Выставьте настройки и запускайте")
            etln_settings_df = front_functions.create_etln_settings(etln_reg, project_name)
            launched = st.form_submit_button("Запустить объединение")

        if launched:
            etln_settings_df = etln_settings_df.set_index("vars", drop=True)
            # etln_settings_dict = etln_settings_df.to_dict(orient='index')
            back_functions.merge_bases(etln_reg, project_name, etln_settings_df)