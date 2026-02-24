"""
templates.py — Generate downloadable Excel template files
"""

import io
import pandas as pd


def generate_key_template():
    """Generate a sample Answer Key template as xlsx bytes."""
    data = {
        "Number": [1, 2, 3, 4, 5],
        "Question": [
            "On the second day, dry land was created.",
            "What was the source of the waters in the Flood?",
            "Which of the following is NOT correct regarding Sodom?",
            "What was Kayin's profession?",
            "Who began the journey from Ur Kasdim?",
        ],
        "Answer": [
            "F",
            "D",
            "A",
            "Farmer / tiller of the ground",
            "Terach",
        ],
        "Points": [3, 6, 4, 6, 6],
        "Comment": [
            "",
            "D. Rain and underground waters",
            "",
            "Alt: Ackerbauer, земледелец, עובד אדמה",
            "Alt: Terach (with Avram, Sarai, Lot)",
        ],
    }
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()
