"""Generate the sample student marks dataset used by the notebook and the app.

The data is synthetic. It is generated with a fixed random seed so the results
in the notebook and README can be reproduced exactly.

Usage:
    python scripts/generate_data.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
N_STUDENTS = 60
EXAMS = {"Midterm": "2024-01-10", "Final": "2024-03-15"}

# Each subject has its own average and spread so the analysis has
# real differences to find (for example, Math is the most spread out).
SUBJECTS = {
    "Math": {"mean": 68, "std": 16},
    "English": {"mean": 74, "std": 9},
    "Science": {"mean": 71, "std": 12},
    "Computer Science": {"mean": 76, "std": 11},
    "Urdu": {"mean": 79, "std": 7},
}

OUTPUT = Path(__file__).resolve().parents[1] / "data" / "student_marks.csv"


def generate(seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    students = [f"S{i:03d}" for i in range(1, N_STUDENTS + 1)]
    ability = rng.normal(0, 6, N_STUDENTS)  # general strength of each student

    rows = []
    for s_idx, student in enumerate(students):
        for subject, params in SUBJECTS.items():
            midterm = rng.normal(params["mean"], params["std"]) + ability[s_idx]
            # Most students improve a little between the midterm and the final.
            final = midterm + rng.normal(3, 6)
            for exam, score in zip(EXAMS, (midterm, final)):
                rows.append(
                    {
                        "student_id": student,
                        "subject": subject,
                        "exam": exam,
                        "exam_date": EXAMS[exam],
                        "marks": int(np.clip(round(score), 0, 100)),
                    }
                )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(df)} rows to {OUTPUT}")
