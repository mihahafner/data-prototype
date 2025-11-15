
data_prototype/
├── data/
│   └── processed/weather_lju_anomalies.csv
├── tools/
│   └── s3_publish.py
├── requirements.txt
├── README.md                ← week summary
└── README_s3_publish.md     ← tool-specific readme




# ✅ **WEEK 1 — PROJECT FOUNDATION & REPRODUCIBLE DATA INGESTION PIPELINE**

This document summarizes everything implemented in **Week 1** of the *data-prototype* project.
It describes the **architecture**, **components**, **data flow**, **processes**, and how the entire workflow is **fully reproducible** both:

* **locally (PyCharm)**
* **in the cloud (Google Colab)**

This README serves as a **design plan**, a **technical reference**, and a **runbook** for anyone joining the project.

---

# 🚀 **1. PROJECT GOALS FOR WEEK 1**

Week 1 establishes the complete infrastructure required for a growing data project:

### ✔ Fully working local Python environment

### ✔ Fully working cloud execution (Google Colab)

### ✔ Reproducible folder structure

### ✔ Automated data ingestion from Open-Meteo API

### ✔ Clean Git history + `.gitignore`

### ✔ Data stored locally but *never* committed to Git

### ✔ Notebook working in *both* environments (local + Colab)

### ✔ First dataset exported to `data/raw/weather_lju.csv`

These steps create a robust foundation for Week 2 (processing + features).

---

# 📂 **2. PROJECT STRUCTURE (REPRODUCIBLE ACROSS SYSTEMS)**

Only source code, configs, and notebooks are stored in Git.
Data is generated automatically.

```
data-prototype/
│
├── data/                     ← Local only (gitignored)
│   ├── raw/
│   │   └── .gitkeep          ← Keeps folder structure in Git
│   └── processed/            ← Future weeks
│
├── notebooks/
│   └── 01_api_to_csv.ipynb   ← Week 1 notebook (runs local + Colab)
│
├── verify_environment.py     ← Ensures correct Python environment
├── requirements.txt          ← Reproducible dependencies
├── README.md                 ← This document
└── .gitignore                ← Prevents data & temp files from entering Git
```

### ✔ Clean

### ✔ Standard ML/DS layout

### ✔ Data folders exist **without** containing data

### ✔ Git contains only what matters (code, configs, notebooks)

---

# 🌐 **3. ENVIRONMENTS**

Week 1 ensures the project runs identically in two execution environments:

---

## 🖥️ **Local: PyCharm (Windows)**

* Python 3.14 venv created inside the project
* Dependencies installed from `requirements.txt`
* Notebook executed through PyCharm Jupyter integration
* CSV stored locally in:
  `data/raw/weather_lju.csv`

---

## ☁️ **Cloud: Google Colab**

Colab is used for team collaboration and remote execution.

When executed in Colab:

1. The notebook detects it is running in Colab.
2. It clones the repository automatically:

```
/content/data-prototype/
```

3. It sets the working directory to the repo root.
4. It runs the same code and writes data to:

```
/content/data-prototype/data/raw/weather_lju.csv
```

### ✔ Same folder structure

### ✔ Same code

### ✔ Same results

### ✔ No manual setup required

---

# 🔧 **4. UNIVERSAL PATH MANAGEMENT**

*(the core of Week 1 engineering work)*

To support both environments, the notebook uses a **universal project root resolver**:

### ✔ Works locally

### ✔ Works in Colab

### ✔ Automatically clones the repo in Colab

### ✔ Always finds the repo root

### ✔ Always ensures `data/raw/` exists

```python
from pathlib import Path
import os, sys, subprocess

REPO_URL = "https://github.com/mihahafner/data-prototype.git"
REPO_DIRNAME = "data-prototype"

def get_repo_root() -> Path:
    in_colab = "google.colab" in sys.modules

    if in_colab:
        root = Path("/content") / REPO_DIRNAME
        if not root.exists():
            subprocess.run(
                ["git", "clone", "--depth", "1", REPO_URL, str(root)],
                check=True
            )
        os.chdir(root)
        return root

    here = Path.cwd()
    for p in (here, *here.parents):
        if (p / ".git").is_dir():
            return p

    for p in (here, *here.parents):
        if (p / "data").is_dir():
            return p

    return here

REPO_ROOT = get_repo_root()
RAW = REPO_ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
```

