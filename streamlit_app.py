import streamlit as st
import fitz  # PyMuPDF
import re
import tempfile

def extract_classes(pdf_text):
    # Pattern to extract entries like MFS-A(6)- AB {C - 402}
    pattern = re.compile(r"([A-Z]+(?:-[A-Z])?-[A-Z]\([0-9]+\)-\s*[A-Z]{1,4})\s*\{([^}]+)\}")
    matches = pattern.findall(pdf_text)
    result = []
    for entry, venue in matches:
        course_info = entry.replace('\n', ' ').strip()
        result.append((course_info, venue))
    return result

def filter_by_user_input(classes, selected_sections):
    filtered = []
    for entry, venue in classes:
        for section in selected_sections:
            if section in entry:
                filtered.append((entry, venue))
    return filtered

def main():
    st.set_page_config(page_title="IMT Personalized Timetable", layout="wide")
    st.title("📅 Personalized Timetable Generator")
    st.markdown("Upload your academic schedule PDF and select your courses + sections.")

    with st.sidebar:
        st.header("Step 1: Select Your Courses/Sections")
        example_sections = ["MFS-A", "ET-B", "BRM-Exc", "SCMO-A", "DIGM-A"]
        selected_sections = st.multiselect("Select course-section combinations:", example_sections)

    uploaded_file = st.file_uploader("Step 2: Upload Academic Timetable PDF", type="pdf")

    if uploaded_file and selected_sections:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        doc = fitz.open(tmp_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()

        all_classes = extract_classes(full_text)
        personalized = filter_by_user_input(all_classes, selected_sections)

        if personalized:
            st.subheader("📌 Your Personalized Schedule")
            for entry, venue in personalized:
                st.markdown(f"- **{entry}** @ _{venue}_")
        else:
            st.warning("No matching classes found for selected sections.")

    elif uploaded_file:
        st.info("Please select at least one course-section to filter your schedule.")

if __name__ == '__main__':
    main()
