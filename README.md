# SkillCorner X PySport Analytics Cup

#### Introduction

Match footage shows what happened. SkillsCorner turns that into information. But who better than the coach to transform information into wisdom? This project lets coaches select key moments, create highlights, and add their analysis, tactics, and reasoning so players can truly learn from the game.

#### Usecase(s)
Team Strategy Analysis and Post-Match Review: Coaches no longer have to spend hours sifting through video or editing clips. They can create replayable episodes that showcase important plays, positioning, mistakes, and patterns. By adding their perspective, coaches turn raw information into actionable wisdom that can change how the team learns and plays.

#### Potential Audience
Coaches, sports analysts, and sports analytics content creators

---

## Video URL
Watch the demo below to find out how to use this repository to the fullest: 
https://drive.google.com/file/d/1WzB8xe8xU54aGb5QSh4qrVPqyp7rDMzN/view?usp=sharing

---

## Run Instructions
1. **Clone the repository**:
```bash
git clone https://github.com/MihirT906/analytics_cup_analyst.git
cd analytics_cup_analyst
```

2. **Install dependencies**:
The below command creates an environment [analytics_cup_analyst] with all required dependencies:
```bash
conda env create -f environment.yml
conda activate analytics_cup_analyst
```

3. **Create Jupyter Kernel**:
Create a kernel to run juptyter notebooks using the above environemnt
```bash
python -m ipykernel install --user \
  --name analytics_cup_analyst \
  --display-name "Python (analytics_cup_analyst)"
```
3. **Run the application**:
Launch:
```bash
jupyter notebook
```
and run submission.ipynb
Follow along the notebook and run all cells

**Optional Step 3 (Local Editor / Script Run)**
If using VS Code, PyCharm, or another editor:
* Point the interpreter to the analytics_cup_analyst environment
* Run the notebook submission.ipynb

If facing issues with kernel:
Run 
```bash
python submission.py
```

---

For further information, documentation is available at:
docs/episode_studio_documentation.pdf