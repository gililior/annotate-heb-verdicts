import sys

import numpy as np
import streamlit as st
import pandas as pd
import random
import string


if "i" not in st.session_state:
    st.session_state.i = 0


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


def generate_sidebar_linking(color_map, line_numbers):
    for representative in color_map:
        id_rep = get_id_rep(representative)
        if representative in line_numbers:
            key = st.session_state['id_rep_title'][representative]
            # st.sidebar.markdown(
            #     f"<a style='border: 3px solid {color_map[representative]}; padding: 5px; font-size: 16px; color: black;'"
            #     f" href='#{id_rep}'>{representative}</a>",
            #     unsafe_allow_html=True)
            st.sidebar.markdown(
                f"<a style='border: 3px solid {color_map[representative]}; padding: 5px; font-size: 16px; color: black;'"
                f" href='#{key}'>{representative}</a>",
                unsafe_allow_html=True)

            # st.sidebar.markdown(
            #     f"<a style='border: 3px solid {color_map[representative]}; padding: 5px; font-size: 16px; text-align: input {{unicode-bidi:bidi-override; direction: RTL;}} direction: RTL; "
            #     f"color: black;' href='#{id_rep}'>{representative}</a>",
            #     unsafe_allow_html=True)
        else:
            st.sidebar.markdown(
                f"<a style='border: 3px solid {color_map[representative]}; padding: 5px; font-size: 16px; color: gray;'>{representative}</a>",
                unsafe_allow_html=True)
            # st.sidebar.markdown(
            #     f"<a style='border: 3px solid {color_map[representative]}; padding: 5px; font-size: 16px; text-align: input {{unicode-bidi:bidi-override; direction: RTL;}} direction: RTL;"
            #     f"color: gray;'>{representative}</a>",
            #     unsafe_allow_html=True)


@st.cache_data
def load_csv(file_path):
    return pd.read_csv(file_path)



def main():
    # Page title and description
    st.title("Conceptual ToC Viewer")
    st.write("Select a CSV file generated in the clustering pipeline to see how the "
             "conceptual ToC is applied in each doc.")

    # File selection
    # use a basic folder path for (this parent directory)
    csv_file = st.file_uploader("Upload a CSV file", type="csv")

    if csv_file is not None:

        # Load CSV data
        df = load_csv(csv_file)

        if 'csv_file' not in st.session_state:
            st.session_state['csv_file'] = csv_file
        else:
            if st.session_state['csv_file'] != csv_file:
                st.session_state['csv_file'] = csv_file
                # delete the color map and file index from the session state
                del st.session_state['color_map']
                del st.session_state['file_index']
                del st.session_state['title_index']
                del st.session_state['id_rep_title']

        # Set a variable once after a new CSV file is loaded
        if 'color_map' not in st.session_state:
            color_map = generate_colors_map(df)
            st.session_state['color_map'] = color_map
        color_map = st.session_state['color_map']

        if 'file_index' not in st.session_state:
            st.session_state['file_index'] = 0

        if 'title_index' not in st.session_state:
            st.session_state['title_index'] = 0

        if 'id_rep_title' not in st.session_state:
            st.session_state['id_rep_title'] = dict()


        # color_map = st.session_state['color_map']

        st.sidebar.markdown("<h3 style='font-size: 24px;'>ToC (color mapping)</h3>",
                            unsafe_allow_html=True)

        group_by_filename = df.groupby("filename").groups
        # add a checkbox to show Specific title:
        specific_title = st.checkbox("Show Specific Title", value=False)

        if not specific_title:
            # Display file selection dropdown
            # selected_file = st.selectbox("Select a file", group_by_filename.keys())
            selected_file = select_file(list(group_by_filename.keys()))

            # Filter dataframe based on selected file
            filtered_df = df.loc[group_by_filename[selected_file]]
            filtered_df = filtered_df.sort_values(by=['title_index']).reset_index()


        else:
            selected_title = st.selectbox("Select title", color_map.keys())


            # Filter dataframe based on selected file
            filtered_df = df[df.representative== selected_title]
            filtered_df = filtered_df.sort_values(by=['title_index']).reset_index()

            group_by_filename = filtered_df.groupby("filename").groups
            # add markdown of the numbers of the files with this title
            st.markdown(f"<p style='font-size: 18px; font-weight: bold; color: green;'>"
                        f"number of files: {len(group_by_filename)}</p>",
                        unsafe_allow_html=True)

            selected_file = select_file(list(group_by_filename.keys()))

            filtered_df = filtered_df.loc[group_by_filename[selected_file]]
            filtered_df = filtered_df.sort_values(by=['title_index']).reset_index()


        if not filtered_df.empty:
            display_single_file(color_map, filtered_df)
        else:
            st.write("Selected file not found in the CSV.")




