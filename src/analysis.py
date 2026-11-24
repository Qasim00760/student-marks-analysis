"""Analysis functions shared by the notebook and the Streamlit app."""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

REQUIRED_COLUMNS = ["student_id", "subject", "exam", "exam_date", "marks"]
GRADE_ORDER = ["A+", "A", "B", "C", "Fail"]
GRADE_COLORS = {
    "A+": "#1b7837",
    "A": "#7fbf7b",
    "B": "#d9d9d9",
    "C": "#f4a582",
    "Fail": "#b2182b",
}
PASS_MARK = 60


# ---------------------------------------------------------------- loading


def load_marks(source) -> pd.DataFrame:
    """Read a marks CSV (path or uploaded file) and validate its columns."""
    df = pd.read_csv(source)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
            + ". Expected: " + ", ".join(REQUIRED_COLUMNS)
        )

    df = df[REQUIRED_COLUMNS].copy()
    df["marks"] = pd.to_numeric(df["marks"], errors="coerce")
    df["exam_date"] = pd.to_datetime(df["exam_date"], errors="coerce")
    df = df.dropna(subset=["marks", "exam_date"])
    df["marks"] = df["marks"].clip(0, 100)
    return df.reset_index(drop=True)


# ---------------------------------------------------------------- grading


def calculate_grade(marks: float) -> str:
    if marks >= 90:
        return "A+"
    if marks >= 80:
        return "A"
    if marks >= 70:
        return "B"
    if marks >= PASS_MARK:
        return "C"
    return "Fail"


def add_grades(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["grade"] = pd.Categorical(
        out["marks"].apply(calculate_grade), categories=GRADE_ORDER, ordered=True
    )
    return out


# ---------------------------------------------------------------- summaries


def subject_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Average, spread and pass rate per subject, widest spread first."""
    g = df.groupby("subject")["marks"]
    summary = pd.DataFrame(
        {
            "students": g.count(),
            "average": g.mean().round(1),
            "median": g.median(),
            "std_dev": g.std().round(1),
            "lowest": g.min(),
            "highest": g.max(),
            "iqr": (g.quantile(0.75) - g.quantile(0.25)).round(1),
            "pass_rate_%": (g.apply(lambda s: (s >= PASS_MARK).mean() * 100)).round(1),
        }
    )
    summary["range"] = summary["highest"] - summary["lowest"]
    return summary.sort_values("std_dev", ascending=False).reset_index()


def grade_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Share of each grade per subject, in percent."""
    table = pd.crosstab(df["subject"], df["grade"], normalize="index") * 100
    return table.reindex(columns=GRADE_ORDER, fill_value=0).round(1)


def compare_exams(df: pd.DataFrame) -> pd.DataFrame:
    """Marks in the first and last exam for every student and subject."""
    dates = sorted(df["exam_date"].unique())
    if len(dates) < 2:
        raise ValueError("At least two exam dates are needed to compare exams.")
    first, last = dates[0], dates[-1]

    keys = ["student_id", "subject"]
    a = df[df["exam_date"] == first][keys + ["marks"]].rename(columns={"marks": "first_exam"})
    b = df[df["exam_date"] == last][keys + ["marks"]].rename(columns={"marks": "last_exam"})
    out = a.merge(b, on=keys, how="inner")
    out["change"] = out["last_exam"] - out["first_exam"]
    return out


def improvement_by_subject(comparison: pd.DataFrame) -> pd.DataFrame:
    g = comparison.groupby("subject")
    return (
        pd.DataFrame(
            {
                "avg_first_exam": g["first_exam"].mean().round(1),
                "avg_last_exam": g["last_exam"].mean().round(1),
                "avg_change": g["change"].mean().round(1),
                "improved_%": g["change"].apply(lambda s: (s > 0).mean() * 100).round(1),
            }
        )
        .sort_values("avg_change", ascending=False)
        .reset_index()
    )


def student_ranking(df: pd.DataFrame) -> pd.DataFrame:
    """Average marks per student in the latest exam, best first."""
    latest = df[df["exam_date"] == df["exam_date"].max()]
    ranking = (
        latest.groupby("student_id")["marks"]
        .agg(average="mean", subjects_failed=lambda s: int((s < PASS_MARK).sum()))
        .round(1)
        .sort_values("average", ascending=False)
        .reset_index()
    )
    ranking.insert(0, "rank", range(1, len(ranking) + 1))
    return ranking


# ---------------------------------------------------------------- charts


def _subject_order(df: pd.DataFrame) -> list[str]:
    return subject_summary(df)["subject"].tolist()


def plot_marks_distribution(df: pd.DataFrame):
    """Box plot of marks per subject, widest spread on the left."""
    order = _subject_order(df)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.boxplot(
        [df.loc[df["subject"] == s, "marks"] for s in order],
        tick_labels=order,
        patch_artist=True,
        boxprops={"facecolor": "#cfe2f3", "edgecolor": "#3d6d99"},
        medianprops={"color": "#1f3b57", "linewidth": 2},
    )
    ax.axhline(PASS_MARK, color="#b2182b", linestyle="--", linewidth=1, label=f"Pass mark ({PASS_MARK})")
    ax.set_ylabel("Marks")
    ax.set_title("Marks distribution by subject (widest spread on the left)")
    ax.legend(loc="lower right", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def plot_histogram(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(df["marks"], bins=range(0, 105, 5), color="#3d6d99", edgecolor="white")
    ax.axvline(df["marks"].mean(), color="#1f3b57", linewidth=2, label=f"Mean {df['marks'].mean():.1f}")
    ax.axvline(PASS_MARK, color="#b2182b", linestyle="--", linewidth=1, label=f"Pass mark ({PASS_MARK})")
    ax.set_xlabel("Marks")
    ax.set_ylabel("Number of results")
    ax.set_title("Overall marks distribution")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def plot_grade_distribution(df: pd.DataFrame):
    table = grade_distribution(df).reindex(_subject_order(df))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    left = pd.Series(0.0, index=table.index)
    for grade in GRADE_ORDER:
        ax.barh(table.index, table[grade], left=left, color=GRADE_COLORS[grade], label=grade)
        left += table[grade]
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of results (%)")
    ax.set_title("Grade mix by subject")
    ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.15), frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def plot_exam_comparison(improvement: pd.DataFrame):
    data = improvement.set_index("subject")
    x = range(len(data))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar([i - 0.2 for i in x], data["avg_first_exam"], width=0.4, color="#9ecae1", label="First exam")
    ax.bar([i + 0.2 for i in x], data["avg_last_exam"], width=0.4, color="#3d6d99", label="Last exam")
    for i, change in zip(x, data["avg_change"]):
        top = max(data["avg_first_exam"].iloc[i], data["avg_last_exam"].iloc[i])
        ax.text(i, top + 1, f"{change:+.1f}", ha="center", fontsize=9)
    ax.set_xticks(list(x), data.index)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Average marks")
    ax.set_title("Average marks: first exam vs last exam")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig
