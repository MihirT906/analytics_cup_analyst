# SkillCorner X PySport Analytics Cup
This repository contains the submission template for the SkillCorner X PySport Analytics Cup **Analyst Track**. 
Your submission for the **Analyst Track** should be on the `main` branch of your own fork of this repository.

Find the Analytics Cup [**dataset**](https://github.com/SkillCorner/opendata/tree/master/data) and [**tutorials**](https://github.com/SkillCorner/opendata/tree/master/resources) on the [**SkillCorner Open Data Repository**](https://github.com/SkillCorner/opendata).

## Submitting
Make sure your `main` branch contains:

1. A single Jupyter Notebook in the root of this repository called `submission.ipynb`
    - This Juypter Notebook can not contain more than 2000 words.
    - All other code should also be contained in this repository, but should be imported into the notebook from the `src` folder.


or,


1. A single Python file in the root of this repository called `main.py`
    - This file should not contain more than 2000 words.
    - All other code should also be contained in this repository, but should be imported into the notebook from the `src` folder.

or, 


1. A publicly accessible web app or website written in a language of your choice (e.g. Javascript)

    - Your code should follow a clear and well defined structure.
    - All other code should also be contained in this repository.
    - The URL to the webapp should be included at the bottom of the read me under **URL to Web App / Website**


2. An abstract of maximum 300 words that follows the **Analyst Track Abstract Template**.
3. Add a URL to a screen recording video of maximum 60 seconds that shows your work. Add it under the **Video URL** Section below. (Use YouTube, or any other site to share this video).
4. Submit your GitHub repository on the [Analytics Cup Pretalx page](https://pretalx.pysport.org)

Finally:
- Make sure your GitHub repository does **not** contain big data files. The tracking data should be loaded directly from the [Analytics Cup Data GitHub Repository](https://github.com/SkillCorner/opendata). For more information on how to load the data directly from GitHub please see this [Jupyter Notebook](https://github.com/SkillCorner/opendata/blob/master/resources/getting-started-skc-tracking-kloppy.ipynb).
- Make sure the `submission.ipynb` notebook runs on a clean environment, or
- Provide clear and concise instructions how to run the `main.py` (e.g. `streamlit run main.py`) if applicable in the **Run Instructions** Section below.
- Providing a URL to a publically accessible webapp or website with a running version of your submission is mandatory when choosing to submit in a different language then Python, it is encouraged, but optional when submitting in Python.

_⚠️ Not adhering to these submission rules and the [**Analytics Cup Rules**](https://pysport.org/analytics-cup/rules) may result in a point deduction or disqualification._

---

## Analyst Track Abstract Template (max. 300 words)
#### Introduction

While match footage captures what happens on the field, it does not preserve the insights, reasoning, and experience of the coach. This project addresses that gap by allowing coaches to create focused episodes from a match and layer their analysis, annotations, and tactical reasoning onto them. It allows you to transform raw footage into an interpretable, accessible record that conveys insight to players.

#### Usecase(s)
Team Strategy Analysis and Post-Match Review: Coaches no longer need to sift through full match videos or spend time on complex editing to convey their insights. They can create replayable, highlighted episodes that clearly showcase key plays, player positioning, mistakes, and recurring patterns, making post-game discussions more effective and understandable for players.

#### Potential Audience
Coaches, sports analysts, and sports analytics content creators
---

## Video URL

---

## Run Instructions
1. **Clone the repository**:
```bash
git clone https://github.com/MihirT906/analytics_cup_analyst.git
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Run the application**:
Follow along the file:
```bash
analytics_cup_analyst/submission.ipynb
```
---

## [Optional] URL to Web App / Website