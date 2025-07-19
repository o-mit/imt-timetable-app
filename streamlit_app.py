import streamlit as st
import pandas as pd
import pdfplumber
import re
from io import BytesIO

# --- Function to load course and section data from CSV ---
@st.cache_data
def load_course_data(file_path="Course_and_Sections.csv"):
    """
    Loads course data from the specified CSV file into a pandas DataFrame.
    Caches the data to avoid reloading on every interaction.
    """
    try:
        df = pd.read_csv(file_path)
        # Standardize column names
        df.columns = [col.strip().replace(' ', '_').replace('.', '') for col in df.columns]
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure it's in the same directory as the script.")
        return None

# --- Function to parse the uploaded PDF timetable ---
def parse_timetable_pdf(uploaded_file):
    """
    Parses the uploaded PDF file to extract class schedule information.
    """
    all_classes = []
    # Regex to extract details from a class information string
    # Pattern: Course-Section(Session)-Faculty {Venue} or (Venue)
    class_pattern = re.compile(r"([A-Z\d\w-]+)-([A-Z])\((\d+)\)-\s*([A-Z\s/]+?)\s*[\(\{](.+?)[\)\}]")

    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            # Get time slots from the header row
            time_slots = table[0]

            # Process rows starting from the second row (index 1)
            for row in table[1:]:
                day_info = row[0]
                if day_info and day_info.strip():
                    current_day = day_info.replace('\n', ' ')

                # Iterate through class cells for the current row
                for i, cell in enumerate(row[1:], start=1):
                    if cell and cell.strip():
                        # Handle multiple classes in one cell
                        entries = cell.strip().split('\n\n')
                        for entry in entries:
                            match = class_pattern.match(entry.replace('\n', ' '))
                            if match:
                                course_abbr, section, session, faculty, venue = match.groups()
                                time_slot = time_slots[i].replace('\n', '') if i < len(time_slots) else "N/A"
                                
                                all_classes.append({
                                    "Day": current_day,
                                    "Time": time_slot,
                                    "Course_Abbreviation": course_abbr.strip(),
                                    "Section": section.strip(),
                                    "Faculty": faculty.strip(),
                                    "Venue": venue.strip()
                                })
    return all_classes


# --- Main Application Logic ---
def main():
    st.set_page_config(page_title="IMT Timetable Generator", layout="wide")
    st.title(" Personalized Weekly Timetable Generator")
    st.write("Select your courses and sections, then upload the general weekly schedule PDF to get your personalized timetable.")

    # Load course data
    course_df = load_course_data()
    if course_df is None:
        return

    # Create a mapping from abbreviation to full course name
    abbr_to_name = pd.Series(course_df.Course_Name.values, index=course_df.Abbriviation).to_dict()

    # --- User Selection ---
    st.sidebar.header("Your Course Selections")
    
    # Generate a list of all possible "Course - Section" pairs for the selection widget
    course_section_options = []
    for _, row in course_df.iterrows():
        sections = str(row.Sections).split(',')
        for sec in sections:
            option = f"{row.Abbriviation} - {sec.strip()}"
            course_section_options.append(option)
            
    user_selections = st.sidebar.multiselect(
        "Select all your registered courses and their sections:",
        options=sorted(list(set(course_section_options)))
    )

    # --- PDF Upload ---
    st.sidebar.header("Upload Schedule")
    uploaded_pdf = st.sidebar.file_uploader("Upload the general timetable PDF", type="pdf")

    if st.sidebar.button("Generate My Timetable"):
        if not user_selections:
            st.warning("Please select your courses and sections first.")
        elif not uploaded_pdf:
            st.warning("Please upload the general timetable PDF.")
        else:
            # --- Processing and Display ---
            with st.spinner("Parsing the PDF and generating your schedule..."):
                # Parse the PDF
                all_classes = parse_timetable_pdf(uploaded_pdf)
                
                if not all_classes:
                    st.error("Could not extract any class information from the PDF. Please check the PDF format.")
                    return

                # Filter for the user's classes
                my_classes = []
                for cls in all_classes:
                    class_id = f"{cls['Course_Abbreviation']} - {cls['Section']}"
                    if class_id in user_selections:
                        # Add full course name for display
                        cls['Course_Name'] = abbr_to_name.get(cls['Course_Abbreviation'], "Unknown Course")
                        my_classes.append(cls)

                # Display the personalized schedule
                if not my_classes:
                    st.info("No classes found for your selected courses and sections in the provided schedule.")
                else:
                    st.success("Your personalized timetable is ready!")
                    
                    # For sorting days of the week correctly
                    day_order = [
                        'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'
                    ]
                    
                    # Clean up day info and sort
                    df = pd.DataFrame(my_classes)
                    df['Day_Short'] = df['Day'].apply(lambda x: x.split()[0][:3] if x else 'N/A')
                    df['Day_Short'] = pd.Categorical(df['Day_Short'], categories=day_order, ordered=True)
                    df = df.sort_values('Day_Short')

                    # Display day by day
                    for day_name in df['Day_Short'].unique():
                        st.subheader(f"🗓️ {df[df['Day_Short'] == day_name]['Day'].iloc[0]}")
                        day_df = df[df['Day_Short'] == day_name]
                        
                        for _, row in day_df.iterrows():
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.write(f"**🕒 Time:** {row['Time']}")
                            with col2:
                                st.write(f"**📚 Course:** {row['Course_Name']} ({row['Course_Abbreviation']}-{row['Section']})")
                            with col3:
                                st.write(f"**👨‍🏫 Faculty:** {row['Faculty']}")
                                st.write(f"**📍 Venue:** {row['Venue']}")
                        st.markdown("---")

if __name__ == "__main__":
    main()
