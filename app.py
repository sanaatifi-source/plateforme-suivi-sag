import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import base64
import os
import io

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False


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
            return base64.b64encode(img_file.read()).decode()
    return None


def calculer_duree_reelle(debut, fin):
    try:
        if str(debut).strip() == "" or str(fin).strip() == "":
            return None

        h1 = datetime.strptime(str(debut).strip(), "%H:%M")
        h2 = datetime.strptime(str(fin).strip(), "%H:%M")

        duree = (h2 - h1).total_seconds() / 3600

        if duree < 0:
            duree += 24

        return round(duree, 2)

    except Exception:
        return None


def couleur_avancement(avancement):
    if avancement < 30:
        return "#dc2626"
    elif avancement < 80:
        return "#f59e0b"
    else:
        return "#16a34a"


def show_kpi(title, value, unit=""):
    st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">{title}</div>
    <div class="kpi-value">{value} {unit}</div>
</div>
""", unsafe_allow_html=True)


def generer_pdf(df, checklist, equipes, events):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=28,
        leftMargin=28,
        topMargin=28,
        bottomMargin=28
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        textColor=colors.HexColor("#D97706"),
        fontSize=18,
        spaceAfter=14
    )

    subtitle_style = ParagraphStyle(
        "SubtitleCustom",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#111827"),
        fontSize=13,
        spaceAfter=8
    )

    elements = []

    df = df.copy()

    if "Duree_Reelle_h" not in df.columns:
        df["Duree_Reelle_h"] = df.apply(
            lambda row: calculer_duree_reelle(
                row["Heure_debut_reelle"],
                row["Heure_fin_reelle"]
            ),
            axis=1
        )

    df["Duree_Dashboard_h"] = df["Duree_Reelle_h"].fillna(df["Duree_Estimee_h"])

    total_estime = df["Duree_Estimee_h"].sum()
    total_reel = df["Duree_Reelle_h"].sum()
    avancement_global = df["Avancement_%"].mean()
    nb_retards = len(df[df["Retard_detecte"] == "Oui"])
    nb_bloques = len(df[df["Statut"] == "Bloqué"])
    taux_checklist = sum(checklist.values()) / len(checklist) * 100

    elements.append(Paragraph("Rapport de Suivi du Changement de Blindage SAG", title_style))
    elements.append(Paragraph("Managem - Site Tizert", styles["Normal"]))
    elements.append(Paragraph(f"Développée par : {DEVELOPPEUR}", styles["Normal"]))
    elements.append(Paragraph(f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("1. Synthèse générale", subtitle_style))

    data_kpi = [
        ["Indicateur", "Valeur"],
        ["Durée totale estimée", f"{total_estime:.1f} h"],
        ["Durée réelle renseignée", f"{total_reel:.1f} h"],
        ["Avancement global", f"{avancement_global:.1f} %"],
        ["Étapes bloquées", str(nb_bloques)],
        ["Retards détectés", str(nb_retards)],
        ["Checklist validée", f"{taux_checklist:.0f} %"],
    ]

    table_kpi = Table(data_kpi, colWidths=[260, 180])
    table_kpi.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(table_kpi)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("2. Durées par zone", subtitle_style))

    zone_duration = df.groupby("Zone", as_index=False)["Duree_Dashboard_h"].sum()

    data_zone = [["Zone", "Durée dashboard (h)"]]
    for _, row in zone_duration.iterrows():
        data_zone.append([row["Zone"], f"{row['Duree_Dashboard_h']:.1f}"])

    table_zone = Table(data_zone, colWidths=[260, 180])
    table_zone.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D97706")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(table_zone)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("3. Gestion des équipes", subtitle_style))

    data_eq = [["Équipe", "Responsable", "Nb", "Mission"]]
    for eq in equipes:
        data_eq.append([
            str(eq.get("Equipe", "")),
            str(eq.get("Responsable", "")),
            str(eq.get("Nb_intervenants", "")),
            str(eq.get("Mission", ""))
        ])

    table_eq = Table(data_eq, colWidths=[120, 110, 50, 170])
    table_eq.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(table_eq)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("4. Événements terrain", subtitle_style))

    data_ev = [["Heure", "Zone", "Type", "Commentaire"]]
    for ev in events[-12:]:
        data_ev.append([
            str(ev.get("Heure", "")),
            str(ev.get("Zone", ""))[:20],
            str(ev.get("Type", ""))[:20],
            str(ev.get("Evenement", ""))[:45]
        ])

    table_ev = Table(data_ev, colWidths=[45, 90, 80, 230])
    table_ev.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D97706")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 6.5),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(table_ev)
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("5. Checklist sécurité / qualité", subtitle_style))

    data_check = [["Point de contrôle", "Statut"]]
    for k, v in checklist.items():
        data_check.append([k, "Validé" if v else "Non validé"])

    table_check = Table(data_check, colWidths=[300, 140])
    table_check.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 7),
    ]))
    elements.append(table_check)

    doc.build(elements)
    buffer.seek(0)

    return buffer


# =========================================================
# IMAGES
# =========================================================

blindage_img = get_base64_image("blindage.jpeg")
logo_img = get_base64_image("Managem cropped.jpeg")


# =========================================================
# BACKGROUND
# =========================================================

if blindage_img:
    st.markdown(f"""
