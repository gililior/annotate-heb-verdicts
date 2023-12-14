
from app import init, hello_page, main
import streamlit as st
import string

HEB_VERDICTS_DESC = "In the following task you will be presented a verdict from the Israeli court. \n"


def generate_rep_map_to_column():
    heb_verdicts_header = ["username", "filename", "file_length",
                           "ראיות התביעה",
                           "יסוד העבירה",
                           "עדויות התביעה",
                           "עדויות מטעם ההגנה",
                           "סיכום",
                           "עדות הנאשם",
                           "כתב האישום",
                           "הכרעת דין",
                           "סוף דבר"]

    map_to_columns = {}
    for i, header in enumerate(heb_verdicts_header):
        if header in {"username", "filename", "file_length"}:
            continue
        letter = string.ascii_uppercase[i]
        map_to_columns[header] = letter

    return map_to_columns


if __name__ == '__main__':
    init("heb_verdicts", HEB_VERDICTS_DESC)

    if 'column_map' not in st.session_state:
        representative_map_to_column = generate_rep_map_to_column()
        row_ind = 1
        st.session_state.ws.update(values=[["username"]], range_name='A1')
        st.session_state.ws.update(values=[["filename"]], range_name='B1')
        st.session_state.ws.update(values=[["file_length"]], range_name='C1')
        for representative in representative_map_to_column:
            st.session_state.ws.update(values=[[representative]], range_name=f'{representative_map_to_column[representative]}1')
        st.session_state['column_map'] = representative_map_to_column

    if st.session_state.cur_page == 0:
        hello_page()
    else:
        main("heb_verdicts.csv")