---

# 🌦️ **5. DATA INGESTION PIPELINE (OPEN-METEO API)**

The notebook performs the following:

## 1️⃣ Fetch hourly temperature + humidity for Ljubljana

via Open-Meteo free API.

```python
import requests
response = requests.get("https://api.open-meteo.com/...")
json_data = response.json()
```

## 2️⃣ Convert to DataFrame

```python
import pandas as pd
df = pd.DataFrame({
    "time": json_data["hourly"]["time"],
    "temp_c": json_data["hourly"]["temperature_2m"],
    "rh": json_data["hourly"]["relative_humidity_2m"],
})
```

## 3️⃣ Save CSV locally (atomic write)

```python
tmp = RAW / "weather_lju.csv.tmp"
out = RAW / "weather_lju.csv"

df.to_csv(tmp, index=False, encoding="utf-8")
tmp.replace(out)   # atomic replacement
```

## 4️⃣ Verify it

### Local:

```
data/raw/weather_lju.csv
```

### Colab:

```
/content/data-prototype/data/raw/weather_lju.csv
```

---

# 🚫 **6. GIT STRATEGY — DATA SHOULD NEVER GO INTO GIT**

`.gitignore` contains:

```
data/
!data/raw/.gitkeep
```

Meaning:

* All data files are ignored ❌
* Folder structure stays in Git ✔
* No CSV uploaded
* No large data history
* Clean project

This is critical for scaling into Weeks 2–8.

---

# 🔁 **7. REPRODUCIBILITY**

Anyone can clone the repo and reproduce Week 1:

### 👉 Local:

```bash
git clone https://github.com/mihahafner/data-prototype.git
cd data-prototype
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pycharm .
```

Run:
`notebooks/01_api_to_csv.ipynb`
Click *Run All* → CSV generated.

---

### 👉 Colab:

Open:

```
https://colab.research.google.com/github/mihahafner/data-prototype/blob/main/notebooks/01_api_to_csv.ipynb
```

Click:

**"Run Anyway" → Run All**

Everything is reproduced automatically:

* Repo cloned ✔
* Paths resolved ✔
* Data fetched ✔
* CSV saved ✔

---

# 🧱 **8. WEEK 1 ARCHITECTURE OVERVIEW**

```
┌──────────────────────────┐
│   GitHub Repository      │
│ (code, notebooks, config)│
└───────────────┬──────────┘
                │
                │ cloned (Colab) / pulled (local)
                ▼
  ┌────────────────────────┐
  │ Execution Environment  │─────────────┐
  │   • Local (PyCharm)    │             │
  │   • Colab (Cloud)      │             │
  └───────────┬────────────┘             │
              │                          │
   resolve repo root path                │
              ▼                          │
    ┌────────────────────┐               │
    │  data/ directory   │   ← ignored by Git
    └─────────┬──────────┘               │
              │                          │
              ▼                          │
     ┌────────────────────┐              │
     │ Open-Meteo API     │──────────────┘
     └────────────────────┘
```

---

# 🎯 **9. WEEK 1: DELIVERABLES COMPLETED**

### ✔ Local + Colab unified execution

### ✔ Automatic repo cloning in Colab

### ✔ API ingestion

### ✔ Clean & structured data folder

### ✔ Correct .gitignore

### ✔ First data export

### ✔ Professional folder architecture

### ✔ No data committed to Git

### ✔ README and requirements ready

Your project now has a **solid engineering foundation**.

---

# 🧭 **10. NEXT STEPS (WEEK 2 PREVIEW)**

Week 2 will focus on:

* reading raw CSV
* cleaning & preprocessing
* handling missing values
* making processed datasets
* writing data to `data/processed/`
* building reusable Python modules
* versioning processed datasets
* adding unit tests

---

If you'd like, I can generate:

### 🔹 A diagram

### 🔹 A PDF version of Week 1 summary

### 🔹 A project roadmap for all 8 weeks

### 🔹 A “Next Steps” notebook for Week 2

Just tell me.
