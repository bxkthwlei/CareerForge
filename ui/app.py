"""Streamlit dashboard for CareerForge with a public landing page."""

import base64
import copy
import html
import json
import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from database.db import (  # noqa: E402
    get_progress_history,
    initialize_database,
    load_profile,
    record_skill_progress,
    save_profile,
)
from services.auth import login_user, register_user  # noqa: E402
from services.comparison import compare_careers  # noqa: E402
from services.learning_path import generate_learning_path  # noqa: E402
from services.progress import update_skill_progress  # noqa: E402
from services.readiness import calculate_readiness  # noqa: E402
from services.recommendation import recommend_careers  # noqa: E402
from services.roadmap import generate_roadmap  # noqa: E402
from services.skill_gap import analyze_skill_gap  # noqa: E402
from services.what_if import simulate_skill_change  # noqa: E402


DATABASE_PATH = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("CAREERFORGE_DB_PATH")
    or str(PROJECT_ROOT / "database" / "careerforge.db")
)
CAREERS_PATH = PROJECT_ROOT / "data" / "careers.json"
SKILLS_PATH = PROJECT_ROOT / "data" / "skills.json"
HERO_IMAGE_PATH = PROJECT_ROOT / "assets" / "hero-career-path.webp"
BACKGROUND_PATH = PROJECT_ROOT / "assets" / "backgrounds"
CAREER_COUNT = 30

AUTH_BACKGROUND_PATHS = {
    "login": BACKGROUND_PATH / "login.webp",
    "register": BACKGROUND_PATH / "register.webp",
}

PAGE_BACKGROUND_PATHS = {
    "dashboard": BACKGROUND_PATH / "dashboard.webp",
    "overview": BACKGROUND_PATH / "overview.webp",
    "skill_gap": BACKGROUND_PATH / "skill-gap.webp",
    "learning": BACKGROUND_PATH / "learning-roadmap.webp",
    "what_if": BACKGROUND_PATH / "what-if.webp",
    "compare": BACKGROUND_PATH / "comparison.webp",
    "progress": BACKGROUND_PATH / "progress.webp",
}

FEATURE_PAGES = {
    "overview": {
        "title": "Overview",
        "icon": "📊",
        "description": (
            "View ranked career recommendations and match scores."
        ),
    },
    "skill_gap": {
        "title": "Skill Gap",
        "icon": "🎯",
        "description": (
            "Identify missing skills and career readiness."
        ),
    },
    "learning": {
        "title": "Learning & Roadmap",
        "icon": "🗺️",
        "description": (
            "Follow an AI learning path and monthly roadmap."
        ),
    },
    "what_if": {
        "title": "What-If Simulator",
        "icon": "🔄",
        "description": (
            "Simulate how improving a skill changes career results."
        ),
    },
    "compare": {
        "title": "Career Comparison",
        "icon": "⚖️",
        "description": (
            "Compare two career paths across important metrics."
        ),
    },
    "progress": {
        "title": "Progress Tracking",
        "icon": "📈",
        "description": (
            "Review completed skills and continue learning."
        ),
    },
}


DEFAULT_PROFILE = {
    "skills": {
        "python": 6,
        "linux": 7,
        "networking": 8,
        "cybersecurity": 7,
        "siem": 3,
        "incident_response": 2,
        "routing_switching": 6,
        "network_security": 6,
        "cloud": 3,
        "aws": 2,
        "docker": 3,
        "sql": 4,
        "statistics": 3,
        "data_visualization": 2,
        "excel": 5,
        "web_development": 3,
        "apis": 2,
        "databases": 4,
    },
    "interests": [
        "cybersecurity",
        "networking",
        "problem_solving",
    ],
    "completed_projects": 1,
    "available_months": 4,
    "weekly_hours": 8,
}


def load_json(path):
    """Load a UTF-8 JSON file."""

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def readable_name(identifier):
    """Convert an internal identifier into a label."""

    return identifier.replace("_", " ").title()


def image_data_uri(path):
    """Return a local image as an embeddable data URI."""

    image_bytes = path.read_bytes()
    encoded = base64.b64encode(image_bytes).decode("ascii")
    media_type = "image/webp" if path.suffix == ".webp" else "image/png"
    return f"data:{media_type};base64,{encoded}"


