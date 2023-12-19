
import numpy as np
import streamlit as st
import pandas as pd
import random
import gspread
import string


INSTRUCTIONS = "For each file, you will be shown a proposed division of the " \
               "documents to subjects according to a suggested table of contents, and " \
               "you are asked to improve this division to what you think fits the most." \
               "  \nTo do so, use the checkbox for each title to include/exclude this " \
               "section from the current document, and use the slider for each title, " \
               "to determine which paragraphs are included under this title." \
               "  \nfew notes:  \n- Not all sections from the table of contents must " \
               "appear in all documents, and you can control it using the checkbox " \
               "next to each title in the table of contents." \
               "  \n- Not all of the document paragraphs must be included as part of the " \
               "section proposed in the table of contents." \
               "  \n- The ranges of paragraphs for each section must not overlap. That " \
               "is, each paragraph can be included as part of only one section (or none)."


def init(ws_name, desc):
    with st.expander("❔ See Instructions"):
        st.write(desc+INSTRUCTIONS)
    if "ws" not in st.session_state:
        gc = gspread.service_account_from_dict(st.secrets["credentials"])
        sh = gc.open("cluster-annotation")
        st.session_state.ws = sh.worksheet(ws_name)
        st.session_state.i = 0
        st.session_state.cur_page = 0


def generate_random_colors(length):
    colors = []
    for _ in range(length):
        red = random.randint(0, 255)
        green = random.randint(0, 255)
        blue = random.randint(0, 255)
        colors.append(f"rgb({red}, {green}, {blue})")
    return colors


def generate_colors_map(df):
    representatives = df.representative.unique()
    colors = generate_random_colors(len(representatives))
    color_map = {}
    for i, rep in enumerate(representatives):
        color_map[rep] = colors[i]
    return color_map


def generate_sidebar_linking(color_map, line_numbers, total):
    for representative in line_numbers:
        key = st.session_state['id_rep_title'][representative]
        st.sidebar.markdown(
            f"<a style='border: 3px solid {color_map[representative]}; padding: 5px; font-size: 16px; color: black;'"
            f" href='#{key}'>{representative}</a>",
            unsafe_allow_html=True)
        add_widgets_for_rep(representative, total)
    for representative in color_map:
        if representative in line_numbers:
            continue
        st.sidebar.markdown(
            f"<a style='border: 3px solid {color_map[representative]}; padding: 5px; font-size: 16px; color: gray;'>{representative}</a>",
            unsafe_allow_html=True)
        add_widgets_for_rep(representative, total)


def add_widgets_for_rep(representative, total):
    st.sidebar.checkbox(label=f"{representative}_checkbox",
                        key=f"{representative}_checkbox",
                        value=st.session_state[f"{representative}_checkbox"],
                        label_visibility='hidden')
    st.sidebar.select_slider(representative, label_visibility='hidden',
                             options=list(np.arange(1, total)),
                             value=st.session_state[f"{representative}_range"],
                             key=f"{representative}_range",
                             disabled=not st.session_state[f"{representative}_checkbox"])


@st.cache_data
def load_csv(file_path):
    return pd.read_csv(file_path)


def generate_rep_map_to_column(df):
    representatives = df.representative.unique()
    rep_to_column = {}
    for i, rep in enumerate(representatives):
        index_letter = i+3
        letter = string.ascii_uppercase[index_letter]
        rep_to_column[rep] = letter
    return rep_to_column


def get_user_files_list(all_files):
    """ checks which files the user haven't seen yet.
    prioritizes files with one annotator, ignore files with more than 2 annotators"""
    rows = st.session_state.ws.get_all_values()
    annotations_df = pd.DataFrame(rows)
    group_by_filename = annotations_df.groupby(1).groups
    one_annotator_file = []
    for filename in group_by_filename:
        if filename == "filename":
            continue
        file_rows = annotations_df.loc[group_by_filename[filename]]
        all_files.remove(filename)
        if st.session_state.username in file_rows[0].values:
            continue
        if len(group_by_filename[filename]) == 1:
            one_annotator_file.append(filename)
    random.shuffle(one_annotator_file)
    random.shuffle(all_files)
    st.session_state.user_files_list = one_annotator_file + all_files


def main(csv_path):
    st.title("Conceptual ToC Annotator")

    if "df" not in st.session_state:
        st.session_state["df"] = load_csv(csv_path)
    df = st.session_state["df"]

    if 'color_map' not in st.session_state:
        color_map = generate_colors_map(df)
        st.session_state['color_map'] = color_map

    color_map = st.session_state['color_map']
    representative_map_to_column = st.session_state['column_map']

    if 'title_index' not in st.session_state:
        st.session_state['title_index'] = 0

    if 'id_rep_title' not in st.session_state:
        st.session_state['id_rep_title'] = dict()

    group_by_filename = df.groupby("filename").groups

    if 'user_files_list' not in st.session_state:
        all_files = [fname for fname in group_by_filename.keys()
                     if len(group_by_filename[fname] > 1)]
        get_user_files_list(all_files)
    user_files = st.session_state['user_files_list']

    st.sidebar.progress(value=st.session_state.i / len(user_files))
    st.sidebar.markdown("<h3 style='font-size: 24px;'>ToC (color mapping)</h3>",
                        unsafe_allow_html=True)

    if st.button('submit'):
        # validate
        valid = validate_ranges(representative_map_to_column)
        if valid:
            st.session_state.i += 1
            next_row_ind = len(st.session_state.ws.col_values(1)) + 1
            st.session_state.ws.update(values=[[st.session_state.username]], range_name='A' + str(next_row_ind))
            st.session_state.ws.update(values=[[user_files[st.session_state.i - 1]]], range_name='B' + str(next_row_ind))
            st.session_state.ws.update(values=[[st.session_state.len_file]], range_name='C' + str(next_row_ind))
            for representative in representative_map_to_column:
                if st.session_state[f"{representative}_checkbox"]:
                    letter = representative_map_to_column[representative]
                    st.session_state.ws.update(values=[[str(st.session_state[f"{representative}_range"])]], range_name=letter + str(next_row_ind))
                st.session_state.pop(f"{representative}_range")
                st.session_state.pop(f"{representative}_checkbox")
    selected_file = user_files[st.session_state.i]
    import streamlit as st

    court = "mechozi" if selected_file.startswith("m") else "shalom"
    link_prefix = "https://www.nevo.co.il/psika_word/" + court + "/"
    link_to_doc = link_prefix + selected_file.replace(".csv", ".doc")
    st.write(f"file name:{selected_file.replace('.csv', '')}")
    st.write(f"[link]({link_to_doc}) to document in nevo")

    # Filter dataframe based on selected file
    filtered_df = df.loc[group_by_filename[selected_file]]
    filtered_df = filtered_df.sort_values(by=['title_index']).reset_index()
    st.session_state.len_file = len(filtered_df)

    if not filtered_df.empty:
        display_single_file(color_map, filtered_df)
    else:
        st.write("Selected file not found in the CSV.")


