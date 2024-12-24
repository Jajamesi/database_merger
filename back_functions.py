import streamlit as st
sss = st.session_state
import io

import pandas as pd
import pydataprocessing as dp

import os

import constants
import validations_funcs


def find_latest_base(directory, extensions=('.sav', '.zsav')):
    """
    Find the latest file with specified extensions in a given directory.

    :param directory: Path to the directory to search.
    :param extensions: Tuple of file extensions to consider.
    :return: Path to the latest file or None if no matching files are found.
    """
    latest_file = None
    latest_time = -1

    # Iterate through all files in the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                file_path = os.path.join(root, file)
                file_mod_time = os.path.getmtime(file_path)
                if file_mod_time > latest_time:
                    latest_file = file_path
                    latest_time = file_mod_time

    return latest_file

@st.cache_data
def create_setting_df(path_to_dir):

    if not validations_funcs.validate_folder(path_to_dir):
        st.error(f"Ошибка - папки с таким название не существует: {path_to_dir}")
        st.stop()

    path_to_sav = find_latest_base(path_to_dir)
    sss["etln_path"] = path_to_sav

    df, meta = dp.read_spss(path_to_sav)
    st.write(f"Эталонная база - {path_to_sav}")

    vars = meta.var_names
    labels = list(meta.var_names_to_labels.values())
    is_label_changeable = [False for _ in range(len(labels))]
    text_label_changeable = labels
    vals = [meta.var_value_labels[v] if v in meta.var_value_labels else None for v in vars]
    merge_values = [False for _ in range(len(labels))]
    how_merge = [None for _ in range(len(labels))]

    config_df = pd.DataFrame(
        {
            'vars': vars,
            'labels': labels,
            'is_label_changeable': is_label_changeable,
            'text_label_changeable': text_label_changeable,
            'vals': vals,
            'merge_values': merge_values,
            'how_merge': how_merge
        }
    )

    return config_df


@st.cache_data
def merge_bases(etln_reg: int, project_name: str, settings):


    res_df, res_meta = dp.read_spss(sss["etln_path"])
    res_meta.type_vars(res_df)

    for reg_i, reg_folder in constants.REGIONS_DICT.items():

        with st.sidebar:
            st.markdown(f"[{reg_folder}](#{reg_folder.replace(' ', '-')})", unsafe_allow_html=True)

        with (st.container(border=True)):
            st.subheader(reg_folder, anchor=reg_folder.replace(' ', '-'))

            # FOLDER CHECK
            reg_dir = os.path.join(constants.ROOT, constants.QUANT_DIR, reg_folder, project_name)
            if not validations_funcs.validate_folder(reg_dir):
                st.error(f"Ошибка - папки с таким название не существует: {reg_dir}")
                continue

            # FILE CHECK
            reg_file_path = find_latest_base(reg_dir)
            if reg_file_path is None:
                st.error(f"Ошибка - в папке {reg_folder} не найден ни один файл sav / zsav")
                continue

            # OPEN
            st.write(f"Используем файл - :blue[{reg_file_path}]")
            reg_df, reg_meta = dp.read_spss(reg_file_path)
            reg_meta.type_vars(reg_df)

            # Check each variable
            for res_var in res_meta.var_names:

                # TRY TO FIND BY VARIABLE LABEL
                res_v_label = res_meta.var_names_to_labels[res_var].strip().lower()

                # depending on type of search
                if settings.loc[res_var, "is_label_changeable"]:
                    changes = settings.loc[res_var, "text_label_changeable"].split(" ")
                    for change in changes:
                        res_v_label = res_v_label.replace(change.lower())
                    res_v_label = res_v_label.replace("  ", ' ')
                    res_v_label_parts = res_v_label.split(" ")

                    var_label_match = []
                    for k, v in reg_meta.var_value_labels.items():
                        if all([p in v for p in res_v_label_parts]):
                            var_label_match.append(k)
                            break
                else:
                    var_label_match = [k for k, v in reg_meta.var_value_labels.items() if v.strip().lower()==res_v_label]
                if not var_label_match:
                    st.error(f"Ошибка - нет соответствия по метке переменной для переменной {res_v_label}")
                    continue

                # SEVERAL VARIABLES AND NO VALUE LABELS TO CHECK
                if (res_var not in res_meta.var_value_labels) and (len(var_label_match)>1):
                    st.error(f"Ошибка - для переменной {res_v_label} сразу несколько переменных подходит по метке переменной")
                    continue

                # TRY TO FIND BY LABEL - IF IT HAS ANY
                if res_var in res_meta.var_value_labels:

                    for found_var in var_label_match:
                        if res_meta.q_type != "multipunch":
                            # CHECK IF LABELS MATCH
                            # IF ALLOW TO CONCAT - WORK DEPENDING ON FORMAT
                        else:
                            #LABELS SHOULD MATCH COMPLETELY








    return

