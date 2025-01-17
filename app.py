import streamlit as st
sss = st.session_state

import constants
import front_functions
import back_functions

import collections.abc
import sys
if not hasattr(collections, 'Iterable'):
    collections.Iterable = collections.abc.Iterable
import savReaderWriter

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

    if etln_reg and project_name:
        with st.form("form"):
            st.subheader("Выставьте настройки и запускайте")
            etln_settings_df = front_functions.create_etln_settings(etln_reg, project_name)
            merge_new = st.checkbox(
                label="Добавлять новые переменные в базу",
                help="Если выставлено, робот будет подливать в базу переменные, которые нашел в региональной базе, но их нет в эталоне. К переменной добавится префикс региона, где в первый раз ее нашли.",
                key="merge_new",
                value=False
            )

            launched = st.form_submit_button("Запустить объединение", disabled=etln_settings_df.empty)

        if launched:
            with st.sidebar:
                st.subheader("Статус")

            etln_settings_df = etln_settings_df.set_index("vars", drop=True)
            # etln_settings_df = etln_settings_df[etln_settings_df["include"]]

            placeholder = st.empty()

            # etln_settings_dict = etln_settings_df.to_dict(orient='index')
            back_functions.merge_bases(etln_reg, project_name, etln_settings_df)

            placeholder.success("Объединение завершено")