def validate_ranges(representative_map_to_column):
    indices_covered = np.full((st.session_state.len_file,), fill_value=False)
    for representative in representative_map_to_column:
        if st.session_state[f"{representative}_checkbox"]:
            range_rep = st.session_state[f"{representative}_range"]
            if np.any(indices_covered[range_rep[0]-1:range_rep[1]]):
                st.error(f"ranges are incorrect for {representative}")
                return False
            indices_covered[range_rep[0]-1:range_rep[1]] = True
    return True


def display_single_file(color_map, filtered_df):

    st.header("Text Content:")

    all_paragraphs, labels_start_end = get_paragraphs(filtered_df)

    line_numbers = {}
    is_open = (False, None)
    for i, paragraph in enumerate(all_paragraphs):
        prev_label, current_label = labels_start_end[i]
        if prev_label is not None:
            line_numbers[prev_label] = (line_numbers[prev_label], i)
            color = color_map[prev_label]
            st.markdown(f"""<hr style="height:10px;border:none;color:{color};background-color:{color};" /> """, unsafe_allow_html=True)
            is_open = (False, None)
        if current_label is not None:
            st.header(current_label, anchor=str(st.session_state['title_index']))
            st.session_state['id_rep_title'].update({current_label: st.session_state['title_index']})
            st.session_state['title_index'] += 1
            color = color_map[current_label]
            st.markdown(f"""<hr style="height:10px;border:none;color:{color};background-color:{color};" /> """,unsafe_allow_html=True)
            is_open = (True, current_label)
            line_numbers[current_label] = i+1

        # convert the paragraph to html replacing the \n with <br>
        paragraph = paragraph.replace("\n", "<br>")

        html_text = f"""<table><tr><th> {i+1} </th><th> {paragraph} </th></tr></table>"""
        st.markdown(html_text, unsafe_allow_html=True)

    if is_open[0]:
        label = is_open[1]
        color = color_map[label]
        st.markdown(
            f"""<hr style="text-align: input {{unicode-bidi:bidi-override; direction: RTL;}} direction: RTL;height:10px;border:none;color:{color};background-color:{color};" /> """,
            unsafe_allow_html=True)
        line_numbers[label] = (line_numbers[label], len(all_paragraphs))

    init_checkbox_and_slider_values(color_map, line_numbers)

    generate_sidebar_linking(color_map, line_numbers, len(all_paragraphs)+1)


def init_checkbox_and_slider_values(color_map, line_numbers):
    for rep in color_map:
        if f"{rep}_checkbox" in st.session_state:
            continue

        if rep in line_numbers:
            st.session_state[f"{rep}_checkbox"] = True
            st.session_state[f"{rep}_range"] = line_numbers[rep]
        else:
            st.session_state[f"{rep}_checkbox"] = False
            st.session_state[f"{rep}_range"] = (1, 1)


def get_id_rep(representative):
    return representative.lower().replace('.', '').replace(' ', '-')


def get_paragraphs(filtered_df):
    all_paragraphs = []
    all_labels = []
    labels_start_end = []
    for i, row in filtered_df.iterrows():
        paragraph = f"{row['title_text']}\n\n{row['section_text']}\n\n"
        if i + 1 < len(filtered_df):
            if row['section_text'] == filtered_df.loc[i + 1]['title_text']:
                paragraph += f"{filtered_df.loc[i + 1]['section_text']}\n\n"
        label = row["representative"] if row["community"] != -1 else None
        prev = current = None
        if i == 0 and label is not None:
            current = label
        if i > 0 and all_labels[-1] != label:
            if i > 0 and all_labels[-1] is not None:
                prev = all_labels[-1]
            if label is not None:
                current = label
        labels_start_end.append((prev, current))
        all_paragraphs.append(paragraph)
        all_labels.append(label)

    return all_paragraphs, labels_start_end


def hello_page():
    st.header('Conceptual ToC Annotator')
    st.markdown('Hello! Please enter your username')
    st.text_input('Username', key='username_box')

    st.button('Next', key='next_button0', on_click=record_name)


def record_name():
    if len(st.session_state.username_box) == 0:
        st.error('You must enter a valid username')
    else:
        st.session_state.username = st.session_state.username_box
        next_page()


def next_page():
    st.session_state.cur_page += 1

