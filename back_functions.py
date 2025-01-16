import streamlit as st
sss = st.session_state
import io
from collections import defaultdict
import pandas as pd
import pydataprocessing as dp

import os

import constants
import validations_funcs


import warnings
from pandas.errors import PerformanceWarning

# Suppress PerformanceWarning
warnings.simplefilter("ignore", PerformanceWarning)
warnings.simplefilter('ignore', FutureWarning)

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


def find_project_dir(directory, project_name):
    entries = os.listdir(directory)

    directories = [entry for entry in entries if os.path.isdir(os.path.join(directory, entry))]

    if not directories:
        st.error(f"Ошибка1 - папки с таким название не существует: {directory}/{project_name}")
        return None

    suitable_dirs = [d for d in directories if project_name in d]

    if len(suitable_dirs)>1:
        st.error(f"Ошибка2 - найдено несколько папок с проектом: {directory}/{project_name}")
        return None
    elif not suitable_dirs:
        st.error(f"Ошибка3 - папки с таким название не существует: {directory}/{project_name}")
        return None

    return os.path.join(directory, suitable_dirs[0])


def find_reg_base(directory, reg_id):
    file_path = os.path.join(directory, f"{reg_id}.sav")
    if os.path.exists(file_path):
        return file_path
    return None

@st.cache_data
def create_setting_df(path_to_dir):

    if not validations_funcs.validate_folder(path_to_dir):
        st.error(f"Ошибка - папки с таким название не существует: {path_to_dir}")
        return None

    # path_to_sav = find_latest_base(path_to_dir)
    path_to_sav = path_to_dir

    df, meta = dp.read_spss(path_to_sav)
    st.write(f"Эталонная база - {path_to_sav}")

    include = [True for _ in range(len(meta.var_names))]
    vars = meta.var_names
    labels = list(meta.var_names_to_labels.values())
    is_label_changeable = [False for _ in range(len(labels))]
    text_label_changeable = labels
    vals = [meta.var_value_labels[v] if v in meta.var_value_labels else None for v in vars]
    merge_values = [False for _ in range(len(labels))]
    how_merge = [None for _ in range(len(labels))]

    config_df = pd.DataFrame(
        {
            'include': include,
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

    log_content = str()

    res_df, res_meta = dp.read_spss(sss["etln_path"])

    for var in settings[~settings["include"]].index:
        res_meta = del_from_meta(res_meta, var)
        res_df = res_df.drop(var, axis=1)

    res_meta.type_vars(res_df)

    for reg_i, reg_folder in constants.REGIONS_DICT.items():

        log_content += '\n\n' + reg_folder

        if reg_i==etln_reg:
            continue

        st.sidebar.markdown(f"[{reg_folder}](#{reg_folder.replace(' ', '-')})", unsafe_allow_html=True)

        with (st.container(border=True)):
            st.subheader(reg_folder, anchor=reg_folder.replace(' ', '-'))

            # FOLDER CHECK
            # changed to find reg directory
            # reg_dir = os.path.join(constants.ROOT, constants.QUANT_DIR, reg_folder, project_name)
            reg_dir = find_project_dir(os.path.join(constants.ROOT, constants.QUANT_DIR, reg_folder), project_name)
            if reg_dir is None:
                continue

            if not validations_funcs.validate_folder(reg_dir):
                e = f"Внимание: База не подлита! Ошибка - папки с таким название не существует: {reg_dir}. Проверьте наличие и/или название папки."
                log_content+= '\n' + e
                st.error(e)
                continue

            # FILE CHECK
            # reg_file_path = find_latest_base(reg_dir)
            reg_file_path = find_reg_base(reg_dir, reg_i) # changed to format "reg_id.sav"
            if reg_file_path is None:
                e = f"Внимание: База не подлита! Ошибка - в папке {reg_folder} не найдена база. Проверьте наличие файла и/или его название."
                log_content += '\n' + e
                st.error(e)
                continue

            # OPEN
            st.write(f"Используем файл - :blue[{reg_file_path}]")

            try:
                reg_df, reg_meta = dp.read_spss(reg_file_path)
            except TypeError:
                e = f"Внимание: База не подлита! Не удалось обработать базу - проверьте, что в базе есть наблюдения"
                log_content += '\n' + e
                st.error(e)
                continue

            FOUND_VARS = set()

            reg_meta.type_vars(reg_df)
            reg_fin_df = pd.DataFrame()

            if validations_funcs.check_df_empty(reg_df):
                e = f"Внимание: База не подлита! Не удалось обработать базу - проверьте, что в базе есть наблюдения"
                log_content += '\n' + e
                st.error(e)
                continue

            # VARIABLES VALIDATIONS
            support_vars = [v for v, t in res_meta.q_type.items() if t in {"technical", "weight"}]
            for var_ in support_vars:
                if not validations_funcs.check_var_existence(var_, reg_meta.var_names):
                    e = f"База подлита не полностью! В базе `{reg_i}.sav` нет переменной {var_}"
                    log_content += '\n' + e
                    st.error(e)

            # Check each variable
            for res_var_ind, res_var in enumerate(res_meta.var_names):

                # TRY TO FIND BY VARIABLE LABEL
                res_v_label = res_meta.var_names_to_labels[res_var].strip().lower()

                # depending on type of search
                if settings.loc[res_var, "is_label_changeable"]:
                    changes = settings.loc[res_var, "text_label_changeable"].split(" ")
                    st.write(changes)
                    for change in changes:
                        res_v_label = res_v_label.replace(change.lower(), "")
                    res_v_label = res_v_label.replace("  ", ' ')
                    res_v_label_parts = res_v_label.split(" ")
                    res_v_label_parts = [p for p in res_v_label_parts if p != ""]

                    st.write(res_v_label_parts)

                    var_label_match = []
                    for k, v in reg_meta.var_names_to_labels.items():
                        if all([p in v.lower() for p in res_v_label_parts]):
                            var_label_match.append(k)
                            break
                else:
                    var_label_match = [k for k, v in reg_meta.var_names_to_labels.items() if v.strip().lower()==res_v_label]

                if (not var_label_match) and (res_meta.q_type[res_var] not in {"technical", "weight"}):
                    e = f"Ошибка - нет соответствия по метке переменной для переменной {res_var} '{res_v_label}' в базе `{reg_i}.sav`"
                    log_content += '\n' + e
                    st.error(e)
                    continue


                # SEVERAL VARIABLES AND NO VALUE LABELS TO CHECK - TAKE ONE WITH MATCHING PREVIOUS VARIABLE
                if (res_var not in res_meta.var_value_labels):
                    if (len(var_label_match)>1):

                        previous_res_var = res_meta.var_names[res_var_ind-1]
                        previous_res_var_label = res_meta.var_names_to_labels[previous_res_var]
                        for potential_found in var_label_match:
                            prev_pot_found = reg_meta.var_names[reg_meta.var_names.index(potential_found)-1]
                            prev_pot_found_label =reg_meta.var_names_to_labels[prev_pot_found]
                            if previous_res_var_label == prev_pot_found_label:
                                reg_fin_df[res_var] = reg_df[potential_found]
                                FOUND_VARS.add(potential_found)

                                # WEIGHTS ARE NUMERIC
                                if res_meta.q_type[res_var] == "weight":
                                    is_numeric = pd.api.types.is_numeric_dtype(reg_df[res_var])
                                    # is_numeric = pd.to_numeric(reg_df[found_var].dropna(), errors='coerce').notna().all()
                                    if not is_numeric:
                                        e = f"Ошибка - в базе переменной {res_var} есть не числовые значения"
                                        log_content += '\n' + e
                                        st.error(e)
                                break
                        else:
                            e = f"Ошибка - для переменной {res_var} '{res_v_label}' сразу несколько переменных подходит по метке переменной"
                            log_content += '\n' + e
                            st.error(e)
                            continue


                        # if res_var in var_label_match:
                        #     reg_fin_df[res_var] = reg_df[res_var]
                        #     FOUND_VARS.add(res_var)
                        #     # WEIGHTS ARE NUMERIC
                        #     if res_meta.q_type[res_var] == "weight":
                        #         is_numeric = pd.api.types.is_numeric_dtype(reg_df[res_var])
                        #         # is_numeric = pd.to_numeric(reg_df[found_var].dropna(), errors='coerce').notna().all()
                        #         if not is_numeric:
                        #             e = f"Ошибка - в базе переменной {res_var} есть не числовые значения"
                        #             log_content += '\n' + e
                        #             st.error(e)
                        # else:
                        #     e = f"Ошибка - для переменной {res_var} '{res_v_label}' сразу несколько переменных подходит по метке переменной"
                        #     log_content += '\n' + e
                        #     st.error(e)
                        #     continue

                    elif len(var_label_match)==1:
                        # print(res_var)
                        # print(var_label_match)
                        found_var = var_label_match[0]
                        # OPEN AND TECH VARIABLE JUST MERGE AS IS
                        reg_fin_df[res_var] = reg_df[found_var]
                        FOUND_VARS.add(found_var)

                        # WEIGHTS ARE NUMERIC
                        if res_meta.q_type[res_var] == "weight":
                            is_numeric = pd.api.types.is_numeric_dtype(reg_df[found_var])
                            # is_numeric = pd.to_numeric(reg_df[found_var].dropna(), errors='coerce').notna().all()
                            if not is_numeric:
                                e = f"Ошибка - в базе переменной {found_var} есть не числовые значения"
                                log_content += '\n' + e
                                st.error(e)

                        continue



                # TRY TO FIND BY LABEL - IF IT HAS ANY
                if res_var in res_meta.var_value_labels:
                    clean_found_flag = False

                    for found_var in var_label_match:
                        # FOR NOT MULTIPUNCHES ALWAYS SHOULD BE HERE
                        # CHECK IF LABELS MATCH
                        if res_meta.var_value_labels[res_var] == reg_meta.var_value_labels[found_var]:
                            # just merge
                            reg_fin_df[res_var] = reg_df[found_var]
                            FOUND_VARS.add(found_var)

                            # ADDITIONAL CHECK FOR INDEX MATCH FOR MULTIPUNCHES
                            if res_meta.q_type[res_var] == "multipunch":
                                if res_var.split('_')[-1] != found_var.split('_')[-1]:
                                    e = f"Не совпадают индексы в MRSet`e {res_var} в эталоне и {found_var} в `{reg_i}.sav`"
                                    log_content += '\n' + e
                                    st.warning(e)

                            clean_found_flag = True
                            break

                    # IF NO GOOD MATCH FOR SINGLEPUNCHES USE THE FIRST FOUND AND MATCH
                    if not clean_found_flag:
                        found_var = var_label_match[0]
                        if res_meta.q_type[found_var] != "multipunch":
                            # IF ALLOW TO CONCAT - WORK DEPENDING ON FORMAT
                            if settings.loc[res_var, "merge_values"]:
                                # transfer new codes values to res_meta
                                if settings.loc[res_var, "how_merge"] == "По коду":
                                    for code in reg_meta.var_value_labels[found_var]:
                                        if code not in res_meta.var_value_labels[res_var]:
                                            res_meta.var_value_labels[res_var].update({code: reg_meta.var_value_labels[found_var][code]})
                                    reg_fin_df[res_var] = reg_df[found_var]
                                    FOUND_VARS.add(found_var)
                                    e = f"Подлил наиболее похожую {found_var} в {res_var} ответы по коду ответа из файла `{reg_i}.sav`. Проверьте базу."
                                    log_content += '\n' + e
                                    st.warning(e)
                                elif settings.loc[res_var, "how_merge"] == "По метке":
                                    reverse_res_val_labels = {v:k for k, v in res_meta.var_value_labels[res_var].items()}
                                    replace_dict = {}
                                    max_res_code = len(reverse_res_val_labels)
                                    for code, label in reg_meta.var_value_labels[found_var].items():
                                        if label in reverse_res_val_labels:
                                            if code != reverse_res_val_labels[label]:
                                                replace_dict[code] = reverse_res_val_labels[label]
                                        # add extra codes
                                        else:
                                            replace_dict[code] = max_res_code
                                            res_meta.var_value_labels[res_var].update(
                                                {max_res_code: label})

                                            max_res_code +=1
                                    e = f"Подлил наиболее похожую {found_var} в {res_var} ответы по метке ответа из файла `{reg_i}.sav`. Проверьте базу."
                                    log_content += '\n' + e
                                    st.warning(e)

                                    # if recodes are, recode them
                                    if replace_dict:
                                        reg_fin_df[found_var] = reg_df[found_var].replace(replace_dict)
                                        FOUND_VARS.add(found_var)
                            else:
                                e = f"База подлита не полностью! Ошибка - для переменной {res_var} '{res_v_label}' из файла `{reg_i}.sav` нет точного совпадения по значениям и меткам"
                                log_content += '\n' + e
                                st.error(e)


                        # FOR MULTIPUNCHES SHOULD BE STRICT VALUE LABELS MATCH - CHECKED HIGHER
                        else:
                            pass
                            #LABELS SHOULD MATCH COMPLETELY


            # PROCESS EXCEED VARS
            exceed_vars = set(reg_df.columns) - FOUND_VARS
            if exceed_vars:
                e = f"В базе есть лишние переменные{", которые не были подлиты" if not sss["merge_new"] else ""}: {', '.join(exceed_vars)}"
                log_content += '\n' + e
                st.warning(e)

                if sss["merge_new"]:
                    for var in exceed_vars:
                        new_var = f"r{reg_i}_{var}"

                        if new_var not in res_meta.var_names:
                            reg_fin_df[new_var]  = reg_df[var]
                            res_meta = copy_from_meta_to_meta(reg_meta, res_meta, var, new_var)

                            settings.loc[new_var] = [
                                True,
                                reg_meta.var_names_to_labels.get(var),
                                False,
                                None,
                                reg_meta.var_value_labels.get(var),
                                False,
                                None
                            ]


            # APPEND TO FIN DF
            if not reg_fin_df.empty:
                res_df = pd.concat([res_df, reg_fin_df], axis=0)
                log_content += '\n' + f"{reg_folder} подлил"
                st.success(f"{reg_folder} подлил")
            else:
                e = f"Внимание: База не подлита! {reg_folder} не набраблось ни одной переменной подходящей под структуру"
                log_content += '\n' + e
                st.error(e)



    dir_to_save = os.path.join(constants.ROOT, constants.QUANT_DIR, constants.FED_FOLDER, project_name)
    if not os.path.exists(dir_to_save):
        os.mkdir(dir_to_save)

    dp.write_spss(
        res_df,
        res_meta,
        dir_to_save,
        project_name
    )
    print("DF IS SAVED")

    if log_content:
        path_to_log = os.path.join(dir_to_save, f"ЛОГ_ОБЪЕДИНЕНИЯ.txt")
        with open(path_to_log, "w") as file:
            file.write(log_content)



def del_from_meta(meta, attrib):
    for param, v in meta.__dict__.items():
        if isinstance(v, list):
            if attrib in v:
                v.remove(attrib)
        elif isinstance(v, (dict, defaultdict)):
            if attrib in v:
                del v[attrib]

    return meta


def copy_from_meta_to_meta(meta_src, meta_trg, var_to_copy, new_name):

    for param, v in meta_src.__dict__.items():
        if isinstance(v, list):
            if (var_to_copy in v) and (not (new_name in getattr(meta_trg, param))): # REDO DIS BULLSHIT
                list_attr = getattr(meta_trg, param)
                list_attr.append(new_name)

        elif isinstance(v, (dict, defaultdict)):
            if var_to_copy in v:
                dict_attr = getattr(meta_trg, param)
                dict_attr[new_name] = v[var_to_copy]

    return meta_trg