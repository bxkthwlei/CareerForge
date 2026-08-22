# CareerForge

CareerForge is an AI-assisted career recommendation and skill-gap planning
application built with Python and Streamlit. It ranks career matches, analyses
missing skills, generates learning paths and roadmaps, tracks progress, and
supports account-based profiles.

## Main features

- Career recommendation with cosine similarity and weighted scoring
- Skill-gap and readiness analysis
- Prerequisite-aware learning paths
- Constraint-based monthly roadmaps
- What-if simulation and career comparison
- User registration, login, saved profiles, and progress tracking
- SQLite for local development and PostgreSQL for cloud deployment

## Run locally

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest -q
streamlit run streamlit_app.py
```

For the free GitHub + Streamlit Community Cloud + Neon deployment steps, read
[DEPLOYMENT.md](DEPLOYMENT.md).