<style>
.stApp {{
    background:
        radial-gradient(circle at center,
        rgba(38,38,38,0.82) 0%,
        rgba(15,15,15,0.95) 52%,
        rgba(0,0,0,1) 100%);
    color: white;
    overflow-x: hidden;
}}

.stApp::before {{
    content: "";
    position: fixed;
    top: 50%;
    left: 50%;
    width: 950px;
    height: 950px;
    transform: translate(-50%, -50%);
    z-index: 0;
    pointer-events: none;

    background-image:
        radial-gradient(circle,
            rgba(0,0,0,0) 22%,
            rgba(0,0,0,0.16) 48%,
            rgba(0,0,0,0.68) 76%,
            rgba(0,0,0,1) 100%),
        url("data:image/jpeg;base64,{blindage_img}");

    background-size: cover;
    background-repeat: no-repeat;
    background-position: center;
    opacity: 0.27;
    filter: brightness(0.78) contrast(1.12) blur(0.35px);
    animation: rotateBlindage 85s linear infinite;
}}

@keyframes rotateBlindage {{
    from {{
        transform: translate(-50%, -50%) rotate(0deg);
    }}
    to {{
        transform: translate(-50%, -50%) rotate(360deg);
    }}
}}

.stApp > div {{
    position: relative;
    z-index: 1;
}}
</style>
""", unsafe_allow_html=True)
else:
    st.markdown("""
<style>
.stApp {
    background: #111111;
    color: white;
}
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

[data-testid="stToolbar"] {
    display: none;
}

.block-container {
    max-width: 95%;
    padding-top: 1rem;
}

.top-header {
    display: flex;
    align-items: center;
    gap: 42px;
    padding: 32px 52px;
    margin-top: 12px;
    margin-bottom: 38px;
    background: linear-gradient(135deg, rgba(0,0,0,0.82), rgba(35,35,35,0.74));
    border: 1px solid rgba(245,158,11,0.48);
    border-radius: 30px;
    backdrop-filter: blur(12px);
    box-shadow: 0 0 42px rgba(245,158,11,0.16);
}

.logo-zone {
    width: 310px;
    min-width: 310px;
    height: 170px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: radial-gradient(circle, rgba(0,0,0,0.90), rgba(0,0,0,0.62), rgba(0,0,0,0));
    border-radius: 30px;
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
    font-size: 42px;
    font-weight: 900;
    line-height: 1.12;
}

.header-subtitle {
    color: #e7e5e4;
    font-size: 18px;
    margin-top: 10px;
}

.dev-signature {
    color: #f59e0b;
    margin-top: 14px;
    font-weight: 700;
}

.kpi-card {
    background: linear-gradient(145deg, rgba(28,28,28,0.88), rgba(45,45,45,0.72));
    border: 1px solid rgba(245,158,11,0.44);
    border-radius: 24px;
    padding: 24px;
    text-align: center;
    min-height: 115px;
}

.kpi-title {
    font-size: 15px;
    color: #e7e5e4;
    margin-bottom: 8px;
}

.kpi-value {
    font-size: 30px;
    font-weight: 900;
    color: #f59e0b;
    word-break: break-word;
}

.stTabs [data-baseweb="tab"] {
    font-size: 17px;
    font-weight: 700;
}

.stTabs [aria-selected="true"] {
    color: #f59e0b !important;
}

.synoptic-card {
    background: rgba(25,25,25,0.78);
    border-radius: 24px;
    padding: 24px;
    text-align: center;
    margin-bottom: 15px;
}

