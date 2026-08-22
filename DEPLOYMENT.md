# CareerForge free deployment

CareerForge is ready for a free deployment using GitHub, Streamlit Community
Cloud, and a Neon PostgreSQL database.

## 1. Test locally

Create and activate a virtual environment, then install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pytest -q
streamlit run streamlit_app.py
```

Without `DATABASE_URL`, the app uses the local
`database/careerforge.db` SQLite file.

## 2. Upload to GitHub

Upload the project files to the `CareerForge` repository. Do not upload:

- `venv/`
- `.pytest_cache/` or `__pycache__/`
- any `.db` file
- `.streamlit/secrets.toml`
- any file containing the Neon connection string

The included `.gitignore` protects these paths when Git is used.

## 3. Deploy on Streamlit Community Cloud

1. Open <https://share.streamlit.io> and sign in with GitHub.
2. Select **Create app** and choose the `CareerForge` repository.
3. Choose the `main` branch.
4. Set the entrypoint to `streamlit_app.py`.
5. Open **Advanced settings** and use a supported Python version such as 3.12.
6. In **Secrets**, add the real Neon connection string:

```toml
DATABASE_URL = "postgresql://USER:PASSWORD@HOST/neondb?sslmode=require"
```

7. Click **Deploy**.

The application creates the `users`, `profiles`, and `progress` tables in Neon
when it starts. User accounts and progress then remain available across app
restarts.

## 4. Verify the deployment

1. Register a new test account.
2. Log in and change one skill level.
3. Complete a learning-path skill.
4. Log out and log in again.
5. Confirm that the profile and progress are still present.

If deployment fails, open **Manage app > Logs** and check the first error. Never
paste the full database URL into a public issue, screenshot, or repository.