def select_file(files):
    def prev_file():
        if st.session_state['file_index'] > 0:
            st.session_state['file_index'] -= 1

    def next_file():
        if st.session_state['file_index'] < len(files) - 1:
            st.session_state['file_index'] += 1

    def go_to_file():
        # split the number of the sentence from the string of st.session_state["sentence_for_tagging"]
        # and then convert it to int
        st.session_state["file_index"] = files.index(st.session_state["file_for_tagging"])

    st.selectbox(
        "Select file:",
        files,
        index=st.session_state["file_index"],
        on_change=go_to_file,
        key="file_for_tagging",
    )

    file = files[st.session_state['file_index']]
    col1, col2 = st.columns(2)
    with col1:
        st.button('prev', on_click=prev_file)
    with col2:
        st.button('next', on_click=next_file)
    st.markdown(f"Selected file: {file}", unsafe_allow_html=True)
    return file

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
            # st.markdown(f"""<hr style="text-align: input {{unicode-bidi:bidi-override; direction: RTL;}} direction: RTL; height:10px;border:none;color:{color};background-color:{color};" /> """, unsafe_allow_html=True)
            is_open = (False, None)
        if current_label is not None:
            id_rep = get_id_rep(current_label)
            st.header(current_label, anchor=str(st.session_state['title_index']))
            st.session_state['id_rep_title'].update({current_label: st.session_state['title_index']})
            st.session_state['title_index'] += 1
            # st.header(f"<h3 id='{id_rep}'>{current_label}</h3>", unsafe_allow_html=True)  # todo add id for the hyperlink, write this as a header
            # st.markdown(f"<h3 id='{id_rep}'>{current_label}</h3>", unsafe_allow_html=True)  # todo add id for the hyperlink, write this as a header
            color = color_map[current_label]
            st.markdown(f"""<hr style="height:10px;border:none;color:{color};background-color:{color};" /> """,unsafe_allow_html=True)
            # st.markdown(f"""<hr style="text-align: input {{unicode-bidi:bidi-override; direction: RTL;}} direction: RTL;height:10px;border:none;color:{color};background-color:{color};" /> """,
            #             unsafe_allow_html=True)
            is_open = (True, current_label)
            line_numbers[current_label] = i+1

        # convert the paragraph to html replacing the \n with <br>
        paragraph = paragraph.replace("\n", "<br>")

        st.markdown(
            f"<p style='text-align: input {{unicode-bidi:bidi-override; direction: RTL;}} direction: RTL;"
            f" '>{paragraph}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='direction: RTL; text-align: right; >{paragraph}</p>", unsafe_allow_html=True)

    if is_open[0]:
        label = is_open[1]
        color = color_map[label]
        st.markdown(
            f"""<hr style="text-align: input {{unicode-bidi:bidi-override; direction: RTL;}} direction: RTL;height:10px;border:none;color:{color};background-color:{color};" /> """,
            unsafe_allow_html=True)
        line_numbers[label] = (line_numbers[label], len(all_paragraphs))

    generate_sidebar_linking(color_map, line_numbers)


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
        label = row["representative"]
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


if __name__ == '__main__':
    main()