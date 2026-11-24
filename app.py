"""Streamlit app for exploring student marks.

Run locally:
    streamlit run app.py
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.analysis import (
    REQUIRED_COLUMNS,
    add_grades,
    compare_exams,
    improvement_by_subject,
    load_marks,
    plot_exam_comparison,
    plot_grade_distribution,
    plot_histogram,
    plot_marks_distribution,
    student_ranking,
    subject_summary,
)

SAMPLE_DATA = Path(__file__).parent / "data" / "student_marks.csv"

st.set_page_config(page_title="Student Marks Analysis", layout="wide")
st.title("Student Marks Analysis")
st.write(
    "Find which subjects have the widest spread of marks, how grades are distributed, "
    "and how results changed between the first and last exam."
)

# ---------------------------------------------------------------- data source
with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload a CSV", type="csv")
    st.caption("Required columns: " + ", ".join(REQUIRED_COLUMNS))
    with open(SAMPLE_DATA, "rb") as f:
        st.download_button("Download sample CSV", f, file_name="student_marks.csv")

try:
    raw = load_marks(uploaded if uploaded is not None else SAMPLE_DATA)
except ValueError as err:
    st.error(str(err))
    st.stop()

if uploaded is None:
    st.info("Showing the sample dataset. Upload your own CSV from the sidebar to analyze it.")

df = add_grades(raw)

with st.sidebar:
    st.header("Filters")
    subjects = sorted(df["subject"].unique())
    chosen_subjects = st.multiselect("Subjects", subjects, default=subjects)
    exams = sorted(df["exam"].unique())
    chosen_exams = st.multiselect("Exams", exams, default=exams)

view = df[df["subject"].isin(chosen_subjects) & df["exam"].isin(chosen_exams)]
if view.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ---------------------------------------------------------------- headline numbers
summary = subject_summary(view)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Students", view["student_id"].nunique())
c2.metric("Average marks", f"{view['marks'].mean():.1f}")
c3.metric("Pass rate", f"{(view['marks'] >= 60).mean() * 100:.1f}%")
c4.metric("Widest spread", summary.iloc[0]["subject"], f"std dev {summary.iloc[0]['std_dev']}", delta_color="off")

# ---------------------------------------------------------------- tabs
tab_spread, tab_grades, tab_exams, tab_students, tab_data = st.tabs(
    ["Spread by subject", "Grades", "Exam comparison", "Student ranking", "Data"]
)

with tab_spread:
    st.pyplot(plot_marks_distribution(view))
    st.dataframe(summary, hide_index=True, width="stretch")
    st.pyplot(plot_histogram(view))

with tab_grades:
    st.caption("A+ 90 and above, A 80 to 89, B 70 to 79, C 60 to 69, Fail below 60")
    st.pyplot(plot_grade_distribution(view))

with tab_exams:
    try:
        comparison = compare_exams(df[df["subject"].isin(chosen_subjects)])
        improvement = improvement_by_subject(comparison)
        st.pyplot(plot_exam_comparison(improvement))
        st.dataframe(improvement, hide_index=True, width="stretch")
    except ValueError as err:
        st.info(str(err))
        comparison = None

with tab_students:
    ranking = student_ranking(view)
    st.dataframe(ranking, hide_index=True, width="stretch")

with tab_data:
    st.dataframe(view, hide_index=True, width="stretch")
    st.download_button(
        "Download subject summary",
        summary.to_csv(index=False),
        file_name="subject_summary.csv",
    )
    if comparison is not None:
        st.download_button(
            "Download exam comparison",
            comparison.to_csv(index=False),
            file_name="exam_comparison.csv",
        )