def apply_page_background(image_path, *, authentication=False):
    """Apply a readable image background to one non-landing page."""

    background_image = image_data_uri(image_path)
    overlay = "0.78" if authentication else "0.86"
    form_style = """
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.82);
            backdrop-filter: blur(14px);
        }
    """ if authentication else ""

    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image:
                linear-gradient(
                    rgba(248, 250, 252, {overlay}),
                    rgba(238, 242, 255, {overlay})
                ),
                url('{background_image}');
            background-position: center;
            background-repeat: no-repeat;
            background-size: cover;
            background-attachment: fixed;
        }}

        [data-testid="stHeader"] {{
            background: rgba(248, 250, 252, 0.70);
            backdrop-filter: blur(12px);
        }}

        {form_style}
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_custom_styles():
    """Apply the CareerForge visual theme."""

    st.markdown(
        """
        <style>
        .block-container {
            max-width: 1280px;
            padding-top: 3.25rem;
            padding-bottom: 4rem;
        }

        [data-testid="stAppViewContainer"] {
            background-image:
                radial-gradient(
                    circle at 92% 4%,
                    rgba(56, 189, 248, 0.08),
                    transparent 24rem
                ),
                radial-gradient(
                    circle at 12% 88%,
                    rgba(14, 165, 233, 0.055),
                    transparent 26rem
                );
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(56, 189, 248, 0.18);
            background: linear-gradient(
                180deg,
                rgba(56, 189, 248, 0.08) 0%,
                rgba(14, 165, 233, 0.04) 100%
            );
        }

        [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
            padding-top: 1.4rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.025em;
        }

        [data-testid="stMetric"] {
            min-height: 126px;
            padding: 1.15rem 1.25rem;
            border: 1px solid rgba(56, 189, 248, 0.20);
            border-radius: 16px;
            background: linear-gradient(
                145deg,
                rgba(56, 189, 248, 0.10),
                rgba(14, 165, 233, 0.05)
            );
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.07);
        }

        [data-testid="stMetricLabel"] {
            font-weight: 650;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid rgba(56, 189, 248, 0.20) !important;
            border-radius: 18px !important;
            background: linear-gradient(
                145deg,
                rgba(56, 189, 248, 0.08),
                rgba(14, 165, 233, 0.035)
            );
            box-shadow: 0 12px 32px rgba(15, 23, 42, 0.07);
            transition: transform 160ms ease, box-shadow 160ms ease;
        }

        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 16px 38px rgba(15, 23, 42, 0.11);
        }

        [data-testid="stForm"] {
            padding: 1.35rem;
            border-radius: 16px;
            border-color: rgba(56, 189, 248, 0.22);
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
        }

        .stButton > button,
        [data-testid="stFormSubmitButton"] > button {
            min-height: 2.7rem;
            border-radius: 10px;
            border-color: rgba(56, 189, 248, 0.38);
            font-weight: 650;
            transition: transform 150ms ease, box-shadow 150ms ease;
        }

        .stButton > button:hover,
        [data-testid="stFormSubmitButton"] > button:hover {
            transform: translateY(-1px);
            border-color: rgb(56, 189, 248);
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.20);
        }

        .stButton > button[kind="primary"] {
            color: white;
            border: 0;
            background: linear-gradient(120deg, #2563eb, #38bdf8);
            box-shadow: 0 9px 22px rgba(37, 99, 235, 0.28);
        }

        .stButton > button[kind="primary"]:hover {
            color: white;
            border: 0;
            background: linear-gradient(120deg, #1d4ed8, #0369a1);
            box-shadow: 0 12px 26px rgba(37, 99, 235, 0.32);
        }

        [data-testid="stDataFrame"] {
            border: 1px solid rgba(56, 189, 248, 0.16);
            border-radius: 14px;
            overflow: hidden;
        }

        .cf-hero {
            padding: 1.65rem 1.8rem;
            margin-bottom: 1.5rem;
            color: white;
            border-radius: 20px;
            background: linear-gradient(125deg, #1e40af, #2563eb 55%, #0891b2);
            box-shadow: 0 18px 42px rgba(37, 99, 235, 0.24);
        }

        .cf-hero h1 {
            margin: 0 0 0.35rem 0;
            color: white;
            font-size: 2rem;
        }

        .cf-hero p {
            margin: 0;
            color: rgba(255, 255, 255, 0.88);
            font-size: 1.02rem;
        }

        .cf-page-eyebrow {
            margin-bottom: 0.5rem;
            color: rgba(255, 255, 255, 0.78);
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .cf-feature-hero {
            position: relative;
            overflow: hidden;
            padding: 1.65rem 1.8rem;
            margin: 1.05rem 0 1.8rem 0;
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 20px;
            background: linear-gradient(125deg, #0b1f4d, #1d4ed8 52%, #0369a1);
            box-shadow: 0 18px 42px rgba(6, 78, 59, 0.20);
        }

        .cf-feature-hero::after {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            right: -55px;
            top: -105px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.10);
        }

        .cf-feature-title {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin-bottom: 0.45rem;
        }

        .cf-feature-icon {
            display: grid;
            place-items: center;
            width: 3.2rem;
            height: 3.2rem;
            flex: 0 0 3.2rem;
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.13);
            font-size: 1.65rem;
            backdrop-filter: blur(8px);
        }

        .cf-feature-hero h1 {
            position: relative;
            z-index: 1;
            margin: 0;
            color: white;
            font-size: clamp(1.8rem, 3vw, 2.45rem);
        }

        .cf-feature-hero p {
            position: relative;
            z-index: 1;
            max-width: 760px;
            margin: 0;
            color: rgba(255, 255, 255, 0.86);
            font-size: 1rem;
        }

        .cf-back-label {
            margin-bottom: 0.35rem;
            color: #5f756c;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .cf-sidebar-user {
            padding: 0.85rem 1rem;
            margin: 0.4rem 0 1rem 0;
            border: 1px solid rgba(56, 189, 248, 0.20);
            border-radius: 13px;
            background: rgba(56, 189, 248, 0.08);
        }

        .cf-sidebar-user small {
            display: block;
            opacity: 0.72;
            margin-bottom: 0.15rem;
        }

        .cf-sidebar-user strong {
            font-size: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_workspace_styles():
    """Apply the restrained SaaS theme outside the landing page."""

    st.markdown(
        """
        <style>
        :root { --cf-ink:#e6f4ff; --cf-muted:#8fafc8; --cf-line:#1b365d; --cf-blue:#38bdf8; }
        [data-testid="stAppViewContainer"] { background:#050b18; }
        [data-testid="stHeader"] { background:rgba(5,11,24,.90); backdrop-filter:blur(12px); }
        .block-container { width:100%; max-width:1480px; padding:2.2rem clamp(1rem,2.6vw,2.75rem) 4rem; }
        [data-testid="stSidebar"] { background:#071226; border-right:1px solid var(--cf-line); }
        [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top:1.2rem; }
        h1,h2,h3 { color:var(--cf-ink); letter-spacing:-.035em; }
        p,[data-testid="stCaptionContainer"] { color:var(--cf-muted); }
        [data-testid="stMetric"] { min-height:116px; padding:1.15rem 1.2rem; background:rgba(11,23,48,.88); border:1px solid var(--cf-line); border-radius:12px; box-shadow:0 10px 28px rgba(0,0,0,.20); backdrop-filter:blur(14px); }
        [data-testid="stVerticalBlockBorderWrapper"] { background:rgba(11,23,48,.82)!important; border:1px solid var(--cf-line)!important; border-radius:14px!important; box-shadow:0 10px 28px rgba(0,0,0,.18); backdrop-filter:blur(14px); transition:border-color 160ms ease,box-shadow 160ms ease; }
        [data-testid="stVerticalBlockBorderWrapper"]:hover { transform:none; border-color:#38bdf8!important; box-shadow:0 12px 30px rgba(56,189,248,.14); }
        [data-testid="stForm"] { padding:1.5rem; background:rgba(11,23,48,.86); border:1px solid var(--cf-line); border-radius:14px; box-shadow:0 12px 30px rgba(0,0,0,.16); backdrop-filter:blur(14px); }
        .stButton>button,[data-testid="stFormSubmitButton"]>button { min-height:2.75rem; border:1px solid #244b75; border-radius:8px; background:#0e2140; color:#e6f4ff; font-weight:650; box-shadow:none; }
        .stButton>button:hover,[data-testid="stFormSubmitButton"]>button:hover { transform:none; border-color:#7dd3fc; color:#7dd3fc; box-shadow:0 4px 14px rgba(56,189,248,.18); }
        .stButton>button[kind="primary"],[data-testid="stFormSubmitButton"]>button[kind="primary"] { border:1px solid var(--cf-blue); background:var(--cf-blue); color:#030b1a; box-shadow:none; }
        [data-testid="stDataFrame"] { overflow:hidden; background:#0b1730; border:1px solid var(--cf-line); border-radius:12px; }
        .cf-auth-brand { margin-bottom:2.2rem; }
        .cf-auth-brand strong { display:block; color:var(--cf-ink); font-size:1.22rem; letter-spacing:-.03em; }
        .cf-auth-brand span { color:var(--cf-muted); font-size:.88rem; }
        .cf-auth-heading { margin:0 0 .4rem; font-size:clamp(2rem,3vw,2.7rem); }
        .cf-auth-copy { max-width:34rem; margin:0 0 1.5rem; color:var(--cf-muted); }
        .cf-auth-art { min-height:690px; display:flex; flex-direction:column; justify-content:flex-end; padding:clamp(1.5rem,4vw,3.2rem); border-radius:18px; color:#fff; background-position:center; background-size:cover; box-shadow:0 20px 55px rgba(15,23,42,.18); }
        .cf-auth-art h2 { max-width:30rem; margin:0 0 .7rem; color:#fff; font-size:clamp(1.8rem,3vw,2.8rem); }
        .cf-auth-art p { max-width:32rem; margin:0; color:rgba(255,255,255,.78); font-size:1rem; }
        .cf-dashboard-hero,.cf-feature-hero { position:relative; min-height:250px; display:flex; flex-direction:column; justify-content:flex-end; overflow:hidden; padding:clamp(1.6rem,3vw,2.5rem); margin:0 0 2rem; border:1px solid rgba(255,255,255,.14); border-radius:16px; color:#fff; background-position:center; background-size:cover; box-shadow:0 12px 34px rgba(15,23,42,.14); }
        .cf-dashboard-hero::before,.cf-feature-hero::before { content:""; position:absolute; inset:0; background:linear-gradient(90deg,rgba(5,12,28,.94),rgba(5,12,28,.72) 48%,rgba(5,12,28,.18)); }
        .cf-dashboard-hero>*,.cf-feature-hero>* { position:relative; z-index:1; max-width:680px; }
        .cf-dashboard-hero h1,.cf-feature-hero h1 { margin:0 0 .55rem; color:#fff; font-size:clamp(2rem,3.5vw,3.1rem); }
        .cf-dashboard-hero p,.cf-feature-hero p { margin:0; color:rgba(255,255,255,.78); font-size:1.02rem; }
        .cf-page-eyebrow { margin-bottom:.6rem; color:#7dd3fc; font-size:.75rem; font-weight:750; letter-spacing:.13em; text-transform:uppercase; }
        .cf-feature-title { display:block; margin:0; }
        .cf-feature-icon,.cf-back-label { display:none; }
        .cf-section-heading { margin:.2rem 0 1.3rem; }
        .cf-section-heading h2 { margin:0 0 .25rem; font-size:1.55rem; }
        .cf-section-heading p { margin:0; }
        .cf-card-index { display:inline-flex; align-items:center; justify-content:center; width:2rem; height:2rem; margin-bottom:.55rem; border-radius:8px; background:#10264d; color:#7dd3fc; font-size:.75rem; font-weight:800; }
        .cf-sidebar-user { margin:.6rem 0 1rem; padding:.9rem 1rem; border:1px solid var(--cf-line); border-radius:10px; background:#0b1730; }
        @media(max-width:800px) { .block-container{padding-top:1.2rem}.cf-auth-art{min-height:360px}.cf-dashboard-hero,.cf-feature-hero{min-height:220px} }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_landing_styles():
    """Apply styles used only by the public landing page."""

    st.markdown(
        """
        <style>
        .block-container {
            width: 100%;
            max-width: none;
            padding: 1.25rem clamp(1rem, 3.5vw, 4.5rem) 4rem;
        }

        .cf-site-nav {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 0 0 1.15rem;
            padding: 0.8rem 0;
        }

        .cf-brand {
            display: flex;
            align-items: center;
            gap: 0.7rem;
            color: #e6f4ff;
            font-size: 1.18rem;
            font-weight: 800;
            letter-spacing: -0.025em;
        }

        .cf-brand-mark {
            display: grid;
            place-items: center;
            width: 2.35rem;
            height: 2.35rem;
            color: white;
            border-radius: 12px;
            background: linear-gradient(135deg, #2563eb, #22d3ee);
            box-shadow: 0 9px 22px rgba(37, 99, 235, 0.28);
        }

        .cf-nav-note {
            color: #8fafc8;
            font-size: 0.88rem;
            font-weight: 600;
        }

        .cf-landing-hero {
            position: relative;
            display: flex;
            align-items: center;
            width: 100%;
            min-height: min(680px, 72vh);
            overflow: hidden;
            padding: clamp(2.4rem, 6vw, 6.5rem);
            color: white;
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 28px;
            background-position: center;
            background-size: cover;
            box-shadow: 0 30px 80px rgba(15, 23, 42, 0.24);
        }

        .cf-landing-hero::after {
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: linear-gradient(
                90deg,
                rgba(2, 6, 23, 0.12),
                transparent 58%
            );
        }

        .cf-landing-copy {
            position: relative;
            z-index: 1;
            width: min(720px, 54%);
        }

        .cf-kicker {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.48rem 0.75rem;
            margin-bottom: 1.2rem;
            color: #93c5fd;
            border: 1px solid rgba(125, 211, 252, 0.28);
            border-radius: 999px;
            background: rgba(30, 64, 175, 0.22);
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            backdrop-filter: blur(12px);
        }

        .cf-kicker-dot {
            width: 0.48rem;
            height: 0.48rem;
            border-radius: 50%;
            background: #38bdf8;
            box-shadow: 0 0 16px #38bdf8;
        }

        .cf-landing-hero h1 {
            max-width: 680px;
            margin: 0 0 1.25rem;
            color: white;
            font-size: clamp(2.65rem, 5.5vw, 5rem);
            line-height: 0.98;
            letter-spacing: -0.055em;
        }

        .cf-gradient-word {
            color: #7dd3fc;
            background: linear-gradient(90deg, #60a5fa, #22d3ee);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .cf-landing-hero p {
            max-width: 580px;
            margin: 0;
            color: rgba(226, 232, 240, 0.88);
            font-size: clamp(1rem, 1.6vw, 1.18rem);
            line-height: 1.75;
        }

        .cf-hero-proof {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem 1.2rem;
            margin-top: 1.6rem;
            color: rgba(226, 232, 240, 0.82);
            font-size: 0.88rem;
            font-weight: 650;
        }

        .cf-hero-proof span::before {
            content: "✓";
            margin-right: 0.38rem;
            color: #67e8f9;
        }

        .cf-cta-row {
            padding: 1.05rem 0 0.65rem;
        }

        .cf-section {
            width: 100%;
            padding: clamp(4rem, 7vw, 7rem) 0 0;
        }

        .cf-section-heading {
            max-width: 720px;
            margin: 0 auto 2.3rem;
            text-align: center;
        }

        .cf-section-heading small {
            color: #38bdf8;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .cf-section-heading h2 {
            margin: 0.65rem 0 0.8rem;
            color: #e6f4ff;
            font-size: clamp(2rem, 4vw, 3.1rem);
            line-height: 1.08;
        }

        .cf-section-heading p {
            margin: 0;
            color: #8fafc8;
            font-size: 1.03rem;
            line-height: 1.7;
        }

        .cf-feature-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
        }

        .cf-web-card {
            min-height: 220px;
            padding: clamp(1.35rem, 2.3vw, 2rem);
            border: 1px solid #1b365d;
            border-radius: 20px;
            background: rgba(11, 23, 48, 0.78);
            box-shadow: 0 12px 38px rgba(0, 0, 0, 0.16);
            transition: transform 180ms ease, box-shadow 180ms ease,
                border-color 180ms ease;
            backdrop-filter: blur(12px);
        }

        .cf-web-card:hover {
            transform: translateY(-5px);
            border-color: #38bdf8;
            box-shadow: 0 20px 48px rgba(56, 189, 248, 0.14);
        }

        .cf-card-icon {
            display: grid;
            place-items: center;
            width: 3rem;
            height: 3rem;
            margin-bottom: 1.15rem;
            border-radius: 14px;
            background: linear-gradient(145deg, #10264d, #0b2f57);
            font-size: 1.35rem;
        }

        .cf-web-card h3 {
            margin: 0 0 0.55rem;
            color: #e6f4ff;
            font-size: 1.08rem;
        }

        .cf-web-card p {
            margin: 0;
            color: #8fafc8;
            line-height: 1.65;
        }

        .cf-steps {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1.1rem;
        }

        .cf-step {
            position: relative;
            min-height: 230px;
            padding: clamp(1.5rem, 2.5vw, 2.2rem);
            overflow: hidden;
            border-radius: 22px;
            background: #0b1730;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
        }

        .cf-step-number {
            display: inline-grid;
            place-items: center;
            width: 2.3rem;
            height: 2.3rem;
            margin-bottom: 1.4rem;
            color: #030b1a;
            border-radius: 50%;
            background: #38bdf8;
            font-weight: 850;
        }

        .cf-step h3 {
            margin: 0 0 0.55rem;
            color: white;
        }

        .cf-step p {
            margin: 0;
            color: #8fafc8;
            line-height: 1.65;
        }

        @media (max-width: 900px) {
            .cf-feature-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .cf-landing-copy { width: 70%; }
            .cf-landing-hero {
                min-height: 570px;
                background-position: 58% center;
            }
        }

        @media (max-width: 640px) {
            .block-container { padding: 1rem 1rem 3rem; }

            .cf-site-nav {
                align-items: flex-start;
                margin-top: 0;
            }

            .cf-nav-note { display: none; }

            .cf-landing-hero {
                min-height: 620px;
                padding: 2rem 1.35rem;
                border-radius: 22px;
                background-position: 64% center;
            }

            .cf-landing-hero::before {
                content: "";
                position: absolute;
                inset: 0;
                background: rgba(2, 6, 23, 0.48);
            }

            .cf-landing-copy { width: 100%; }
            .cf-landing-hero h1 { font-size: clamp(2.55rem, 14vw, 4rem); }
            .cf-feature-grid, .cf-steps { grid-template-columns: 1fr; }
            .cf-web-card { min-height: auto; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def initialize_app_state():
    """Initialize the database and base Streamlit session."""

    initialize_database(DATABASE_PATH)

    defaults = {
        "authenticated": False,
        "current_user": None,
        "public_page": "landing",
        "auth_page": "login",
        "current_page": "dashboard",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def initialize_user_state(username):
    """Load the profile belonging to the authenticated user."""

    if st.session_state.get("profile_owner") == username:
        return

    stored_profile = load_profile(username, DATABASE_PATH)

    if stored_profile is None:
        stored_profile = copy.deepcopy(DEFAULT_PROFILE)
        save_profile(
            username,
            stored_profile,
            DATABASE_PATH,
        )

    st.session_state.user_profile = stored_profile
    st.session_state.selected_skills = list(
        stored_profile.get("skills", {}).keys()
    )
    st.session_state.profile_owner = username
    st.session_state.current_page = "dashboard"
    st.session_state.pop("what_if_result", None)


def clear_user_state():
    """Clear authenticated and profile-specific session data."""

    removable_keys = {
        "user_profile",
        "selected_skills",
        "profile_owner",
        "what_if_result",
        "auth_notice",
        "login_username",
        "login_password",
        "register_username",
        "register_email",
        "register_password",
        "register_confirm_password",
    }

    for key in list(st.session_state):
        if (
            key in removable_keys
            or key.startswith("profile_skill_")
        ):
            del st.session_state[key]

    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.public_page = "landing"
    st.session_state.auth_page = "login"
    st.session_state.current_page = "dashboard"


def open_auth_page(page_name):
    """Open the login or account-registration page."""

    st.session_state.public_page = "auth"
    st.session_state.auth_page = page_name
    st.rerun()


def render_landing_page():
    """Render the public CareerForge marketing landing page."""

    hero_image = image_data_uri(HERO_IMAGE_PATH)

    st.markdown(
        """
        <div class="cf-site-nav">
            <div class="cf-brand">
                <span class="cf-brand-mark">CF</span>
                <span>CareerForge</span>
            </div>
            <div class="cf-nav-note">
                AI-powered career planning, built around your skills
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <section
            class="cf-landing-hero"
            style="background-image:
                linear-gradient(
                    90deg,
                    rgba(2, 6, 23, 0.98) 0%,
                    rgba(2, 6, 23, 0.88) 34%,
                    rgba(2, 6, 23, 0.24) 64%,
                    rgba(2, 6, 23, 0.08) 100%
                ),
                url('{hero_image}');"
        >
            <div class="cf-landing-copy">
                <div class="cf-kicker">
                    <span class="cf-kicker-dot"></span>
                    Your personalized career intelligence
                </div>
                <h1>
                    Turn your skills into a
                    <span class="cf-gradient-word">clear career path.</span>
                </h1>
                <p>
                    Discover careers that fit you, understand the skills
                    you are missing, and follow a practical roadmap built
                    around your goals and available time.
                </p>
                <div class="cf-hero-proof">
                    <span>Personalized matches</span>
                    <span>Actionable skill gaps</span>
                    <span>Progress that stays saved</span>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="cf-cta-row"></div>',
        unsafe_allow_html=True,
    )
    primary, secondary, spacer = st.columns([1.2, 1, 3.8])

    with primary:
        if st.button(
            "Start My Career Plan",
            type="primary",
            use_container_width=True,
        ):
            open_auth_page("register")

    with secondary:
        if st.button(
            "Sign In",
            use_container_width=True,
        ):
            open_auth_page("login")

    st.markdown(
        """
        <section class="cf-section">
            <div class="cf-section-heading">
                <small>One workspace, six focused tools</small>
                <h2>Everything you need to move from uncertainty to action.</h2>
                <p>
                    CareerForge combines explainable matching, planning,
                    simulation, and progress tracking in one practical workspace.
                </p>
            </div>
            <div class="cf-feature-grid">
                <article class="cf-web-card">
                    <div class="cf-card-icon">◎</div>
                    <h3>Career Overview</h3>
                    <p>See ranked career matches with transparent scores for skills and interests.</p>
                </article>
                <article class="cf-web-card">
                    <div class="cf-card-icon">◈</div>
                    <h3>Skill-Gap Analysis</h3>
                    <p>Know exactly which skills need attention and how far you are from each target.</p>
                </article>
                <article class="cf-web-card">
                    <div class="cf-card-icon">↗</div>
                    <h3>Learning Roadmap</h3>
                    <p>Turn skill gaps into an ordered learning path that fits your weekly schedule.</p>
                </article>
                <article class="cf-web-card">
                    <div class="cf-card-icon">◇</div>
                    <h3>What-If Simulator</h3>
                    <p>Preview how improving one skill can change your scores and career rankings.</p>
                </article>
                <article class="cf-web-card">
                    <div class="cf-card-icon">⇄</div>
                    <h3>Career Comparison</h3>
                    <p>Compare two paths side by side using the metrics that matter most.</p>
                </article>
                <article class="cf-web-card">
                    <div class="cf-card-icon">✓</div>
                    <h3>Progress Tracking</h3>
                    <p>Save completed steps, update your profile, and continue from any device.</p>
                </article>
            </div>
        </section>

        <section class="cf-section">
            <div class="cf-section-heading">
                <small>How it works</small>
                <h2>A smarter career plan in three simple steps.</h2>
            </div>
            <div class="cf-steps">
                <article class="cf-step">
                    <span class="cf-step-number">1</span>
                    <h3>Build your profile</h3>
                    <p>Add your current skills, interests, project experience, and study time.</p>
                </article>
                <article class="cf-step">
                    <span class="cf-step-number">2</span>
                    <h3>Explore your fit</h3>
                    <p>Review explainable career matches, readiness, and priority skill gaps.</p>
                </article>
                <article class="cf-step">
                    <span class="cf-step-number">3</span>
                    <h3>Follow your roadmap</h3>
                    <p>Complete learning steps and watch your career readiness improve over time.</p>
                </article>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_login_page():
    """Render and process the login form."""

    st.title("CareerForge")
    st.caption("AI Career and Skill-Gap Planner")
    st.subheader("Login")
    st.markdown(
        """
        <p class="cf-auth-copy">
            Welcome back. Sign in to continue your career plan,
            review your progress, and explore your next best move.
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        identifier = st.text_input(
            "Username or email",
            key="login_username",
        )
        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )
        submitted = st.form_submit_button(
            "Login",
            use_container_width=True,
        )

    if submitted:
        result = login_user(
            identifier,
            password,
            DATABASE_PATH,
        )

        if result["success"]:
            st.session_state.authenticated = True
            st.session_state.current_user = result["user"][
                "username"
            ]
            initialize_user_state(
                st.session_state.current_user
            )
            st.rerun()

        st.error(result["message"])

    st.write("New to CareerForge?")

    if st.button(
        "Create an Account",
        use_container_width=True,
    ):
        st.session_state.auth_page = "register"
        st.rerun()

    if st.button(
        "← Back to Home",
        key="login_back_to_home",
        use_container_width=True,
    ):
        st.session_state.public_page = "landing"
        st.rerun()


def render_register_page():
    """Render and process the registration form."""

    st.title("CareerForge")
    st.caption("AI Career and Skill-Gap Planner")
    st.subheader("Register")
    st.markdown(
        """
        <p class="cf-auth-copy">
            Create your account and set up a private workspace for
            your skills, career matches, roadmap, and learning progress.
        </p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("register_form"):
        username = st.text_input(
            "Username",
            key="register_username",
        )
        email = st.text_input(
            "Email",
            key="register_email",
        )
        password = st.text_input(
            "Password",
            type="password",
            key="register_password",
        )
        confirm_password = st.text_input(
            "Confirm password",
            type="password",
            key="register_confirm_password",
        )
        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True,
        )

    if submitted:
        result = register_user(
            username,
            email,
            password,
            confirm_password,
            DATABASE_PATH,
        )

        if result["success"]:
            st.session_state.auth_page = "login"
            st.session_state.auth_notice = result["message"]
            st.rerun()

        st.error(result["message"])

    if st.button(
        "Back to Login",
        use_container_width=True,
    ):
        st.session_state.auth_page = "login"
        st.rerun()


def render_authentication():
    """Render the selected authentication screen."""

    form_column, art_column = st.columns([0.82, 1.18], gap="large")

    with form_column:
        notice = st.session_state.pop(
            "auth_notice",
            None,
        )

        if notice:
            st.success(
                f"{notice} You can now log in."
            )

        if st.session_state.auth_page == "register":
            render_register_page()
        else:
            render_login_page()

    with art_column:
        page_name = st.session_state.auth_page
        artwork = image_data_uri(AUTH_BACKGROUND_PATHS[page_name])
        if page_name == "register":
            art_title = "Build a plan around the skills you already have."
            art_copy = "Create your profile once, then use explainable matching, skill-gap analysis, and a practical roadmap in one workspace."
        else:
            art_title = "Your next career move, made clearer."
            art_copy = "Return to your personalized recommendations, learning plan, and saved progress from any device."

        st.markdown(
            f"""
            <div class="cf-auth-art" style="background-image:linear-gradient(180deg,rgba(5,12,28,.05),rgba(5,12,28,.92)),url('{artwork}');">
                <h2>{art_title}</h2><p>{art_copy}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_account_sidebar(username):
    """Render account navigation controls."""

    safe_username = html.escape(username)
    st.sidebar.title("CareerForge")
    st.sidebar.caption("AI Career Planner")
    st.sidebar.markdown(
        f"""
        <div class="cf-sidebar-user">
            <small>Signed in as</small>
            <strong>{safe_username}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button(
        "Logout",
        use_container_width=True,
    ):
        clear_user_state()
        st.rerun()


def render_profile_editor(
    username,
    skill_catalog,
    careers,
):
    """Render the profile form in the sidebar."""

    profile = st.session_state.user_profile
    skill_names = {
        item["id"]: item["name"]
        for item in skill_catalog
    }
    all_skill_ids = list(skill_names)
    all_interests = sorted(
        {
            interest
            for career in careers
            for interest in career["interests"]
        }
    )

    st.sidebar.divider()

    with st.sidebar.expander(
        "Profile Settings",
        expanded=False,
    ):
        st.caption(f"Profile: {username}")

        selected_skills = st.multiselect(
            "Skills to assess",
            options=all_skill_ids,
            default=st.session_state.selected_skills,
            format_func=lambda skill: skill_names[skill],
        )
        st.session_state.selected_skills = selected_skills

        with st.form("profile_form"):
            skill_levels = {}

            for skill in selected_skills:
                skill_levels[skill] = st.slider(
                    skill_names[skill],
                    min_value=0,
                    max_value=10,
                    value=int(
                        profile.get("skills", {}).get(skill, 0)
                    ),
                    key=f"profile_skill_{skill}",
                )

            interests = st.multiselect(
                "Interests",
                options=all_interests,
                default=[
                    item
                    for item in profile.get("interests", [])
                    if item in all_interests
                ],
                format_func=readable_name,
            )
            completed_projects = st.number_input(
                "Completed projects",
                min_value=0,
                max_value=20,
                value=int(profile.get("completed_projects", 0)),
            )
            available_months = st.number_input(
                "Available months",
                min_value=1,
                max_value=24,
                value=int(profile.get("available_months", 4)),
            )
            weekly_hours = st.number_input(
                "Weekly study hours",
                min_value=1,
                max_value=80,
                value=int(profile.get("weekly_hours", 8)),
            )

            submitted = st.form_submit_button(
                "Save and Recalculate",
                use_container_width=True,
            )

    if submitted:
        updated_profile = {
            "skills": skill_levels,
            "interests": interests,
            "completed_projects": int(completed_projects),
            "available_months": int(available_months),
            "weekly_hours": int(weekly_hours),
        }
        save_profile(
            username,
            updated_profile,
            DATABASE_PATH,
        )
        st.session_state.user_profile = updated_profile
        st.session_state.pop("what_if_result", None)
        st.sidebar.success("Profile saved.")

    return st.session_state.user_profile


def build_analysis(profile):
    """Build the main analysis for the current profile."""

    recommendations = recommend_careers(profile, limit=5)

    if not recommendations:
        return None

    top_career = recommendations[0]
    gap_result = analyze_skill_gap(
        profile["skills"],
        top_career["required_skills"],
    )
    readiness = calculate_readiness(
        technical_score=top_career["weighted_score"],
        completion_score=gap_result["completion_percentage"],
        interest_score=top_career["interest_score"],
        completed_projects=profile.get("completed_projects", 0),
        target_projects=top_career.get("target_projects", 2),
    )
    learning_path = generate_learning_path(
        profile["skills"],
        top_career["required_skills"],
    )
    roadmap = generate_roadmap(
        user_skills=profile["skills"],
        required_skills=top_career["required_skills"],
        available_months=profile.get("available_months", 4),
        weekly_hours=profile.get("weekly_hours", 8),
    )

    return {
        "recommendations": recommendations,
        "top_career": top_career,
        "gap": gap_result,
        "readiness": readiness,
        "learning_path": learning_path,
        "roadmap": roadmap,
    }


def open_feature_page(page_name):
    """Open one dashboard feature screen."""

    st.session_state.current_page = page_name
    st.rerun()


def render_dashboard(username):
    """Render six feature cards on the main dashboard."""

    safe_username = html.escape(username)
    artwork = image_data_uri(PAGE_BACKGROUND_PATHS["dashboard"])
    st.markdown(
        f"""
        <div class="cf-dashboard-hero" style="background-image:linear-gradient(90deg,rgba(5,12,28,.12),rgba(5,12,28,.04)),url('{artwork}');">
            <div class="cf-page-eyebrow">Personal career workspace</div>
            <h1>Welcome back, {safe_username}</h1>
            <p>
                Build your career direction with personalized AI
                recommendations, skill analysis, and learning plans.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """<div class="cf-section-heading"><h2>Career planning workspace</h2><p>Select a tool to open its dedicated workspace.</p></div>""",
        unsafe_allow_html=True,
    )

    page_items = list(FEATURE_PAGES.items())

    for row_start in range(0, len(page_items), 3):
        columns = st.columns(3)

        for card_offset, (column, (page_name, page)) in enumerate(zip(
            columns,
            page_items[row_start:row_start + 3],
        )):
            with column:
                with st.container(border=True):
                    st.markdown(
                        f'<span class="cf-card-index">{row_start + card_offset + 1:02d}</span>',
                        unsafe_allow_html=True,
                    )
                    st.subheader(page["title"])
                    st.write(page["description"])
                    st.write("")

                    if st.button(
                        f"Open {page['title']}",
                        key=f"open_{page_name}",
                        use_container_width=True,
                    ):
                        open_feature_page(page_name)


def render_feature_header(page_name):
    """Render a feature title and dashboard back button."""

    page = FEATURE_PAGES[page_name]

    back_column, _ = st.columns([1.45, 5])

    with back_column:
        if st.button(
            "← Dashboard",
            key=f"back_{page_name}",
            use_container_width=True,
        ):
            open_feature_page("dashboard")

    safe_title = html.escape(page["title"])
    safe_description = html.escape(page["description"])
    artwork = image_data_uri(PAGE_BACKGROUND_PATHS[page_name])

    st.markdown(
        f"""
        <div class="cf-feature-hero" style="background-image:linear-gradient(90deg,rgba(5,12,28,.15),rgba(5,12,28,.04)),url('{artwork}');">
            <div class="cf-page-eyebrow">
                CareerForge Workspace
            </div>
            <div class="cf-feature-title">
                <h1>{safe_title}</h1>
            </div>
            <p>{safe_description}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview(analysis):
    """Render top-level metrics and recommendations."""

    top = analysis["top_career"]
    readiness = analysis["readiness"]
    gap = analysis["gap"]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Top Career", top["name"])
    metric_columns[1].metric("Career Match", f"{top['final_score']}%")
    metric_columns[2].metric(
        "Readiness",
        f"{readiness['overall_score']}%",
    )
    metric_columns[3].metric(
        "Requirements Completed",
        f"{gap['completion_percentage']}%",
    )

    chart_data = pd.DataFrame(
        {
            "Career": [
                item["name"]
                for item in analysis["recommendations"]
            ],
            "Score": [
                item["final_score"]
                for item in analysis["recommendations"]
            ],
        }
    ).set_index("Career")

    st.subheader("Top Career Matches")
    st.bar_chart(
        chart_data,
        color="#38bdf8",
    )

    recommendation_rows = [
        {
            "Rank": position,
            "Career": career["name"],
            "Category": career["category"],
            "Final Score": career["final_score"],
            "Cosine": career["cosine_score"],
            "Weighted Skills": career["weighted_score"],
            "Interest": career["interest_score"],
        }
        for position, career in enumerate(
            analysis["recommendations"],
            start=1,
        )
    ]
    st.dataframe(
        pd.DataFrame(recommendation_rows),
        use_container_width=True,
        hide_index=True,
    )


def render_skill_gap(analysis):
    """Render skill gaps and readiness."""

    gap = analysis["gap"]
    readiness = analysis["readiness"]

    st.subheader(f"Skill Gap — {analysis['top_career']['name']}")
    gap_rows = [
        {
            "Skill": readable_name(item["skill"]),
            "Current": item["current_level"],
            "Required": item["required_level"],
            "Gap": item["gap"],
            "Status": item["status"],
        }
        for item in gap["skill_details"]
    ]
    st.dataframe(
        pd.DataFrame(gap_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Career Readiness")
    columns = st.columns(5)
    columns[0].metric("Technical", f"{readiness['technical_score']}%")
    columns[1].metric("Completion", f"{readiness['completion_score']}%")
    columns[2].metric("Interest", f"{readiness['interest_score']}%")
    columns[3].metric("Projects", f"{readiness['project_score']}%")
    columns[4].metric("Overall", f"{readiness['overall_score']}%")
    st.info(f"Readiness level: {readiness['readiness_level']}")


def render_learning_and_roadmap(analysis):
    """Render the learning path and monthly roadmap."""

    learning_path = analysis["learning_path"]
    roadmap = analysis["roadmap"]

    st.subheader("AI Learning Path")

    if learning_path["learning_path"]:
        path_rows = [
            {
                "Step": item["step"],
                "Skill": readable_name(item["skill"]),
                "Current": item["current_level"],
                "Target": item["target_level"],
                "Gap": item["gap"],
                "Reason": item["reason"],
            }
            for item in learning_path["learning_path"]
        ]
        st.dataframe(
            pd.DataFrame(path_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("All required skills have been achieved.")

    st.subheader("Personalized Roadmap")
    roadmap_columns = st.columns(4)
    roadmap_columns[0].metric(
        "Months",
        roadmap["available_months"],
    )
    roadmap_columns[1].metric(
        "Weekly Hours",
        roadmap["weekly_hours"],
    )
    roadmap_columns[2].metric(
        "Estimated Hours",
        roadmap["total_estimated_hours"],
    )
    roadmap_columns[3].metric(
        "Feasible",
        "Yes" if roadmap["feasible"] else "No",
    )

    roadmap_rows = []
    for month in roadmap["months"]:
        if not month["activities"]:
            roadmap_rows.append(
                {
                    "Month": month["month"],
                    "Skill": "Review and practice",
                    "Levels": "-",
                    "Hours": 0,
                }
            )

        for activity in month["activities"]:
            roadmap_rows.append(
                {
                    "Month": month["month"],
                    "Skill": readable_name(activity["skill"]),
                    "Levels": (
                        f"{activity['current_level']} → "
                        f"{activity['target_level']}"
                    ),
                    "Hours": activity["estimated_hours"],
                }
            )

    st.dataframe(
        pd.DataFrame(roadmap_rows),
        use_container_width=True,
        hide_index=True,
    )

    for warning in roadmap["warnings"]:
        st.warning(warning)


def render_what_if(profile, skill_catalog):
    """Render the What-If Simulator."""

    st.subheader("What-If Simulator")
    skill_names = {
        item["id"]: item["name"]
        for item in skill_catalog
    }
    skill = st.selectbox(
        "Skill to improve",
        options=list(skill_names),
        format_func=lambda item: skill_names[item],
    )
    current_level = int(profile.get("skills", {}).get(skill, 0))
    target_levels = list(range(current_level, 11))
    new_level = st.select_slider(
        "New level",
        options=target_levels,
        value=target_levels[-1],
    )

    if st.button(
        "Run Simulation",
        disabled=new_level == current_level,
    ):
        st.session_state.what_if_result = simulate_skill_change(
            profile,
            skill,
            new_level,
            limit=CAREER_COUNT,
        )

    result = st.session_state.get("what_if_result")

    if not result:
        return

    biggest = result["biggest_improvement"]
    if biggest:
        st.success(
            f"Biggest improvement: {biggest['name']} "
            f"(+{biggest['score_change']}%)"
        )

    changed_rows = [
        {
            "Career": item["name"],
            "Before": item["before_score"],
            "After": item["after_score"],
            "Change": item["score_change"],
            "Rank Before": item["before_rank"],
            "Rank After": item["after_rank"],
        }
        for item in result["career_changes"]
        if item["score_change"] != 0
    ]
    st.dataframe(
        pd.DataFrame(changed_rows),
        use_container_width=True,
        hide_index=True,
    )


def render_comparison(profile, careers):
    """Render side-by-side career comparison."""

    st.subheader("Career Comparison")
    career_names = [career["name"] for career in careers]
    first = st.selectbox(
        "First career",
        career_names,
        index=career_names.index("Network Engineer"),
    )
    second = st.selectbox(
        "Second career",
        career_names,
        index=career_names.index("SOC Analyst"),
    )

    if first == second:
        st.warning("Choose two different careers.")
        return

    result = compare_careers(profile, first, second)
    first_result = result["career_a"]
    second_result = result["career_b"]

    comparison_rows = [
        {
            "Metric": "Overall score",
            first: first_result["final_score"],
            second: second_result["final_score"],
        },
        {
            "Metric": "Cosine similarity",
            first: first_result["cosine_score"],
            second: second_result["cosine_score"],
        },
        {
            "Metric": "Weighted skills",
            first: first_result["weighted_score"],
            second: second_result["weighted_score"],
        },
        {
            "Metric": "Interest match",
            first: first_result["interest_score"],
            second: second_result["interest_score"],
        },
    ]
    st.dataframe(
        pd.DataFrame(comparison_rows),
        use_container_width=True,
        hide_index=True,
    )
    st.success(
        f"Overall winner: {result['overall_winner']} "
        f"(difference {result['score_difference']}%)"
    )


def render_progress(username, profile, analysis):
    """Render saved progress and complete the next skill."""

    st.subheader("Progress Tracking")
    gap = analysis["gap"]
    st.progress(gap["completion_percentage"] / 100)
    st.write(
        f"Requirements completed: "
        f"{gap['matched_count']}/{gap['total_skills']} "
        f"({gap['completion_percentage']}%)"
    )

    history = get_progress_history(
        username,
        DATABASE_PATH,
    )

    if history:
        history_rows = [
            {
                "Career": item["career_name"],
                "Skill": readable_name(item["skill"]),
                "Before": item["old_level"],
                "After": item["new_level"],
                "Improvement": item["improvement"],
                "Recorded": item["recorded_at"],
            }
            for item in history
        ]
        st.dataframe(
            pd.DataFrame(history_rows),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No saved progress yet.")

    steps = analysis["learning_path"]["learning_path"]

    if not steps:
        st.success("Career learning path completed.")
        return

    next_step = steps[0]
    st.info(
        f"Next skill: {readable_name(next_step['skill'])} — "
        f"Level {next_step['current_level']} → "
        f"{next_step['target_level']}"
    )

    if st.button("Complete Next Skill"):
        update_result = update_skill_progress(
            profile,
            next_step["skill"],
            next_step["target_level"],
        )
        updated_profile = update_result["updated_profile"]

        duplicate = any(
            item["career_name"] == analysis["top_career"]["name"]
            and item["skill"] == next_step["skill"]
            and item["new_level"] == next_step["target_level"]
            for item in history
        )

        if not duplicate:
            record_skill_progress(
                profile_name=username,
                career_name=analysis["top_career"]["name"],
                skill=next_step["skill"],
                old_level=next_step["current_level"],
                new_level=next_step["target_level"],
                db_path=DATABASE_PATH,
            )

        save_profile(
            username,
            updated_profile,
            DATABASE_PATH,
        )
        st.session_state.user_profile = updated_profile
        st.session_state.pop("what_if_result", None)
        st.rerun()


def main():
    """Run the CareerForge Streamlit application."""

    st.set_page_config(
        page_title="CareerForge",
        page_icon="🎯",
        layout="wide",
    )
    apply_custom_styles()
    initialize_app_state()

    if not st.session_state.authenticated:
        if st.session_state.public_page == "landing":
            apply_landing_styles()
            render_landing_page()
        else:
            apply_workspace_styles()
            render_authentication()
        return

    username = st.session_state.current_user
    apply_workspace_styles()
    initialize_user_state(username)

    careers = load_json(CAREERS_PATH)
    skill_catalog = load_json(SKILLS_PATH)
    render_account_sidebar(username)
    profile = render_profile_editor(
        username,
        skill_catalog,
        careers,
    )

    current_page = st.session_state.current_page

    if current_page == "dashboard":
        render_dashboard(username)
        return

    if current_page not in FEATURE_PAGES:
        st.session_state.current_page = "dashboard"
        st.rerun()

    analysis = build_analysis(profile)

    if analysis is None:
        st.error("No career recommendations were found.")
        return

    render_feature_header(current_page)

    if current_page == "overview":
        render_overview(analysis)
    elif current_page == "skill_gap":
        render_skill_gap(analysis)
    elif current_page == "learning":
        render_learning_and_roadmap(analysis)
    elif current_page == "what_if":
        render_what_if(profile, skill_catalog)
    elif current_page == "compare":
        render_comparison(profile, careers)
    elif current_page == "progress":
        render_progress(username, profile, analysis)


if __name__ == "__main__":
    main()
