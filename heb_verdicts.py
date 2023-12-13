
from app import init, hello_page, main
import streamlit as st
import string

HEB_VERDICTS_DESC = "In the following task you will be presented a verdict from the Israeli court. \n"


def generate_rep_map_to_column():
    heb_verdicts_header = ["username", "filename", "file_length", "פרשת ראיות התביעה",
                           "הדיון", "התנהגותה של המתלוננת במהלך האירוע",
                           "העבירה של מעשה מגונה היסוד הנפשי", "סיכום", "גרסת הנאשם",
                           "כתב האישום", "הכרעת דין", "גדר המחלוקת",
                           "ה עדותה של או כ אם הקטין", "סוף דבר", "אישום שני"]

    map_to_columns = {}
    for i, header in enumerate(heb_verdicts_header):
        if header in {"username", "filename", "file_length"}:
            continue
        letter = string.ascii_uppercase[i]
        map_to_columns[header] = letter
    print(map_to_columns)

    return map_to_columns


if __name__ == '__main__':
    init("heb_verdicts", HEB_VERDICTS_DESC)

    if 'column_map' not in st.session_state:
        representative_map_to_column = generate_rep_map_to_column()
        print(representative_map_to_column)
        row_ind = 1
        st.session_state.ws.update('A1', "username")
        st.session_state.ws.update('B1', "filename")
        st.session_state.ws.update('C1', "file_length")
        for representative in representative_map_to_column:
            st.session_state.ws.update(f'{representative_map_to_column[representative]}1', representative)
        st.session_state['column_map'] = representative_map_to_column

    if st.session_state.cur_page == 0:
        hello_page()
    else:
        main("heb_verdicts.csv")
