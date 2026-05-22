# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64
import os
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Plateforme SAG Relining",
    page_icon="⚙️",
    layout="wide"
)

DEVELOPPEUR = "ATIFI SANA"

# =========================================================
# FONCTIONS
# =========================================================

def get_base64_image(image_path):

    if os.path.exists(image_path):

        with open(image_path, "rb") as img_file:

            return base64.b64encode(
                img_file.read()
            ).decode()

    return None


def couleur_avancement(av):

    if av < 30:
        return "#dc2626"

    elif av < 80:
        return "#f59e0b"

    else:
        return "#16a34a"


def show_kpi(title, value, unit=""):

    st.markdown(f"""
<div class="kpi-card">

<div class="kpi-title">
{title}
</div>

<div class="kpi-value">
{value} {unit}
</div>

</div>
""", unsafe_allow_html=True)

# =========================================================
# PDF
# =========================================================

def generer_pdf(df):

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4
    )

    styles = getSampleStyleSheet()

    elements = []

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        textColor=colors.HexColor("#D97706"),
        fontSize=22
    )

    elements.append(
        Paragraph(
            "Rapport de Suivi du Changement de Blindage SAG",
            title_style
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    total_estime = df["Duree_Estimee_h"].sum()

    total_reel = df["Duree_Reelle_h"].sum()

    avancement = df["Avancement_%"].mean()

    data = [
        ["Indicateur", "Valeur"],

        ["Durée totale estimée",
         f"{total_estime:.1f} h"],

        ["Durée réelle",
         f"{total_reel:.1f} h"],

        ["Avancement global",
         f"{avancement:.1f} %"]
    ]

    table = Table(data, colWidths=[260, 180])

    table.setStyle(TableStyle([

        ("BACKGROUND", (0, 0), (-1, 0),
         colors.HexColor("#111827")),

        ("TEXTCOLOR", (0, 0), (-1, 0),
         colors.white),

        ("GRID", (0, 0), (-1, -1),
         0.5, colors.grey),

        ("FONTNAME", (0, 0), (-1, 0),
         "Helvetica-Bold"),

        ("PADDING", (0, 0), (-1, -1),
         8)

    ]))

    elements.append(table)

    doc.build(elements)

    buffer.seek(0)

    return buffer

# =========================================================
# IMAGES
# =========================================================

blindage_img = get_base64_image(
    "blindage.jpeg"
)

logo_img = get_base64_image(
    "Managem cropped.jpeg"
)

# =========================================================
# BACKGROUND
# =========================================================

if blindage_img:

    st.markdown(f"""
<style>

.stApp {{

    background:
        radial-gradient(
            circle at center,
            rgba(35,35,35,0.80) 0%,
            rgba(15,15,15,0.95) 55%,
            rgba(0,0,0,1) 100%
        );

    color: white;
    overflow-x: hidden;
}}

.stApp::before {{

    content: "";

    position: fixed;

    top: 50%;
    left: 50%;

    width: 850px;
    height: 850px;

    transform:
        translate(-50%, -50%);

    z-index: 0;

    pointer-events: none;

    background-image:

        radial-gradient(
            circle,
            rgba(0,0,0,0) 20%,
            rgba(0,0,0,0.20) 55%,
            rgba(0,0,0,0.80) 82%,
            rgba(0,0,0,1) 100%
        ),

        url(
            "data:image/jpeg;base64,{blindage_img}"
        );

    background-size: cover;

    background-repeat: no-repeat;

    background-position: center;

    opacity: 0.32;

    animation:
        rotateBlindage 85s linear infinite;
}}

@keyframes rotateBlindage {{

    from {{

        transform:
            translate(-50%, -50%)
            rotate(0deg);

    }}

    to {{

        transform:
            translate(-50%, -50%)
            rotate(360deg);

    }}
}}

.stApp > div {{

    position: relative;
    z-index: 1;
}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# CSS
# =========================================================

st.markdown("""
<style>

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

.block-container {
    max-width: 96%;
    padding-top: 1rem;
}

.top-header {

    display: flex;
    align-items: center;
    gap: 40px;

    padding: 30px 45px;

    margin-top: 10px;
    margin-bottom: 35px;

    background:
        linear-gradient(
            135deg,
            rgba(0,0,0,0.82),
            rgba(35,35,35,0.70)
        );

    border:
        1px solid rgba(245,158,11,0.45);

    border-radius: 30px;

    backdrop-filter: blur(10px);
}

.logo-zone {

    width: 320px;
    min-width: 320px;

    height: 180px;

    display: flex;

    align-items: center;
    justify-content: center;

    background:
        radial-gradient(
            circle,
            rgba(0,0,0,0.90),
            rgba(0,0,0,0.55),
            rgba(0,0,0,0)
        );

    border-radius: 28px;
}

.logo-managem {

    width: 270px;

    object-fit: contain;
}

.header-small {

    color: #f59e0b;

    font-size: 16px;

    font-weight: 900;

    letter-spacing: 2px;
}

.header-title {

    color: white;

    font-size: 44px;

    font-weight: 900;

    line-height: 1.1;
}

.header-subtitle {

    color: #e7e5e4;

    font-size: 18px;

    margin-top: 10px;
}

.dev-signature {

    color: #f59e0b;

    margin-top: 12px;

    font-weight: 700;
}

.kpi-card {

    background:
        linear-gradient(
            145deg,
            rgba(20,20,20,0.90),
            rgba(45,45,45,0.75)
        );

    border:
        1px solid rgba(245,158,11,0.40);

    border-radius: 24px;

    padding: 24px;

    text-align: center;
}

.kpi-title {

    font-size: 15px;

    color: #d6d3d1;
}

.kpi-value {

    font-size: 32px;

    font-weight: 900;

    color: #f59e0b;
}

.synoptic-card {

    background:
        rgba(25,25,25,0.82);

    border-radius: 22px;

    padding: 22px;

    text-align: center;
}

.footer-text {

    text-align: center;

    color: #d6d3d1;

    font-size: 13px;

    margin-top: 20px;
}

</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

if logo_img:

    st.markdown(f"""
<div class="top-header">

<div class="logo-zone">

<img
src="data:image/jpeg;base64,{logo_img}"
class="logo-managem">

</div>

<div>

<div class="header-small">
MANAGEM - SITE TIZERT
</div>

<div class="header-title">
Plateforme de Suivi du Changement de Blindage SAG
</div>

<div class="header-subtitle">
Suivi terrain • KPI • Dashboard • Rapport PDF
</div>

<div class="dev-signature">
Développée par : {DEVELOPPEUR}
</div>

</div>

</div>
""", unsafe_allow_html=True)

# =========================================================
# DONNÉES
# =========================================================

etapes_base = [

    {
        "Zone": "Fond d'entrée",
        "Etape": "Démontage",
        "Qty": 1,
        "Duree_Estimee_h": 2.0
    },

    {
        "Zone": "Fond d'entrée",
        "Etape": "Montage outer liners",
        "Qty": 32,
        "Duree_Estimee_h": 13.3
    },

    {
        "Zone": "Virole",
        "Etape": "Montage shell liner",
        "Qty": 60,
        "Duree_Estimee_h": 50.0
    },

    {
        "Zone": "Fond de décharge",
        "Etape": "Montage grate",
        "Qty": 32,
        "Duree_Estimee_h": 16.0
    }

]

df_base = pd.DataFrame(etapes_base)

# =========================================================
# SESSION
# =========================================================

if "data" not in st.session_state:

    df_init = df_base.copy()

    df_init["Statut"] = "Non démarré"
    df_init["Avancement_%"] = 0
    df_init["Duree_Reelle_h"] = 0

    st.session_state.data = df_init

# =========================================================
# TABS
# =========================================================

tab1, tab2 = st.tabs([
    "Saisie & Suivi terrain",
    "Dashboard & Rapport"
])

# =========================================================
# ONGLET 1
# =========================================================

with tab1:

    st.markdown(
        "## Saisie & Suivi terrain"
    )

# =========================================================
# ONGLET 2
# =========================================================

with tab2:

    st.markdown(
        "## Synoptique SAG"
    )

    df = st.session_state.data.copy()

    zone_progress = df.groupby(
        "Zone",
        as_index=False
    )["Avancement_%"].mean()

    cols = st.columns(3)

    for i, row in zone_progress.iterrows():

        with cols[i % 3]:

            color = couleur_avancement(
                row["Avancement_%"]
            )

            st.markdown(f"""
<div class="synoptic-card"
style="
border:2px solid {color};
">

<h3>{row['Zone']}</h3>

<div style="
font-size:34px;
font-weight:900;
color:{color};
">
{row['Avancement_%']:.1f}%
</div>

</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(
        "## Rapport PDF professionnel"
    )

    if "Duree_Reelle_h" not in df.columns:
        df["Duree_Reelle_h"] = 0

    pdf_buffer = generer_pdf(df)

    st.download_button(
        label="Télécharger le rapport PDF",
        data=pdf_buffer,
        file_name="rapport_blindage_SAG.pdf",
        mime="application/pdf"
    )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    f"""
<div class="footer-text">

Développée par :
{DEVELOPPEUR}

</div>
""",
    unsafe_allow_html=True
)