.event-card {
    background: rgba(20,20,20,0.80);
    border-left: 4px solid #f59e0b;
    border-radius: 14px;
    padding: 14px 18px;
    margin-bottom: 12px;
}

.field-box {
    background: rgba(25,25,25,0.74);
    border: 1px solid rgba(245,158,11,0.28);
    border-radius: 20px;
    padding: 18px;
    margin-bottom: 20px;
}

div[data-baseweb="input"] {
    background-color: rgba(20,20,20,0.95) !important;
    border-radius: 14px !important;
}

div[data-baseweb="input"] input {
    color: white !important;
    background-color: rgba(20,20,20,0.95) !important;
}

div[data-baseweb="textarea"] {
    background-color: rgba(20,20,20,0.95) !important;
    border-radius: 14px !important;
}

div[data-baseweb="textarea"] textarea {
    color: white !important;
    background-color: rgba(20,20,20,0.95) !important;
}

div[data-baseweb="select"] > div {
    background-color: rgba(20,20,20,0.95) !important;
    color: white !important;
}

div[data-baseweb="select"] span {
    color: white !important;
}

label, p, span {
    color: #f5f5f5 !important;
}

div[data-testid="stExpander"] {
    background: rgba(15,15,15,0.84) !important;
    border: 1px solid rgba(245,158,11,0.25) !important;
    border-radius: 18px !important;
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
        <img src="data:image/jpeg;base64,{logo_img}" class="logo-managem">
    </div>
    <div>
        <div class="header-small">MANAGEM - SITE TIZERT</div>
        <div class="header-title">Plateforme de Suivi du Changement de Blindage SAG</div>
        <div class="header-subtitle">Suivi terrain • Équipes • Événements • Synoptique • Rapport PDF</div>
        <div class="dev-signature">Développée par : {DEVELOPPEUR}</div>
    </div>
</div>
""", unsafe_allow_html=True)
else:
    st.markdown(f"""
<div class="top-header">
    <div>
        <div class="header-small">MANAGEM - SITE TIZERT</div>
        <div class="header-title">Plateforme de Suivi du Changement de Blindage SAG</div>
        <div class="header-subtitle">Suivi terrain • Équipes • Événements • Synoptique • Rapport PDF</div>
        <div class="dev-signature">Développée par : {DEVELOPPEUR}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# DONNÉES
# =========================================================

zones = [
    "Fond d'entrée",
    "Virole",
    "Fond de décharge",
    "Serrage final / Vérification finale"
]

zones_synoptique = [
    "Fond d'entrée",
    "Virole",
    "Fond de décharge"
]

etapes_base = [
    {"Zone": "Fond d'entrée", "Etape": "Démontage du centre vers l'extrémité", "Qty": 1, "Duree_Estimee_h": 2.0},
    {"Zone": "Fond d'entrée", "Etape": "Montage outer head liners", "Qty": 32, "Duree_Estimee_h": 13.3},
    {"Zone": "Fond d'entrée", "Etape": "Montage middle head liners", "Qty": 16, "Duree_Estimee_h": 6.7},
    {"Zone": "Fond d'entrée", "Etape": "Montage inner head liners", "Qty": 8, "Duree_Estimee_h": 3.3},
    {"Zone": "Fond d'entrée", "Etape": "Montage filler ring segment", "Qty": 32, "Duree_Estimee_h": 5.3},
    {"Zone": "Fond d'entrée", "Etape": "Serrage initial 40-50%", "Qty": 1, "Duree_Estimee_h": 1.5},
    {"Zone": "Fond d'entrée", "Etape": "Rotation broyeur et répétition", "Qty": 1, "Duree_Estimee_h": 2.0},

    {"Zone": "Virole", "Etape": "Démontage des lignes de blindage", "Qty": 1, "Duree_Estimee_h": 6.0},
    {"Zone": "Virole", "Etape": "Contrôle revêtement caoutchouc", "Qty": 1, "Duree_Estimee_h": 2.0},
    {"Zone": "Virole", "Etape": "Montage shell liner 1", "Qty": 60, "Duree_Estimee_h": 50.0},
    {"Zone": "Virole", "Etape": "Montage shell liner 2", "Qty": 60, "Duree_Estimee_h": 50.0},
    {"Zone": "Virole", "Etape": "Montage shell liner 3", "Qty": 60, "Duree_Estimee_h": 50.0},
    {"Zone": "Virole", "Etape": "Installation rubber strip", "Qty": 180, "Duree_Estimee_h": 30.0},
    {"Zone": "Virole", "Etape": "Changement revêtement caoutchouc si endommagé", "Qty": 35, "Duree_Estimee_h": 30.0},
    {"Zone": "Virole", "Etape": "Serrage initial 40-50%", "Qty": 1, "Duree_Estimee_h": 2.0},
    {"Zone": "Virole", "Etape": "Rotation broyeur et répétition jusqu'à finition", "Qty": 1, "Duree_Estimee_h": 3.0},

    {"Zone": "Fond de décharge", "Etape": "Démontage centre vers extrémité", "Qty": 1, "Duree_Estimee_h": 2.0},
    {"Zone": "Fond de décharge", "Etape": "Montage grate", "Qty": 32, "Duree_Estimee_h": 16.0},
    {"Zone": "Fond de décharge", "Etape": "Montage lift bar 1", "Qty": 32, "Duree_Estimee_h": 16.0},
    {"Zone": "Fond de décharge", "Etape": "Montage cover plate 1", "Qty": 16, "Duree_Estimee_h": 8.0},
    {"Zone": "Fond de décharge", "Etape": "Montage middle lifter 2", "Qty": 8, "Duree_Estimee_h": 4.0},
    {"Zone": "Fond de décharge", "Etape": "Montage cover plate 2", "Qty": 8, "Duree_Estimee_h": 2.7},
    {"Zone": "Fond de décharge", "Etape": "Montage inner lifter 3", "Qty": 8, "Duree_Estimee_h": 2.7},
    {"Zone": "Fond de décharge", "Etape": "Montage filler ring segment 10", "Qty": 40, "Duree_Estimee_h": 13.3},
    {"Zone": "Fond de décharge", "Etape": "Montage filler ring segment 11", "Qty": 32, "Duree_Estimee_h": 10.7},
    {"Zone": "Fond de décharge", "Etape": "Montage outer lifter", "Qty": 32, "Duree_Estimee_h": 10.7},
    {"Zone": "Fond de décharge", "Etape": "Serrage initial 40-50%", "Qty": 1, "Duree_Estimee_h": 2.0},
    {"Zone": "Fond de décharge", "Etape": "Rotation broyeur et répétition", "Qty": 1, "Duree_Estimee_h": 2.0},

    {"Zone": "Serrage final / Vérification finale", "Etape": "Serrage final boulons M48 / M42 / M36 à 100%", "Qty": 1, "Duree_Estimee_h": 6.0},
    {"Zone": "Serrage final / Vérification finale", "Etape": "Contrôle absence d'espace entre blindages", "Qty": 1, "Duree_Estimee_h": 1.5},
    {"Zone": "Serrage final / Vérification finale", "Etape": "Contrôle alignement des blindages", "Qty": 1, "Duree_Estimee_h": 1.5},
    {"Zone": "Serrage final / Vérification finale", "Etape": "Nettoyage final de la zone", "Qty": 1, "Duree_Estimee_h": 2.0},
    {"Zone": "Serrage final / Vérification finale", "Etape": "Inventaire outillage", "Qty": 1, "Duree_Estimee_h": 1.0},
    {"Zone": "Serrage final / Vérification finale", "Etape": "Scan 3D du blindage", "Qty": 1, "Duree_Estimee_h": 2.0},
]

df_base = pd.DataFrame(etapes_base)


# =========================================================
# SESSION STATE
# =========================================================

if "data" not in st.session_state:
    df_init = df_base.copy()
    df_init["Statut"] = "Non démarré"
    df_init["Avancement_%"] = 0
    df_init["Heure_debut_reelle"] = ""
    df_init["Heure_fin_reelle"] = ""
    df_init["Equipe_responsable"] = ""
    df_init["Commentaire_terrain"] = ""
    df_init["Probleme_rencontre"] = ""
    df_init["Retard_detecte"] = "Non"
    df_init["Cause_retard"] = ""
    df_init["Action_corrective"] = ""
    df_init["Responsable_action"] = ""
    df_init["Priorite"] = "Normale"
    st.session_state.data = df_init

if "checklist" not in st.session_state:
    st.session_state.checklist = {
        "Consignation validée": False,
        "Permis de travail validé": False,
        "Espace confiné contrôlé": False,
        "Ventilation en place": False,
        "Éclairage OK": False,
        "Outillage disponible": False,
        "Absence d’espace entre blindages": False,
        "Alignement contrôlé": False,
        "Nettoyage final effectué": False
    }

if "equipes" not in st.session_state:
    st.session_state.equipes = [
        {"Equipe": "Équipe mécanique", "Responsable": "", "Nb_intervenants": 4, "Mission": "Démontage / montage blindage"},
        {"Equipe": "Équipe sécurité", "Responsable": "", "Nb_intervenants": 1, "Mission": "Contrôle SST / espace confiné"},
        {"Equipe": "Équipe levage", "Responsable": "", "Nb_intervenants": 2, "Mission": "Manutention / levage"},
        {"Equipe": "Supervision", "Responsable": "", "Nb_intervenants": 1, "Mission": "Coordination arrêt"},
    ]

if "events" not in st.session_state:
    st.session_state.events = []


# =========================================================
# ONGLETS
# =========================================================

tab1, tab2 = st.tabs([
    "Saisie & Suivi terrain",
    "Dashboard & Rapport"
])


# =========================================================
# ONGLET 1 : SAISIE TERRAIN
# =========================================================

with tab1:
    st.markdown("## Saisie & Suivi terrain")

    data = st.session_state.data.copy()

    selected_zone = st.selectbox(
        "Sélectionner la zone d’intervention",
        zones
    )

    zone_df = data[data["Zone"] == selected_zone].copy()

    st.markdown(f"### Zone sélectionnée : {selected_zone}")

    st.markdown("""
<div class="field-box">
Cette zone permet de renseigner l’avancement réel, les heures terrain,
les équipes, les problèmes rencontrés et les écarts.
</div>
""", unsafe_allow_html=True)

    for idx, row in zone_df.iterrows():
        with st.expander(f"{row['Etape']} — Quantité : {row['Qty']}", expanded=False):

            c1, c2 = st.columns([1, 1])

            with c1:
                statut = st.selectbox(
                    "Statut",
                    ["Non démarré", "En cours", "Terminé", "Bloqué"],
                    index=["Non démarré", "En cours", "Terminé", "Bloqué"].index(row["Statut"]),
                    key=f"statut_{idx}"
                )

                avancement = st.slider(
                    "Avancement (%)",
                    min_value=0,
                    max_value=100,
                    value=int(row["Avancement_%"]),
                    key=f"av_{idx}"
                )

                heure_debut = st.text_input(
                    "Heure début réelle",
                    value=row["Heure_debut_reelle"],
                    placeholder="Exemple : 08:30",
                    key=f"debut_{idx}"
                )

                heure_fin = st.text_input(
                    "Heure fin réelle",
                    value=row["Heure_fin_reelle"],
                    placeholder="Exemple : 14:00",
                    key=f"fin_{idx}"
                )

            with c2:
                equipe = st.text_input(
                    "Équipe responsable",
                    value=row["Equipe_responsable"],
                    placeholder="Exemple : Équipe mécanique",
                    key=f"eq_{idx}"
                )

                commentaire = st.text_area(
                    "Commentaire terrain",
                    value=row["Commentaire_terrain"],
                    key=f"com_{idx}"
                )

                probleme = st.text_area(
                    "Problème rencontré",
                    value=row["Probleme_rencontre"],
                    key=f"pb_{idx}"
                )

            st.markdown("#### Écarts terrain")

            c3, c4, c5 = st.columns([1, 1, 1])

            with c3:
                retard = st.selectbox(
                    "Retard détecté",
                    ["Non", "Oui"],
                    index=["Non", "Oui"].index(row["Retard_detecte"]),
                    key=f"retard_{idx}"
                )

                priorite = st.selectbox(
                    "Priorité",
                    ["Normale", "Moyenne", "Élevée", "Critique"],
                    index=["Normale", "Moyenne", "Élevée", "Critique"].index(row["Priorite"]),
                    key=f"prio_{idx}"
                )

            with c4:
                cause_retard = st.text_area(
                    "Cause du retard",
                    value=row["Cause_retard"],
                    key=f"cause_{idx}"
                )

            with c5:
                action_corrective = st.text_area(
                    "Action corrective",
                    value=row["Action_corrective"],
                    key=f"action_{idx}"
                )

                responsable_action = st.text_input(
                    "Responsable action",
                    value=row["Responsable_action"],
                    key=f"resp_{idx}"
                )

            data.loc[idx, "Statut"] = statut
            data.loc[idx, "Avancement_%"] = avancement
            data.loc[idx, "Heure_debut_reelle"] = heure_debut
            data.loc[idx, "Heure_fin_reelle"] = heure_fin
            data.loc[idx, "Equipe_responsable"] = equipe
            data.loc[idx, "Commentaire_terrain"] = commentaire
            data.loc[idx, "Probleme_rencontre"] = probleme
            data.loc[idx, "Retard_detecte"] = retard
            data.loc[idx, "Cause_retard"] = cause_retard
            data.loc[idx, "Action_corrective"] = action_corrective
            data.loc[idx, "Responsable_action"] = responsable_action
            data.loc[idx, "Priorite"] = priorite

    st.session_state.data = data

    st.markdown("---")
    st.markdown("## Contrôle qualité / sécurité")

    checklist = st.session_state.checklist.copy()

    c1, c2, c3 = st.columns(3)

    items = list(checklist.keys())

    for i, item in enumerate(items):
        if i % 3 == 0:
            with c1:
                checklist[item] = st.checkbox(item, value=checklist[item], key=f"chk_{item}")
        elif i % 3 == 1:
            with c2:
                checklist[item] = st.checkbox(item, value=checklist[item], key=f"chk_{item}")
        else:
            with c3:
                checklist[item] = st.checkbox(item, value=checklist[item], key=f"chk_{item}")

    st.session_state.checklist = checklist

    st.markdown("---")
    st.markdown("## Gestion des équipes")

    equipes_df = pd.DataFrame(st.session_state.equipes)

    edited_equipes = st.data_editor(
        equipes_df,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_equipes"
    )

    st.session_state.equipes = edited_equipes.to_dict("records")

    st.markdown("---")
    st.markdown("## Journal des événements terrain")

    c_ev1, c_ev2 = st.columns(2)

    with c_ev1:
        ev_zone = st.selectbox("Zone événement", zones, key="ev_zone")
        ev_type = st.selectbox(
            "Type d’événement",
            ["Information", "Retard", "Blocage", "Action corrective", "Sécurité", "Qualité"],
            key="ev_type"
        )

    with c_ev2:
        ev_resp = st.text_input("Responsable événement", key="ev_resp")
        ev_comment = st.text_area("Commentaire événement", key="ev_comment")

    if st.button("Ajouter l’événement"):
        st.session_state.events.append({
            "Heure": datetime.now().strftime("%H:%M"),
            "Zone": ev_zone,
            "Type": ev_type,
            "Evenement": ev_comment,
            "Responsable": ev_resp
        })
        st.success("Événement ajouté au journal terrain.")

    if len(st.session_state.events) > 0:
        st.markdown("### Derniers événements")
        for ev in reversed(st.session_state.events[-6:]):
            st.markdown(f"""
<div class="event-card">
    <b>{ev['Heure']} | {ev['Type']} | {ev['Zone']}</b><br>
    Responsable : {ev['Responsable']}<br>
    Commentaire : {ev['Evenement']}
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## Synthèse terrain")

    taux_checklist = sum(st.session_state.checklist.values()) / len(st.session_state.checklist) * 100
    nb_blocages = len(st.session_state.data[st.session_state.data["Statut"] == "Bloqué"])
    nb_retards = len(st.session_state.data[st.session_state.data["Retard_detecte"] == "Oui"])
    nb_events = len(st.session_state.events)

    c4, c5, c6, c7 = st.columns(4)

    with c4:
        show_kpi("Checklist validée", f"{taux_checklist:.0f}", "%")

    with c5:
        show_kpi("Étapes bloquées", nb_blocages, "")

    with c6:
        show_kpi("Retards détectés", nb_retards, "")

    with c7:
        show_kpi("Événements terrain", nb_events, "")


# =========================================================
# ONGLET 2 : DASHBOARD & RAPPORT
# =========================================================

with tab2:
    st.markdown("## Dashboard & Rapport")

    df = st.session_state.data.copy()

    df["Duree_Reelle_h"] = df.apply(
        lambda row: calculer_duree_reelle(
            row["Heure_debut_reelle"],
            row["Heure_fin_reelle"]
        ),
        axis=1
    )

    df["Duree_Dashboard_h"] = df["Duree_Reelle_h"].fillna(df["Duree_Estimee_h"])

    duree_totale_estimee = df["Duree_Estimee_h"].sum()
    duree_totale_reelle = df["Duree_Reelle_h"].sum()
    nb_etapes_renseignees = df["Duree_Reelle_h"].notna().sum()
    avancement_global = df["Avancement_%"].mean()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        show_kpi("Durée totale estimée", f"{duree_totale_estimee:.1f}", "h")

    with c2:
        show_kpi("Durée réelle renseignée", f"{duree_totale_reelle:.1f}", "h")

    with c3:
        show_kpi("Avancement global", f"{avancement_global:.1f}", "%")

    with c4:
        show_kpi("Étapes renseignées", nb_etapes_renseignees, "")

    st.markdown("---")
    st.markdown("## Synoptique SAG")

    zone_progress = (
        df[df["Zone"].isin(zones_synoptique)]
        .groupby("Zone", as_index=False)["Avancement_%"]
        .mean()
    )

    syn_cols = st.columns(3)

    for i, z in enumerate(zones_synoptique):
        with syn_cols[i]:
            if z in zone_progress["Zone"].values:
                av = float(zone_progress[zone_progress["Zone"] == z]["Avancement_%"].iloc[0])
            else:
                av = 0.0

            color = couleur_avancement(av)

            st.markdown(f"""
<div class="synoptic-card" style="border: 2px solid {color};">
    <h3>{z}</h3>
    <div style="font-size:34px; font-weight:900; color:{color};">
        {av:.1f}%
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("## Analyse des durées")

    col1, col2 = st.columns(2)

    with col1:
        zone_select = st.selectbox(
            "Choisir une zone",
            zones,
            key="dash_zone"
        )

    etapes_zone = df[df["Zone"] == zone_select]["Etape"].tolist()

    with col2:
        etape_select = st.selectbox(
            "Choisir une étape",
            etapes_zone,
            key="dash_etape"
        )

    selected_row = df[
        (df["Zone"] == zone_select)
        &
        (df["Etape"] == etape_select)
    ].iloc[0]

    duree_reelle = selected_row["Duree_Reelle_h"]
    duree_estimee = selected_row["Duree_Estimee_h"]

    c5, c6, c7 = st.columns(3)

    with c5:
        show_kpi("Durée estimée étape", f"{duree_estimee:.1f}", "h")

    with c6:
        if pd.notna(duree_reelle):
            show_kpi("Durée réelle étape", f"{duree_reelle:.1f}", "h")
        else:
            show_kpi("Durée réelle étape", "Non saisie", "")

    with c7:
        if pd.notna(duree_reelle):
            ecart = duree_reelle - duree_estimee
            show_kpi("Écart", f"{ecart:.1f}", "h")
        else:
            show_kpi("Écart", "-", "")

    st.markdown("---")
    st.markdown("### Répartition des zones selon la durée")

    zone_duration = df.groupby("Zone", as_index=False)["Duree_Dashboard_h"].sum()

    fig_zone_duree = px.pie(
        zone_duration,
        names="Zone",
        values="Duree_Dashboard_h",
        title="Répartition de la durée par zone"
    )

    fig_zone_duree.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#ffffff"
    )

    st.plotly_chart(fig_zone_duree, use_container_width=True)

    st.markdown("### Durée des étapes par zone")

    for z in zones_synoptique:
        st.markdown(f"#### {z}")

        df_zone = df[df["Zone"] == z]

        fig = px.bar(
            df_zone,
            x="Etape",
            y="Duree_Dashboard_h",
            text="Duree_Dashboard_h",
            color="Etape"
        )

        fig.update_traces(texttemplate="%{text:.1f} h", textposition="outside")

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#ffffff",
            xaxis_tickangle=-30,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("## Rapport PDF professionnel")

    if REPORTLAB_OK:
        pdf_buffer = generer_pdf(
            st.session_state.data,
            st.session_state.checklist,
            st.session_state.equipes,
            st.session_state.events
        )

        st.download_button(
            label="Télécharger le rapport PDF",
            data=pdf_buffer,
            file_name=f"rapport_suivi_blindage_SAG_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Pour activer le rapport PDF, installe reportlab avec : pip install reportlab")


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.markdown(
    f"""
<div class="footer-text">
Développée par : {DEVELOPPEUR} | Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}
</div>
""",
    unsafe_allow_html=True
)
