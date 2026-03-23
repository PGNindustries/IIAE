import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from fpdf import FPDF
import os, json, csv, datetime
from io import BytesIO

# ==========================================
# 1. CONFIGURACIÓN Y ESTILOS
# ==========================================

st.set_page_config(
    page_title="IIAE Biobardas · TFG",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help":     "mailto:pedro@biobardas.org",
        "Report a bug": "https://github.com/PGNindu/IIAE",
        "About":        "**IIAE Biobardas** · TFG · 2026\n\n"
                        "Desarrollado por Pedro Juan García Navarro.\n"
                        "Universidad Miguel Hernández de Elche (Ingeniería Eléctrica)\n"
                        "en colaboración con la Universidad de Montevideo.\n"
                        "Sistema de cuantificación del Índice de Impacto Ambiental Evitado."
    }
)

# --- COLORES CORPORATIVOS ---
COLOR_PRIMARY  = '#17574A'
COLOR_ACCENT   = '#47d7ac'
COLOR_BG       = '#F4F3EE'
COLOR_GRID     = '#dcdcc0'
COLOR_WARN     = '#e07b39'
COLOR_DANGER   = '#c0392b'

# --- TEMPLATE PLOTLY (corrección: ioRegistrar en pio) ---
import plotly.io as pio

custom_template = go.layout.Template()
custom_template.layout.plot_bgcolor  = '#FAFAF7'
custom_template.layout.paper_bgcolor = '#F8F6F0'
custom_template.layout.font          = dict(color="#1C1C1C", family="DM Sans, Arial, sans-serif")
custom_template.layout.xaxis        = dict(gridcolor=COLOR_GRID, zeroline=False, showgrid=True)
custom_template.layout.yaxis        = dict(gridcolor=COLOR_GRID, zeroline=False, showgrid=True)
custom_template.layout.legend       = dict(bgcolor='rgba(255,255,255,0.5)', bordercolor=COLOR_GRID)
custom_template.layout.margin       = dict(t=50, b=40, l=40, r=40)

pio.templates["biobardas"] = custom_template
pio.templates.default      = "biobardas"

# --- CSS PROFESIONAL DEFINITIVO ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;1,9..144,300;1,9..144,400&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap');

/* BASE */
*, *::before, *::after {{ box-sizing: border-box; }}
html, body, .stApp {{
    background: #EDEAE0 !important;
    font-family: 'DM Sans', sans-serif;
    color: #1C1C1C;
    -webkit-font-smoothing: antialiased;
}}

/* AREA PRINCIPAL */
.block-container {{
    background: #F8F6F0;
    border-radius: 24px;
    padding: 3rem 3rem 3.5rem;
    box-shadow: 0 0 0 1px rgba(23,87,74,0.06), 0 4px 6px rgba(0,0,0,0.04), 0 20px 48px rgba(23,87,74,0.07);
    margin-top: 20px;
    max-width: 1180px;
}}

/* TIPOGRAFIA */
h1 {{
    font-family: 'Fraunces', serif !important;
    color: {COLOR_PRIMARY} !important;
    font-size: 2.3rem !important;
    font-weight: 400 !important;
    font-style: italic !important;
    letter-spacing: -1px !important;
    line-height: 1.15 !important;
    margin-bottom: 0.2rem !important;
}}
h2 {{
    font-family: 'DM Sans', sans-serif !important;
    color: {COLOR_PRIMARY} !important;
    font-size: 1.2rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
}}
h3 {{
    font-family: 'DM Sans', sans-serif !important;
    color: {COLOR_PRIMARY} !important;
    font-weight: 600 !important;
    font-size: 1.02rem !important;
}}
h4, h5 {{
    color: {COLOR_PRIMARY} !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
}}

/* SIDEBAR */
[data-testid="stSidebar"] {{
    background: #0D3529 !important;
    border-right: none !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    background: #0D3529 !important;
}}
[data-testid="stSidebar"] .block-container {{
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
    border-radius: 0 !important;
}}

/* Botones navegacion sidebar — sin bordes, sin cambio de fondo */
[data-testid="stSidebar"] button {{
    width: 100% !important;
    background: transparent !important;
    color: rgba(255,255,255,0.52) !important;
    text-align: left !important;
    padding: 10px 22px !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.1px !important;
    transition: color 0.15s ease !important;
    margin: 0 !important;
}}
[data-testid="stSidebar"] button:hover {{
    background: transparent !important;
    color: rgba(255,255,255,0.85) !important;
    border: none !important;
    box-shadow: none !important;
}}
[data-testid="stSidebar"] button[kind="primary"] {{
    background: transparent !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    box-shadow: none !important;
}}
[data-testid="stSidebar"] button[kind="secondary"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}}

/* TARJETAS METRICAS */
.metric-card {{
    background: #FFFFFF;
    border-radius: 16px;
    padding: 22px 18px 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 4px 14px rgba(0,0,0,0.04);
    text-align: center;
    margin-bottom: 12px;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    position: relative;
    overflow: hidden;
}}
.metric-card::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: {COLOR_PRIMARY};
}}
.metric-card.accent::after {{ background: {COLOR_ACCENT}; }}
.metric-card.warn::after   {{ background: {COLOR_WARN}; }}
.metric-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 32px rgba(23,87,74,0.13);
}}
.metric-value {{
    font-family: 'Fraunces', serif;
    font-size: 2rem;
    font-weight: 300;
    color: {COLOR_PRIMARY};
    margin: 4px 0 0;
    line-height: 1.05;
    letter-spacing: -1px;
}}
.metric-label {{
    font-size: 0.7rem;
    color: #AAA;
    margin-top: 7px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.9px;
    font-family: 'DM Sans', sans-serif;
}}
.metric-icon {{
    font-size: 1.1em;
    margin-bottom: 2px;
    opacity: 0.65;
    display: block;
}}

/* TABLAS */
.stDataFrame {{
    border: 1px solid #E5E2D8 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}}
[data-testid="stDataFrame"] thead th {{
    background: #EFECE4 !important;
    color: {COLOR_PRIMARY} !important;
    font-weight: 600 !important;
    font-size: 0.71rem !important;
    letter-spacing: 0.8px !important;
    text-transform: uppercase !important;
    padding: 10px 14px !important;
    border-bottom: 1px solid #DDD8CC !important;
    font-family: 'DM Sans', sans-serif !important;
}}
[data-testid="stDataFrame"] tbody tr:hover > div {{
    background: rgba(71,215,172,0.05) !important;
}}

/* FORMULARIOS — Labels */
.stNumberInput label, .stTextInput label, .stTextArea label,
.stSelectbox label, .stDateInput label, .stTimeInput label {{
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    color: #888 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.7px !important;
    font-family: 'DM Sans', sans-serif !important;
}}

/* FORMULARIOS — Inputs */
.stNumberInput input, .stTextInput input, .stTextArea textarea {{
    border-radius: 8px !important;
    border: 1.5px solid #DDD8CC !important;
    font-family: 'DM Sans', sans-serif !important;
    background: #FFFFFF !important;
    color: #1C1C1C !important;
    font-size: 0.88rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}}
.stNumberInput input:focus, .stTextInput input:focus, .stTextArea textarea:focus {{
    border-color: {COLOR_PRIMARY} !important;
    box-shadow: 0 0 0 3px rgba(23,87,74,0.08) !important;
    outline: none !important;
}}

/* BOTONES */
button[kind="primary"] {{
    background: {COLOR_PRIMARY} !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.87rem !important;
    letter-spacing: 0.2px !important;
    transition: all 0.18s ease !important;
    border: none !important;
}}
button[kind="primary"]:hover {{
    background: #0B2820 !important;
    box-shadow: 0 5px 22px rgba(23,87,74,0.3) !important;
    transform: translateY(-1px) !important;
}}
button[kind="secondary"] {{
    border-radius: 9px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.84rem !important;
    border: 1.5px solid #DDD8CC !important;
    color: #666 !important;
    background: white !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
}}
button[kind="secondary"]:hover {{
    border-color: {COLOR_PRIMARY} !important;
    color: {COLOR_PRIMARY} !important;
    background: rgba(23,87,74,0.03) !important;
}}

/* EXPANDERS */
details {{
    border-radius: 12px !important;
    border: 1.5px solid #E5E2D8 !important;
    background: #FFFFFF !important;
    padding: 0 8px !important;
    margin-bottom: 6px !important;
    transition: box-shadow 0.15s !important;
}}
details[open] {{
    box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
}}
details summary {{
    font-weight: 600 !important;
    color: {COLOR_PRIMARY} !important;
    font-size: 0.87rem !important;
    padding: 12px 6px !important;
    letter-spacing: 0.1px !important;
    font-family: 'DM Sans', sans-serif !important;
    cursor: pointer;
}}

/* TABS */
[data-testid="stTabs"] {{
    border-bottom: 1px solid #E5E2D8 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.84rem !important;
    color: #AAA !important;
    padding: 10px 18px !important;
    transition: color 0.15s !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: {COLOR_PRIMARY} !important;
    font-weight: 700 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    background: {COLOR_PRIMARY} !important;
    height: 2px !important;
}}

/* SELECTBOX */
[data-testid="stSelectbox"] > div > div {{
    border-radius: 8px !important;
    border: 1.5px solid #DDD8CC !important;
    background: #FFFFFF !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.88rem !important;
}}

/* ALERTAS */
.stAlert {{
    border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.87rem !important;
    border: none !important;
}}

/* SEPARADORES */
hr {{
    border: none !important;
    border-top: 1px solid #E5E2D8 !important;
    margin: 28px 0 !important;
}}

/* PROGRESS BAR */
.stProgress > div > div {{
    background: {COLOR_PRIMARY} !important;
    border-radius: 4px !important;
}}

/* SECCION CHIP — etiqueta decorativa */
.section-chip {{
    display: inline-block;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: {COLOR_PRIMARY};
    background: rgba(23,87,74,0.08);
    border-radius: 20px;
    padding: 3px 10px;
    margin-bottom: 8px;
    font-family: 'DM Sans', sans-serif;
}}

/* WATERMARK */
.watermark-autoria {{
    position: fixed;
    bottom: 14px; right: 18px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.67rem;
    color: rgba(23,87,74,0.28);
    letter-spacing: 0.3px;
    pointer-events: none;
    z-index: 9999;
    text-align: right;
    line-height: 1.6;
}}

footer {{ visibility: hidden; }}
#MainMenu {{ visibility: hidden; }}
[data-testid="stDecoration"] {{ display: none; }}

/* SIDEBAR TOGGLE BUTTON — siempre visible y bien estilizado */
[data-testid="stSidebarCollapsedControl"] {{
    background: #0D3529 !important;
    border-radius: 0 12px 12px 0 !important;
    width: 28px !important;
    top: 50% !important;
    transform: translateY(-50%) !important;
    box-shadow: 3px 0 12px rgba(0,0,0,0.18) !important;
    border: none !important;
    opacity: 1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    z-index: 999 !important;
    transition: background 0.2s ease !important;
}}
[data-testid="stSidebarCollapsedControl"]:hover {{
    background: #195c47 !important;
    width: 32px !important;
}}
[data-testid="stSidebarCollapsedControl"] button {{
    color: #47d7ac !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    width: 100% !important;
    height: 100% !important;
    font-size: 1rem !important;
}}
[data-testid="stSidebarCollapsedControl"] svg {{
    fill: #47d7ac !important;
    stroke: #47d7ac !important;
    width: 14px !important;
    height: 14px !important;
}}

/* Flecha dentro del sidebar (collapse button) — siempre visible */
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] {{
    background: transparent !important;
    border-radius: 8px !important;
    color: #47d7ac !important;
    transition: all 0.15s !important;
    border: none !important;
    box-shadow: none !important;
}}
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"]:hover {{
    background: rgba(71,215,172,0.12) !important;
    color: #47d7ac !important;
}}
[data-testid="stSidebar"] [data-testid="stBaseButton-headerNoPadding"] svg {{
    fill: #47d7ac !important;
    stroke: #47d7ac !important;
    color: #47d7ac !important;
    opacity: 1 !important;
}}

/* Todos los SVG del sidebar en color claro visible */
[data-testid="stSidebar"] svg {{
    fill: #47d7ac !important;
    stroke: #47d7ac !important;
    opacity: 0.85 !important;
}}

</style>
""", unsafe_allow_html=True)

# Watermark de autoria fijo
st.markdown("""
<div class="watermark-autoria">
    Pedro Juan García Navarro &middot; UMH Elche · Univ. de Montevideo<br>
    &copy; 2026 &middot; Todos los derechos reservados
</div>
""", unsafe_allow_html=True)


# ==========================================
# 2. CONSTANTES Y DATOS
# ==========================================

PLASTIC_FILE      = "data_plasticos.json"
HIST_FILE         = "historial_recolecciones.csv"
BOTELLA_PET_KG    = 0.025
COEF_FAUNA        = 0.03
HIST_COLUMNS      = ["Fecha", "Ubicación", "Operador", "Notas", "Tipos", "Cantidades (kg)", "Impacto total", "Fauna afectada"]

# Índices IIAE según la fórmula oficial del TFG:
# IIAE = (PMA·0.30) + (PMI·0.25) + (PRE·0.30) + (PPA·0.15)
# Fuente: "Índice de Impacto Ambiental Evitado – Biobardas / UMH Elche & Univ. de Montevideo"
DEF_PLASTICS = {
    'EPS':  {"indice": 3.95, "vida": 50,   "pma": 4.00, "pmi": 5.00, "pre": 4.25, "ppa": 1.50},
    'PP':   {"indice": 3.83, "vida": 80,   "pma": 4.58, "pmi": 4.88, "pre": 3.00, "ppa": 2.25},
    'LDPE': {"indice": 3.75, "vida": 100,  "pma": 4.92, "pmi": 3.25, "pre": 3.50, "ppa": 2.75},
    'PS':   {"indice": 3.05, "vida": 50,   "pma": 2.25, "pmi": 3.50, "pre": 4.25, "ppa": 1.50},
    'HDPE': {"indice": 2.99, "vida": 800,  "pma": 3.00, "pmi": 3.25, "pre": 2.25, "ppa": 4.00},
    'PVC':  {"indice": 2.32, "vida": 2500, "pma": 1.16, "pmi": 1.00, "pre": 3.25, "ppa": 5.00},
    'PET':  {"indice": 1.11, "vida": 20,   "pma": 1.25, "pmi": 1.13, "pre": 1.00, "ppa": 1.00},
}

COLOR_SEQ = [COLOR_PRIMARY, COLOR_ACCENT, '#a8d5b0', '#e7e7c0', '#f5c06a', '#a0a080', '#c9eac6']


# ==========================================
# 3. UTILIDADES Y LÓGICA
# ==========================================

def load_plastics() -> dict:
    """Carga plásticos con migración automática de índices desactualizados.
    Si el JSON contiene los valores pre-TFG, los reemplaza con los del PDF.
    """
    INDICES_OBSOLETOS = {
        'EPS': 4.14, 'PP': 3.92, 'PS': 3.16,
        'LDPE': 3.12, 'HDPE': 2.37, 'PET': 1.42,
    }
    if os.path.exists(PLASTIC_FILE):
        try:
            with open(PLASTIC_FILE, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict) and data:
                migrated = False
                for mat, old_idx in INDICES_OBSOLETOS.items():
                    if mat in data and abs(data[mat].get("indice", 0) - old_idx) < 0.01:
                        data[mat] = DEF_PLASTICS[mat].copy()
                        migrated = True
                if migrated:
                    with open(PLASTIC_FILE, 'w') as f:
                        json.dump(data, f, indent=2)
                return data
        except (json.JSONDecodeError, IOError):
            pass
    return DEF_PLASTICS.copy()


def save_plastics(data: dict) -> None:
    try:
        with open(PLASTIC_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        st.error(f"Error al guardar plásticos: {e}")


def parse_list_string(s: str) -> list[float]:
    """Parsea strings tipo '[1.0, 2.5]' o '1.0, 2.5' a lista de floats."""
    clean = str(s).replace('[', '').replace(']', '').strip()
    if not clean:
        return []
    try:
        return [float(x.strip()) for x in clean.split(',') if x.strip()]
    except ValueError:
        return []


def load_historial() -> pd.DataFrame:
    """Carga historial CSV. Compatible con formato antiguo (5 cols) y nuevo (8 cols).
    
    Formato antiguo: Fecha | Tipos | Cantidades (kg) | Impacto total | Fauna afectada
    Formato nuevo:   Fecha | Ubicación | Operador | Notas | Tipos | Cantidades (kg) | Impacto total | Fauna afectada
    
    La detección usa csv.reader para contar campos reales (maneja comas dentro de campos).
    """
    OLD_COLUMNS = ["Fecha", "Tipos", "Cantidades (kg)", "Impacto total", "Fauna afectada"]
    
    if not os.path.exists(HIST_FILE) or os.path.getsize(HIST_FILE) == 0:
        return pd.DataFrame(columns=HIST_COLUMNS)
    try:
        # Contar columnas reales de la primera fila con csv.reader (respeta comillas)
        import csv as _csv
        with open(HIST_FILE, 'r', newline='') as f:
            reader = _csv.reader(f)
            first_row = next(reader, [])
        ncols = len(first_row)
        
        is_new_format = (ncols >= 8)
        
        if is_new_format:
            hist = pd.read_csv(HIST_FILE, header=None, names=HIST_COLUMNS)
        else:
            # Formato antiguo: leer con 5 columnas y añadir las nuevas vacías
            hist = pd.read_csv(HIST_FILE, header=None, names=OLD_COLUMNS)
            hist.insert(1, "Ubicación", "")
            hist.insert(2, "Operador",  "")
            hist.insert(3, "Notas",     "")
        
        hist["Fecha"]         = pd.to_datetime(hist["Fecha"], errors='coerce')
        hist["Impacto total"] = pd.to_numeric(hist["Impacto total"], errors='coerce').fillna(0)
        hist["Fauna afectada"]= pd.to_numeric(hist["Fauna afectada"], errors='coerce').fillna(0)
        hist = hist.dropna(subset=["Fecha"])
        hist = hist[HIST_COLUMNS]
        return hist
    except Exception as e:
        st.warning(f"Aviso al leer historial: {e}")
        return pd.DataFrame(columns=HIST_COLUMNS)


def save_historial(fecha: str, tipos: list, cantidades: list, total: float, fauna: float,
                   ubicacion: str = "", operador: str = "", notas: str = "") -> None:
    try:
        with open(HIST_FILE, 'a', newline='') as f:
            csv.writer(f).writerow([
                fecha, ubicacion, operador, notas,
                ", ".join(tipos), ", ".join(map(str, cantidades)), total, fauna
            ])
    except IOError as e:
        st.error(f"Error al guardar historial: {e}")


def calcular_iiae(kg: float, datos: dict) -> dict:
    """Calcula métricas IIAE para un plástico dado."""
    impacto = kg * datos["indice"]
    return {
        "Impacto total":       impacto,
        "Fauna afectada":      impacto * COEF_FAUNA,
        "Persistencia (años)": datos["vida"],
        "Impacto·Persistencia": kg * datos["vida"],
    }


def calc_total_persistence(hist_df: pd.DataFrame, plastics: dict) -> float:
    """Calcula años de persistencia acumulados usando sólo plastics (ya incluye defaults fusionados)."""
    total = 0.0
    if hist_df.empty:
        return total
    for _, row in hist_df.iterrows():
        kgs  = parse_list_string(row["Cantidades (kg)"])
        typs = [t.strip() for t in str(row["Tipos"]).split(",")]
        if len(kgs) != len(typs):
            continue
        for t, k in zip(typs, kgs):
            vida = plastics.get(t, {}).get('vida', 10)
            total += k * vida
    return total


def metric_card(label: str, value: str, icon: str = "", variant: str = "") -> str:
    cls = f"metric-card {variant}".strip()
    icon_html = f'<div class="metric-icon">{icon}</div>' if icon else ""
    return f"""
    <div class="{cls}">
        {icon_html}
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>"""


def try_write_image(fig, path: str) -> bool:
    """Intenta guardar figura como imagen. Retorna True si tuvo éxito."""
    try:
        fig.write_image(path)
        return True
    except Exception:
        return False


def crear_pdf(df: pd.DataFrame, total: float, fauna: float, kg_total: float,
              autor: str = "Equipo Biobardas", fecha_hora: str = "",
              ubicacion: str = "", notas: str = "") -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # Encabezado
    pdf.set_fill_color(23, 87, 74)
    pdf.rect(0, 0, 210, 30, 'F')
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(0, 8)
    pdf.cell(210, 14, 'Informe Ambiental IIAE - Biobardas', align='C', ln=1)

    pdf.set_xy(10, 35)
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(65, 81, 49)
    fecha_str = fecha_hora if fecha_hora else datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 8, f'Fecha y hora: {fecha_str}   |   Operador: {autor}', ln=1)
    if ubicacion:
        pdf.cell(0, 8, f'Ubicacion: {ubicacion}', ln=1)
    if notas:
        pdf.set_font('Arial', 'I', 10)
        pdf.multi_cell(0, 7, f'Notas: {notas}')
        pdf.set_font('Arial', '', 11)
    pdf.ln(4)

    # KPIs
    pdf.set_font('Arial', 'B', 13)
    pdf.set_text_color(23, 87, 74)
    kpis = [
        ("Impacto IIAE Total",   f"{total:.2f}",       (201, 234, 198)),
        ("Peso Total Recogido",  f"{kg_total:.2f} kg", (231, 231, 192)),
        ("Fauna Protegida (est.)", f"{fauna:.1f}",     (196, 226, 255)),
        ("Botellas equiv. PET",  f"{int(kg_total/BOTELLA_PET_KG):,}", (255, 235, 196)),
    ]
    for label, val, fill in kpis:
        pdf.set_fill_color(*fill)
        pdf.cell(95, 12, label, border=1, fill=True)
        pdf.cell(95, 12, val, border=1, fill=True, ln=1)
    pdf.ln(8)

    # Tabla detalle
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(231, 231, 192)
    pdf.set_text_color(23, 87, 74)
    headers = ['Plástico', 'Kg', 'IIAE', 'Fauna', 'Vida (años)']
    widths  = [38, 28, 30, 28, 32]
    for h, w in zip(headers, widths):
        pdf.cell(w, 10, h, border=1, fill=True)
    pdf.ln()

    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(40, 40, 40)
    for _, row in df.iterrows():
        pdf.cell(widths[0], 9, str(row['Plástico']), 1)
        pdf.cell(widths[1], 9, f"{row['Kg recogidos']:.2f}", 1)
        pdf.cell(widths[2], 9, f"{row['Impacto total']:.2f}", 1)
        pdf.cell(widths[3], 9, f"{row['Fauna afectada']:.2f}", 1)
        pdf.cell(widths[4], 9, str(row['Persistencia (años)']), 1, ln=1)

    # Gráficos si existen
    for img_path in ["bar_impacto.png", "radar_impacto.png"]:
        if os.path.exists(img_path):
            pdf.ln(6)
            pdf.image(img_path, w=170)

    return pdf.output(dest='S').encode('latin-1')


# ==========================================
# 4. NAVEGACIÓN
# ==========================================

PAGINAS = {
    "🏠 Inicio":              "Inicio",
    "📊 Análisis Ambiental":  "Análisis Ambiental",
    "📈 Panel de Resultados": "Panel de Resultados",
    "⚡ Valorización Energética": "Valorización Energética",
    "🧮 Modelo de Cálculo":   "Modelo de Cálculo",
}

with st.sidebar:
    # ── Logo y título ──
    st.markdown(f"""
<div style='padding:28px 20px 18px;border-bottom:1px solid rgba(255,255,255,0.1);margin-bottom:4px;'>
  <div style='display:flex;align-items:center;gap:11px;'>
    <div style='width:34px;height:34px;background:rgba(255,255,255,0.12);border-radius:9px;
                display:flex;align-items:center;justify-content:center;font-size:1.2em;flex-shrink:0;'>🌿</div>
    <div>
      <div style='font-family:"Fraunces",serif;color:white;font-size:1.08rem;
                  line-height:1.15;font-weight:400;font-style:italic;'>IIAE Biobardas</div>
      <div style='font-size:0.62rem;color:rgba(255,255,255,0.42);letter-spacing:0.9px;
                  text-transform:uppercase;margin-top:2px;'>Sistema de Gestión Ambiental</div>
    </div>
  </div>
</div>
    """, unsafe_allow_html=True)

    if "page" not in st.session_state:
        st.session_state["page"] = "Inicio"

    st.markdown("<div style='padding:8px 0 0;'>", unsafe_allow_html=True)
    for label, key in PAGINAS.items():
        is_active = st.session_state["page"] == key
        btn_type  = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state["page"] = key
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Autor — al final del flujo normal, sin position:absolute ──
    st.markdown(f"""
<div style='padding:20px 20px 16px;border-top:1px solid rgba(255,255,255,0.08);margin-top:16px;'>
  <div style='font-size:0.67rem;color:rgba(255,255,255,0.35);line-height:1.8;'>
    <div style='font-weight:600;color:rgba(255,255,255,0.55);font-size:0.7rem;
                margin-bottom:1px;'>Pedro Juan García Navarro</div>
    <div>Ingeniería Eléctrica · UMH Elche &amp; Univ. Montevideo</div>
    <div style='margin-top:3px;color:rgba(255,255,255,0.2);letter-spacing:0.2px;'>v3.0 · {datetime.date.today().year}</div>
  </div>
</div>
    """, unsafe_allow_html=True)

selec = st.session_state["page"]

# ==========================================
# MODAL DE BIENVENIDA — TUTORIAL
# ==========================================
import streamlit.components.v1 as components

if "tutorial_seen" not in st.session_state:
    st.session_state["tutorial_seen"] = False

with st.sidebar:
    st.markdown("<div style='padding:0 12px 8px;'>", unsafe_allow_html=True)
    if st.button("❓ Tutorial de uso", key="btn_tutorial_open", use_container_width=True):
        st.session_state["tutorial_seen"] = False
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.get("tutorial_seen", False):

    TUTORIAL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@1,9..144,400&family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #F8F6F0; font-family: 'DM Sans', sans-serif; padding: 0; }
.modal { background: #F8F6F0; border-radius: 16px; overflow: hidden; }
.head { background: #0D3529; padding: 26px 32px 22px; display: flex; align-items: center; justify-content: space-between; }
.head-title { font-family: 'Fraunces', serif; font-size: 1.55rem; font-weight: 400; font-style: italic; color: white; margin-bottom: 3px; }
.head-sub { font-size: 0.77rem; color: rgba(255,255,255,0.45); letter-spacing: 0.3px; }
.badge { background: rgba(71,215,172,0.15); border: 1px solid rgba(71,215,172,0.3); color: #47d7ac; font-size: 0.67rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; padding: 4px 12px; border-radius: 20px; }
.body { padding: 24px 32px 28px; }
.intro { font-size: 0.89rem; color: #555; line-height: 1.7; margin-bottom: 20px; padding-bottom: 18px; border-bottom: 1px solid #E5E2D8; }
.flow-box { background: white; border-radius: 10px; padding: 14px 20px; border: 1px solid #E8E5DC; margin-bottom: 18px; }
.flow-label { font-size: 0.67rem; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; color: #17574A; margin-bottom: 10px; opacity: 0.7; }
.flow { display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }
.flow-step { background: #F0EDE3; border-radius: 7px; padding: 6px 13px; font-size: 0.78rem; font-weight: 600; color: #17574A; }
.flow-arr { color: #47d7ac; font-size: 1rem; font-weight: 700; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.card { background: white; border-radius: 11px; padding: 16px; border: 1px solid #E8E5DC; }
.card-hd { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.ico { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1rem; flex-shrink: 0; }
.card-name { font-weight: 700; font-size: 0.86rem; color: #17574A; }
.card-tag { font-size: 0.65rem; font-weight: 600; letter-spacing: 0.7px; text-transform: uppercase; color: #bbb; margin-top: 1px; }
.card-desc { font-size: 0.8rem; color: #555; line-height: 1.6; margin-bottom: 9px; }
.steps { display: flex; flex-direction: column; gap: 5px; }
.step { display: flex; align-items: flex-start; gap: 7px; font-size: 0.78rem; color: #444; line-height: 1.5; }
.num { min-width: 18px; height: 18px; background: #17574A; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.6rem; font-weight: 700; flex-shrink: 0; margin-top: 1px; }
.formula { background: #0D3529; border-radius: 7px; padding: 10px 13px; margin-top: 9px; font-size: 0.78rem; color: #47d7ac; line-height: 1.6; }
.tip { background: rgba(71,215,172,0.07); border-left: 3px solid #47d7ac; border-radius: 0 6px 6px 0; padding: 8px 11px; font-size: 0.78rem; color: #2a6b5a; margin-top: 8px; line-height: 1.5; }
.warn { background: rgba(224,123,57,0.07); border-left: 3px solid #e07b39; border-radius: 0 6px 6px 0; padding: 8px 11px; font-size: 0.78rem; color: #7a4a1a; margin-top: 8px; line-height: 1.5; }
.foot { border-top: 1px solid #E5E2D8; padding-top: 14px; font-size: 0.75rem; color: #aaa; }
code { background: #F0EDE3; padding: 1px 5px; border-radius: 4px; font-size: 0.75rem; color: #17574A; }
</style>
</head>
<body>
<div class="modal">
  <div class="head">
    <div>
      <div class="head-title">Bienvenido a IIAE Biobardas</div>
      <div class="head-sub">Guía de uso · Sistema de Gestión Ambiental</div>
    </div>
    <div class="badge">Tutorial</div>
  </div>
  <div class="body">

    <div class="intro">
      Esta aplicación te permite <strong>cuantificar el impacto ambiental evitado</strong> en recogidas de plástico de ríos mediante el <em>Índice de Impacto Ambiental Evitado (IIAE)</em>. Aquí tienes un resumen de cada sección y cómo usarla.
    </div>

    <div class="flow-box">
      <div class="flow-label">Flujo de trabajo recomendado</div>
      <div class="flow">
        <div class="flow-step">📊 Registrar recogida</div>
        <div class="flow-arr">→</div>
        <div class="flow-step">📈 Ver resultados</div>
        <div class="flow-arr">→</div>
        <div class="flow-step">👣 Calcular CO₂</div>
        <div class="flow-arr">→</div>
        <div class="flow-step">📄 Exportar PDF</div>
      </div>
    </div>

    <div class="grid">

      <div class="card">
        <div class="card-hd">
          <div class="ico" style="background:rgba(23,87,74,0.09)">📊</div>
          <div><div class="card-name">Análisis Ambiental</div><div class="card-tag">Registro de recogidas</div></div>
        </div>
        <div class="card-desc">Introduce los kg recogidos de cada polímero y calcula el IIAE al instante. Cada campaña queda registrada automáticamente.</div>
        <div class="steps">
          <div class="step"><div class="num">1</div><span>Rellena fecha, hora y ubicación del tramo</span></div>
          <div class="step"><div class="num">2</div><span>Introduce los kg de cada plástico recogido</span></div>
          <div class="step"><div class="num">3</div><span>Pulsa <strong>Calcular Impacto</strong> para ver resultados</span></div>
          <div class="step"><div class="num">4</div><span>Descarga el informe PDF si lo necesitas</span></div>
        </div>
        <div class="formula">IIAE = (P_MA · 0.30) + (P_MI · 0.25)<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;+ (P_RE · 0.30) + (P_PA · 0.15)</div>
      </div>

      <div class="card">
        <div class="card-hd">
          <div class="ico" style="background:rgba(71,215,172,0.12)">📈</div>
          <div><div class="card-name">Panel de Resultados</div><div class="card-tag">Dashboard histórico</div></div>
        </div>
        <div class="card-desc">Visualiza la evolución acumulada de todas las campañas: impacto, fauna protegida, tendencias y análisis por polímero.</div>
        <div class="steps">
          <div class="step"><div class="num">1</div><span><strong>Mensual:</strong> impacto IIAE mes a mes</span></div>
          <div class="step"><div class="num">2</div><span><strong>Acumulado:</strong> curva de impacto total creciente</span></div>
          <div class="step"><div class="num">3</div><span><strong>Historial:</strong> tabla con hora, ubicación y notas</span></div>
          <div class="step"><div class="num">4</div><span><strong>Peligrosidad:</strong> ranking de riesgo por polímero</span></div>
        </div>
        <div class="tip">💡 El botón <strong>Exportar CSV</strong> descarga todo el historial para análisis externo.</div>
      </div>

      <div class="card">
        <div class="card-hd">
          <div class="ico" style="background:rgba(224,123,57,0.10)">👣</div>
          <div><div class="card-name">Valorización Energética</div><div class="card-tag">Waste-to-Energy</div></div>
        </div>
        <div class="card-desc">Calcula la energía eléctrica recuperable mediante valorización térmica directa (Waste-to-Energy) del plástico interceptado.</div>
        <div class="steps">
          <div class="step"><div class="num">1</div><span>Los datos se toman automáticamente de la última campaña calculada</span></div>
          <div class="step"><div class="num">2</div><span>Consulta la energía generada por polímero y el total</span></div>
          <div class="step"><div class="num">3</div><span>Compara la energía con equivalencias reales (hogares, km...)</span></div>
        </div>
        <div class="tip">💡 Basado en los PCI de la base de datos Phyllis2/TNO y en la metodología del TFG (§2.8).</div>
      </div>

      <div class="card">
        <div class="card-hd">
          <div class="ico" style="background:rgba(74,144,226,0.10)">🧮</div>
          <div><div class="card-name">Modelo de Cálculo</div><div class="card-tag">Base científica</div></div>
        </div>
        <div class="card-desc">Consulta la metodología completa: fórmula, pesos de criterios, tabla de polímeros y simulador interactivo.</div>
        <div class="steps">
          <div class="step"><div class="num">1</div><span><strong>Fórmula IIAE:</strong> criterios y referencias científicas</span></div>
          <div class="step"><div class="num">2</div><span><strong>Criterios:</strong> P_MA, P_MI, P_RE, P_PA con sus pesos</span></div>
          <div class="step"><div class="num">3</div><span><strong>Polímeros:</strong> ranking completo de 7 materiales</span></div>
          <div class="step"><div class="num">4</div><span><strong>Simulador:</strong> desglose visual por material</span></div>
        </div>
      </div>

      <div class="card">
        <div class="card-hd">
          <div class="ico" style="background:rgba(139,92,246,0.10)">⚙️</div>
          <div><div class="card-name">Gestión de Índices</div><div class="card-tag">Personalización</div></div>
        </div>
        <div class="card-desc">En Análisis Ambiental, despliega el panel de gestión para añadir materiales, editar índices o restaurar los del TFG.</div>
        <div class="steps">
          <div class="step"><div class="num">1</div><span>Abre <strong>Gestión de Índices y Materiales</strong></span></div>
          <div class="step"><div class="num">2</div><span>Edita un material escribiendo su nombre exacto</span></div>
          <div class="step"><div class="num">3</div><span><strong>Restablecer</strong> vuelve a los valores del PDF del TFG</span></div>
        </div>
        <div class="tip">💡 Índices basados en el TFG — UMH Elche &amp; Universidad de Montevideo (2026).</div>
      </div>

      <div class="card">
        <div class="card-hd">
          <div class="ico" style="background:rgba(23,87,74,0.09)">💾</div>
          <div><div class="card-name">Datos y almacenamiento</div><div class="card-tag">Persistencia</div></div>
        </div>
        <div class="card-desc">Los datos se guardan en el servidor de Streamlit Cloud en dos archivos locales.</div>
        <div class="steps">
          <div class="step"><div class="num">📁</div><span><code>historial_recolecciones.csv</code> — campañas</span></div>
          <div class="step"><div class="num">📁</div><span><code>data_plasticos.json</code> — índices</span></div>
        </div>
        <div class="warn">⚠️ Streamlit puede reiniciar el servidor. Exporta el CSV regularmente.</div>
      </div>

    </div>

    <div class="foot">Puedes volver a ver este tutorial desde el botón <strong>❓ Tutorial de uso</strong> en el sidebar.</div>
  </div>
</div>
</body>
</html>"""

    components.html(TUTORIAL_HTML, height=900, scrolling=True)

    col_skip, col_start = st.columns([1, 1])
    with col_skip:
        if st.button("✖ Cerrar", key="tut_close", use_container_width=True, type="secondary"):
            st.session_state["tutorial_seen"] = True
            st.rerun()
    with col_start:
        if st.button("✅  ¡Entendido, empezar!", key="tut_start", use_container_width=True, type="primary"):
            st.session_state["tutorial_seen"] = True
            st.rerun()
    st.stop()


# ==========================================
# 5. PÁGINAS
# ==========================================

# ---- INICIO ----
if selec == "Inicio":
    col_txt, col_img = st.columns([1.6, 1])

    with col_txt:
        st.markdown(f"""
<div style='margin-bottom:6px;'>
  <span style='font-size:0.75rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase;
               color:{COLOR_ACCENT};font-family:"DM Sans",sans-serif;'>
    Sistema de Gestión Ambiental · TFG
  </span>
</div>
        """, unsafe_allow_html=True)
        st.markdown(f'<h1 style="font-family:Fraunces,serif;font-size:2.6rem;font-weight:400;font-style:italic;color:{COLOR_PRIMARY};letter-spacing:-1px;line-height:1.15;margin:4px 0 10px;">IIAE Biobardas</h1>', unsafe_allow_html=True)
        st.markdown(f"""
<p style='font-size:1.05rem;color:#555;margin-top:-10px;margin-bottom:24px;font-weight:400;
          font-family:"DM Sans",sans-serif;line-height:1.6;'>
  Cuantificación científica del beneficio ambiental de las labores de limpieza en ríos
  mediante el <em>Índice de Impacto Ambiental Evitado</em>.
</p>

<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:24px;'>
  <div style='background:#fff;border-radius:12px;padding:14px 16px;border:1px solid #eee;'>
    <div style='font-size:1.2em;margin-bottom:4px;'>📐</div>
    <div style='font-weight:600;font-size:0.88rem;color:{COLOR_PRIMARY};margin-bottom:3px;'>Calcula el IIAE</div>
    <div style='font-size:0.8rem;color:#777;'>Ponderado por material, peligrosidad y persistencia</div>
  </div>
  <div style='background:#fff;border-radius:12px;padding:14px 16px;border:1px solid #eee;'>
    <div style='font-size:1.2em;margin-bottom:4px;'>⚖️</div>
    <div style='font-weight:600;font-size:0.88rem;color:{COLOR_PRIMARY};margin-bottom:3px;'>Analiza la peligrosidad</div>
    <div style='font-size:0.8rem;color:#777;'>Más allá del peso: impacto real por polímero</div>
  </div>
  <div style='background:#fff;border-radius:12px;padding:14px 16px;border:1px solid #eee;'>
    <div style='font-size:1.2em;margin-bottom:4px;'>📈</div>
    <div style='font-weight:600;font-size:0.88rem;color:{COLOR_PRIMARY};margin-bottom:3px;'>Visualiza tendencias</div>
    <div style='font-size:0.8rem;color:#777;'>Historial acumulado y análisis temporal</div>
  </div>
  <div style='background:#fff;border-radius:12px;padding:14px 16px;border:1px solid #eee;'>
    <div style='font-size:1.2em;margin-bottom:4px;'>📄</div>
    <div style='font-weight:600;font-size:0.88rem;color:{COLOR_PRIMARY};margin-bottom:3px;'>Genera informes PDF</div>
    <div style='font-size:0.8rem;color:#777;'>Informes técnicos con datos y gráficas</div>
  </div>
</div>

<div style='background:#F0EFE9;border-radius:10px;padding:13px 16px;display:flex;
            align-items:center;gap:12px;border:1px solid #E0DED6;'>
  <div style='font-size:1.4em;'>🎓</div>
  <div>
    <div style='font-size:0.8rem;font-weight:600;color:{COLOR_PRIMARY};'>Pedro Juan García Navarro</div>
    <div style='font-size:0.75rem;color:#777;'>Trabajo de Fin de Grado · Ingeniería Eléctrica · UMH Elche &amp; Universidad de Montevideo · 2026</div>
  </div>
</div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Métricas rápidas del historial
        hist_home = load_historial()
        if not hist_home.empty:
            plastics_home = load_plastics()
            t_pers = calc_total_persistence(hist_home, plastics_home)
            h1, h2, h3 = st.columns(3)
            h1.markdown(metric_card("Campañas", str(len(hist_home)), "🎯"), unsafe_allow_html=True)
            h2.markdown(metric_card("IIAE Total", f"{hist_home['Impacto total'].sum():.1f}", "🌊"), unsafe_allow_html=True)
            h3.markdown(metric_card("Años Plástico Evitados", f"{t_pers:,.0f}", "⏳"), unsafe_allow_html=True)
        else:
            st.info("💡 Aún no hay datos. Empieza en **Análisis Ambiental**.")

    with col_img:
        if os.path.exists("dibujo_rio_biobarda.png"):
            st.image("dibujo_rio_biobarda.png", use_container_width=True)
        else:
            # Placeholder visual con identidad Biobardas (sin imagen)
            st.markdown(f"""
            <div style='background:linear-gradient(145deg,{COLOR_PRIMARY} 0%,#0f3d32 60%,{COLOR_ACCENT} 100%);
                        border-radius:20px;height:280px;display:flex;flex-direction:column;
                        align-items:center;justify-content:center;gap:10px;'>
              <svg width="90" height="90" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="48" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
                <path d="M20 65 Q30 45 40 55 Q50 65 60 45 Q70 25 80 45"
                      stroke="{COLOR_ACCENT}" stroke-width="3.5" fill="none" stroke-linecap="round"/>
                <path d="M20 75 Q30 55 40 65 Q50 75 60 55 Q70 35 80 55"
                      stroke="rgba(255,255,255,0.5)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
                <rect x="43" y="18" width="5" height="28" rx="2.5" fill="white" opacity="0.9"/>
                <path d="M48 22 L60 30 L48 38 Z" fill="{COLOR_ACCENT}"/>
              </svg>
              <p style='color:rgba(255,255,255,0.85);font-family:Montserrat,sans-serif;
                        font-size:0.85em;font-weight:600;letter-spacing:1px;margin:0;'>
                BIOBARDAS · RÍO DE LA PLATA
              </p>
            </div>
            """, unsafe_allow_html=True)


# ---- ANÁLISIS AMBIENTAL ----
elif selec == "Análisis Ambiental":
    plastics = load_plastics()
    st.markdown(f'''<h1 style="font-family:Fraunces,serif;font-size:2.2rem;font-weight:400;font-style:italic;color:{COLOR_PRIMARY};letter-spacing:-0.5px;margin-bottom:0.1rem;">Análisis de Recogida</h1>''', unsafe_allow_html=True)

    # ── Gestión de materiales ──
    with st.expander("⚙️ Gestión de Índices y Materiales"):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Materiales configurados:**")
            df_p = pd.DataFrame([
                {"Material": k, "Índice IIAE": v["indice"], "Vida (años)": v["vida"]}
                for k, v in plastics.items()
            ])
            st.dataframe(df_p, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("**Añadir o editar material:**")
            nn = st.text_input("Nombre del material")
            ni = st.number_input("Índice IIAE", min_value=0.1, max_value=15.0, value=2.0, step=0.01)
            nv = st.number_input("Vida media (años)", min_value=1, max_value=1000, value=50)

            col_add, col_reset = st.columns(2)
            if col_add.button("✅ Guardar", use_container_width=True, type="primary"):
                if nn.strip():
                    plastics[nn.strip().upper()] = {"indice": ni, "vida": nv}
                    save_plastics(plastics)
                    st.success(f"Material '{nn.upper()}' guardado.")
                    st.rerun()
                else:
                    st.warning("Introduce un nombre válido.")

            if col_reset.button("🔄 Restablecer", use_container_width=True):
                save_plastics(DEF_PLASTICS)
                st.success("Valores restablecidos.")
                st.rerun()

            # Eliminar material
            st.markdown("**Eliminar material:**")
            to_delete = st.selectbox("Selecciona", [""] + list(plastics.keys()))
            if st.button("🗑️ Eliminar", use_container_width=True) and to_delete:
                if to_delete in plastics:
                    del plastics[to_delete]
                    save_plastics(plastics)
                    st.success(f"'{to_delete}' eliminado.")
                    st.rerun()

    st.markdown("---")
    st.subheader("📋 Datos de la Campaña")

    with st.form("calc_form"):
        # ── Metadatos de la campaña ──
        m1, m2 = st.columns(2)
        with m1:
            camp_fecha = st.date_input("📅 Fecha de recogida", value=datetime.date.today())
            camp_hora  = st.time_input("🕐 Hora de inicio", value=datetime.time(9, 0), step=900)
            camp_ubi   = st.text_input("📍 Ubicación / Tramo del río", placeholder="Ej: Km 15, Margen derecha")
        with m2:
            camp_op    = st.text_input("👤 Operador / Equipo responsable", placeholder="Ej: Equipo A – Pedro García")
            camp_notas = st.text_area("📝 Notas de campo", placeholder="Condiciones, incidencias, observaciones...", height=110)

        st.markdown("---")
        st.subheader("📦 Pesos recogidos por material (kg)")

        p_keys  = list(plastics.keys())
        cols    = st.columns(min(4, len(p_keys)))
        cantidades = {}

        for i, p in enumerate(p_keys):
            idx   = plastics[p]
            label = f"{p}\n(IIAE: {idx['indice']})"
            cantidades[p] = cols[i % len(cols)].number_input(
                label, min_value=0.0, max_value=10000.0, step=0.5, format="%.2f"
            )

        st.markdown("<br>", unsafe_allow_html=True)
        btn_calc = st.form_submit_button("🧮 Calcular Impacto", use_container_width=True, type="primary")

    if btn_calc:
        activos = {p: kg for p, kg in cantidades.items() if kg > 0}
        if not activos:
            st.warning("⚠️ Introduce al menos una cantidad mayor a 0.")
        else:
            # Cálculo
            res = []
            for p, kg in activos.items():
                dat   = plastics[p]
                metr  = calcular_iiae(kg, dat)
                res.append({
                    "Plástico":           p,
                    "Kg recogidos":       kg,
                    "Índice IIAE":        dat["indice"],
                    **metr,
                })
            df = pd.DataFrame(res)

            tot_imp  = df["Impacto total"].sum()
            tot_fau  = df["Fauna afectada"].sum()
            kg_total = df["Kg recogidos"].sum()
            suma_pers = df["Impacto·Persistencia"].sum()

            # Guardar en session_state Y en historial
            st.session_state.update({
                'df': df, 'total': tot_imp, 'ftot': tot_fau, 'kgtot': kg_total
            })
            # Combinar fecha + hora en un solo timestamp
            fecha_hora = datetime.datetime.combine(camp_fecha, camp_hora).strftime("%d/%m/%Y %H:%M")
            fecha_iso  = datetime.datetime.combine(camp_fecha, camp_hora).isoformat(sep=' ')
            save_historial(
                fecha_iso,
                list(df["Plástico"]),
                list(df["Kg recogidos"]),
                tot_imp, tot_fau,
                ubicacion=camp_ubi,
                operador=camp_op,
                notas=camp_notas
            )
            # Guardar metadatos para el PDF
            st.session_state.update({
                'camp_op': camp_op, 'camp_ubi': camp_ubi,
                'camp_notas': camp_notas, 'camp_fecha_hora': fecha_hora
            })

            st.success("✅ Campaña registrada correctamente.")
            st.markdown("### 🏁 Resultados del Análisis")

            # Tarjetas KPI
            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(metric_card("Impacto Evitado (IIAE)", f"{tot_imp:.2f}", "🌿"), unsafe_allow_html=True)
            k2.markdown(metric_card("Peso Total",             f"{kg_total:.2f} kg", "⚖️"), unsafe_allow_html=True)
            k3.markdown(metric_card("Fauna Protegida (est.)", f"{tot_fau:.1f}", "🐟", "accent"), unsafe_allow_html=True)
            k4.markdown(metric_card("Botellas PET equiv.",    f"{int(kg_total/BOTELLA_PET_KG):,}", "♻️", "warn"), unsafe_allow_html=True)

            st.info(f"⚡ **{int(suma_pers):,} años** de persistencia plástica evitados en el ecosistema.")

            st.markdown("<br>", unsafe_allow_html=True)

            g1, g2 = st.columns(2)

            with g1:
                fig_bar = px.bar(
                    df, x='Plástico', y='Impacto total', color='Plástico',
                    title="Impacto IIAE por Material",
                    color_discrete_sequence=COLOR_SEQ,
                    text='Impacto total'
                )
                fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)
                try_write_image(fig_bar, "bar_impacto.png")

            with g2:
                if len(df) >= 2:
                    # Radar chart solo cuando hay 2+ plásticos
                    radar_df = df.copy()
                    cats     = ['Índice IIAE', 'Fauna afectada', 'Persistencia (años)']

                    # Normalización segura
                    for c in cats:
                        max_v = radar_df[c].max()
                        radar_df[c] = (radar_df[c] / max_v * 5) if max_v > 0 else 0

                    fig_rad = go.Figure()
                    for _, row in radar_df.iterrows():
                        fig_rad.add_trace(go.Scatterpolar(
                            r    = [row[c] for c in cats] + [row[cats[0]]],
                            theta = cats + [cats[0]],
                            fill  = 'toself',
                            name  = row['Plástico'],
                        ))
                    fig_rad.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                        title="Perfil de Riesgo Comparativo"
                    )
                    st.plotly_chart(fig_rad, use_container_width=True)
                    try_write_image(fig_rad, "radar_impacto.png")
                else:
                    # Con 1 plástico: mostrar gráfico de composición
                    row   = df.iloc[0]
                    fig_s = go.Figure(go.Indicator(
                        mode  = "gauge+number",
                        value = row["Impacto total"],
                        title = {'text': f"IIAE · {row['Plástico']}"},
                        gauge = {
                            'axis': {'range': [0, row["Impacto total"] * 1.5]},
                            'bar':  {'color': COLOR_PRIMARY},
                            'steps': [
                                {'range': [0, row["Impacto total"] * 0.5], 'color': '#c9eac6'},
                                {'range': [row["Impacto total"] * 0.5, row["Impacto total"]], 'color': COLOR_ACCENT},
                            ]
                        }
                    ))
                    st.plotly_chart(fig_s, use_container_width=True)

            with st.expander("📋 Ver Tabla Detallada"):
                st.dataframe(
                    df.style.format({
                        "Kg recogidos": "{:.2f}", "Índice IIAE": "{:.2f}",
                        "Impacto total": "{:.3f}", "Fauna afectada": "{:.3f}",
                        "Impacto·Persistencia": "{:.1f}"
                    }),
                    use_container_width=True, hide_index=True
                )

    # ── Descarga PDF (siempre visible si hay datos en session) ──
    if 'df' in st.session_state:
        st.markdown("---")
        pdf_bytes = crear_pdf(
            st.session_state['df'], st.session_state['total'],
            st.session_state['ftot'], st.session_state['kgtot'],
            autor    = st.session_state.get('camp_op', 'Equipo Biobardas'),
            fecha_hora = st.session_state.get('camp_fecha_hora', ''),
            ubicacion  = st.session_state.get('camp_ubi', ''),
            notas      = st.session_state.get('camp_notas', '')
        )
        st.download_button(
            "📥 Descargar Informe Oficial (PDF)",
            pdf_bytes,
            file_name=f"informe_iiae_{datetime.date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary"
        )


# ---- PANEL DE RESULTADOS ----
elif selec == "Panel de Resultados":
    plastics = load_plastics()
    st.markdown(f'''<h1 style="font-family:Fraunces,serif;font-size:2.2rem;font-weight:400;font-style:italic;color:{COLOR_PRIMARY};letter-spacing:-0.5px;margin-bottom:0.1rem;">Dashboard de Impacto</h1>''', unsafe_allow_html=True)

    # Controles superiores
    col_del, col_export, _ = st.columns([1, 1, 3])
    if col_del.button("⚠️ Borrar Historial", type="secondary"):
        if os.path.exists(HIST_FILE):
            os.remove(HIST_FILE)
            st.success("Historial borrado.")
            st.rerun()

    # Exportar historial como CSV descargable
    if os.path.exists(HIST_FILE):
        with open(HIST_FILE, 'rb') as f:
            col_export.download_button(
                "📥 Exportar CSV", f.read(),
                file_name=f"historial_iiae_{datetime.date.today()}.csv",
                mime="text/csv", use_container_width=True
            )

    hist = load_historial()

    if hist.empty:
        st.info("📭 No hay datos históricos. Registra tu primera campaña en 'Análisis Ambiental'.")
        st.stop()

    # Columna de kg: parsear cantidades de forma robusta
    def safe_kg_sum(s):
        vals = parse_list_string(s)
        return sum(v for v in vals if v > 0) if vals else 0.0

    hist["kgs"] = hist["Cantidades (kg)"].apply(safe_kg_sum)
    
    # Sanity check: si todos los kgs son 0 pero hay impacto, el CSV está mal parseado
    if hist["kgs"].sum() == 0 and hist["Impacto total"].sum() > 0:
        st.error("⚠️ **Problema con el formato del historial.** Los datos anteriores tienen un formato "
                 "incompatible con la versión actual. Por favor, borra el historial y registra "
                 "las campañas de nuevo con el formulario actualizado.")
        st.stop()

    # ── Métricas globales ──
    t_iiae  = hist["Impacto total"].sum()
    t_kg    = hist["kgs"].sum()
    t_fauna = hist["Fauna afectada"].sum()
    t_pers  = calc_total_persistence(hist, plastics)

    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(metric_card("IIAE Acumulado",     f"{t_iiae:,.2f}", "🌿"), unsafe_allow_html=True)
    m2.markdown(metric_card("Fauna (estimada)",   f"{t_fauna:,.0f}", "🐟", "accent"), unsafe_allow_html=True)
    m3.markdown(metric_card("Botellas PET equiv.", f"{int(t_kg/BOTELLA_PET_KG):,}", "♻️", "warn"), unsafe_allow_html=True)
    m4.markdown(metric_card("Años Persistencia",  f"{t_pers:,.0f}", "⏳"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Evolución temporal ──
    st.subheader("📅 Evolución Temporal")
    tab_m, tab_s, tab_tbl = st.tabs(["Mensual", "Acumulado", "Tabla Historial"])

    hist["Mes"] = hist["Fecha"].dt.to_period("M").astype(str)

    with tab_m:
        df_mes = hist.groupby("Mes").agg(
            Impacto=("Impacto total", "sum"),
            Campañas=("Impacto total", "count"),
            KgTotal=("kgs", "sum"),
            Fauna=("Fauna afectada", "sum")
        ).reset_index()
        fig_line = px.bar(
            df_mes, x="Mes", y="Impacto", color_discrete_sequence=[COLOR_PRIMARY],
            title="Impacto IIAE por Mes", text="Campañas",
            hover_data={"KgTotal": ":.1f", "Campañas": True, "Fauna": ":.1f"}
        )
        fig_line.update_traces(texttemplate='%{text} camp.', textposition='outside')
        st.plotly_chart(fig_line, use_container_width=True)

        # Mini tabla resumen mensual
        st.dataframe(
            df_mes.rename(columns={"Mes": "Mes", "Impacto": "IIAE", "KgTotal": "Kg Total", "Fauna": "Fauna"})
            .style.format({"IIAE": "{:.2f}", "Kg Total": "{:.1f}", "Fauna": "{:.1f}"}),
            use_container_width=True, hide_index=True
        )

    with tab_s:
        hist_s = hist.sort_values("Fecha").copy()
        hist_s["IIAE Acumulado"] = hist_s["Impacto total"].cumsum()
        hist_s["Kg Acumulados"]  = hist_s["kgs"].cumsum()
        hist_s["Hora"]           = hist_s["Fecha"].dt.strftime("%H:%M")
        hist_s["Fecha_str"]      = hist_s["Fecha"].dt.strftime("%d/%m/%Y %H:%M")
        fig_area = px.area(
            hist_s, x="Fecha", y="IIAE Acumulado",
            title="Impacto Positivo Acumulado (IIAE)",
            color_discrete_sequence=[COLOR_ACCENT],
            hover_data={"Fecha_str": True, "Hora": True, "Kg Acumulados": ":.1f", "Fecha": False}
        )
        st.plotly_chart(fig_area, use_container_width=True)

    with tab_tbl:
        # Formatear fecha con hora para mostrar en tabla
        hist_display = hist.copy()
        hist_display["Fecha"] = hist_display["Fecha"].dt.strftime("%d/%m/%Y  %H:%M")
        # Reemplazar vacíos por guión
        for col in ["Ubicación", "Operador", "Notas"]:
            hist_display[col] = hist_display[col].replace("", "—").fillna("—")
        st.dataframe(
            hist_display[["Fecha", "Ubicación", "Operador", "Notas", "Tipos", "kgs", "Impacto total", "Fauna afectada"]]
            .rename(columns={"kgs": "Kg Total"})
            .style.format({"Impacto total": "{:.2f}", "Fauna afectada": "{:.2f}", "Kg Total": "{:.2f}"}),
            use_container_width=True, hide_index=True
        )

    # ── Análisis de horarios ──
    if hist["Fecha"].dt.hour.sum() > 0:  # solo si hay datos de hora reales
        st.markdown("---")
        st.subheader("🕐 Análisis de Horarios")
        hc1, hc2 = st.columns(2)
        with hc1:
            hist["Hora_num"] = hist["Fecha"].dt.hour + hist["Fecha"].dt.minute / 60
            hist["Hora_str"] = hist["Fecha"].dt.strftime("%H:%M")
            fig_hora = px.scatter(
                hist, x="Hora_num", y="Impacto total",
                title="Impacto por hora del día",
                color="Impacto total",
                color_continuous_scale=["#c9eac6", COLOR_ACCENT, COLOR_PRIMARY],
                hover_data={"Hora_str": True, "Impacto total": ":.2f", "Hora_num": False},
                labels={"Hora_num": "Hora del día", "Impacto total": "IIAE"}
            )
            fig_hora.update_layout(coloraxis_showscale=False, xaxis=dict(tickvals=list(range(0,25,2)),
                ticktext=[f"{h:02d}:00" for h in range(0,25,2)]))
            st.plotly_chart(fig_hora, use_container_width=True)
        with hc2:
            franja_labels = {(6,12): "Mañana 6-12h", (12,17): "Mediodía 12-17h",
                             (17,21): "Tarde 17-21h", (0,6): "Nocturno 0-6h", (21,24): "Noche 21-24h"}
            def get_franja(h):
                for (a,b), label in franja_labels.items():
                    if a <= h < b: return label
                return "Otra"
            hist["Franja"] = hist["Fecha"].dt.hour.apply(get_franja)
            df_franja = hist.groupby("Franja")["Impacto total"].agg(["sum", "count"]).reset_index()
            df_franja.columns = ["Franja", "IIAE Total", "Campañas"]
            fig_franja = px.bar(df_franja, x="Franja", y="IIAE Total",
                title="IIAE por franja horaria", color="IIAE Total",
                color_continuous_scale=["#c9eac6", COLOR_ACCENT, COLOR_PRIMARY],
                text="Campañas")
            fig_franja.update_traces(texttemplate='%{text} camp.', textposition='outside')
            fig_franja.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig_franja, use_container_width=True)

    # ── Análisis de peligrosidad ──
    st.markdown("---")
    st.subheader("⚖️ Análisis de Peligrosidad Real")

    all_tips, all_kgs = [], []
    for _, r in hist.iterrows():
        tips = [t.strip() for t in str(r["Tipos"]).split(",")]
        kgs  = parse_list_string(r["Cantidades (kg)"])
        if len(tips) == len(kgs):
            all_tips.extend(tips)
            all_kgs.extend(kgs)

    if not all_tips:
        st.warning("Datos insuficientes para análisis de peligrosidad.")
    else:
        df_items = pd.DataFrame({"Plástico": all_tips, "Kg": all_kgs})
        df_grp   = df_items.groupby("Plástico")["Kg"].sum().reset_index()

        # Índices de impacto
        df_grp["Índice"]       = df_grp["Plástico"].map(lambda x: plastics.get(x, {}).get('indice', 1.0))
        df_grp["Impacto Real"] = df_grp["Kg"] * df_grp["Índice"]
        df_peligro             = df_grp.sort_values("Impacto Real", ascending=False)

        # Pie chart agrupando < 5%
        tot_kg_pie             = df_grp['Kg'].sum()
        df_grp['Agrupado']     = df_grp.apply(
            lambda r: r['Plástico'] if r['Kg'] >= tot_kg_pie * 0.05 else 'Otros', axis=1
        )
        df_pie = df_grp.groupby('Agrupado')['Kg'].sum().reset_index()

        c_pie, c_tbl = st.columns([1, 1.3])

        with c_pie:
            fig_pie = px.pie(
                df_pie, names="Agrupado", values="Kg",
                title="Distribución por Peso Recogido",
                color_discrete_sequence=COLOR_SEQ, hole=0.35
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)

        with c_tbl:
            st.markdown("**🏆 Ranking de Riesgo (por IIAE):**")
            st.dataframe(
                df_peligro[["Plástico", "Kg", "Índice", "Impacto Real"]]
                .style.format({"Kg": "{:.1f}", "Índice": "{:.2f}", "Impacto Real": "{:.2f}"}),
                use_container_width=True, height=280, hide_index=True
            )
            st.caption("💡 Plásticos ligeros pueden tener mayor impacto que materiales más pesados.")

        # Gráfico Kg vs Impacto Real
        st.markdown("#### 🆚 Peso (Kg) vs Daño Real (IIAE)")
        df_melt = df_peligro.melt(
            id_vars="Plástico", value_vars=["Kg", "Impacto Real"],
            var_name="Métrica", value_name="Valor"
        )
        fig_comp = px.bar(
            df_melt, x="Plástico", y="Valor", color="Métrica", barmode="group",
            color_discrete_map={"Kg": COLOR_GRID, "Impacto Real": COLOR_PRIMARY},
            title="Comparativa: Masa recogida vs Impacto ambiental real"
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # ── Alertas ──
        st.markdown("### 🔔 Alertas del Sistema")

        alerts = []
        if len(hist) >= 3:
            media   = hist['Impacto total'].mean()
            max_val = hist['Impacto total'].max()
            if max_val > 1.5 * media:
                fecha_max = hist.loc[hist['Impacto total'].idxmax(), 'Fecha'].date()
                alerts.append(("warning", f"⚠️ **Recogida anómala ({fecha_max}):** El impacto ({max_val:.1f}) supera 1.5× la media ({media:.1f})."))

            top_p = df_peligro.iloc[0]
            if top_p["Impacto Real"] > t_iiae * 0.5:
                alerts.append(("error", f"🚨 **Riesgo Crítico:** **{top_p['Plástico']}** genera > 50% del daño total. Priorizar su reducción."))

            # Nueva alerta: tendencia creciente
            recientes = hist.sort_values("Fecha").tail(3)["Impacto total"]
            if recientes.is_monotonic_increasing:
                alerts.append(("warning", "📈 **Tendencia al alza:** Las últimas 3 campañas muestran impacto creciente. Revisar zona."))

        if alerts:
            for tipo, msg in alerts:
                getattr(st, tipo)(msg)
        else:
            st.success("✅ Sistema de monitorización activo. Sin alertas críticas.")
            if len(hist) < 3:
                st.caption("Registra al menos 3 campañas para activar alertas avanzadas.")


# ---- VALORIZACIÓN ENERGÉTICA ----
elif selec == "Valorización Energética":
    plastics = load_plastics()
    st.markdown(f'''<h1 style="font-family:Fraunces,serif;font-size:2.2rem;font-weight:400;font-style:italic;color:{COLOR_PRIMARY};letter-spacing:-0.5px;margin-bottom:0.1rem;">Valorización Energética</h1>''', unsafe_allow_html=True)
    st.markdown(
        "Estimación del potencial de generación eléctrica a partir del plástico interceptado mediante **valorización térmica directa** *(Waste-to-Energy)*. "
        "Metodología §2.8 del TFG — fórmula termodinámica con PCI de la base de datos **Phyllis2/TNO**."
    )
    st.markdown("---")

    # ── Datos PCI según PDF del TFG (Phyllis2/TNO) ──
    PCI = {
        "HDPE": 43.56,   # MJ/kg
        "LDPE": 43.50,
        "PP":   43.41,
        "EPS":  40.72,
        "PS":   40.72,
        "PET":  21.85,
        "PVC":  21.65,
    }
    ETA_PLANTA = 0.25   # Rendimiento eléctrico global de planta ciclo combinado (§2.8.3)
    MJ_TO_KWH  = 1 / 3.6

    # ── Contexto científico: por qué WtE y no reciclaje/pirólisis ──
    with st.expander("📖 Justificación técnica (§2.8 del TFG)", expanded=False):
        col_j1, col_j2, col_j3 = st.columns(3)
        with col_j1:
            st.markdown(f"""
<div style="background:white;border-radius:12px;padding:16px;border:1px solid #E8E5DC;height:100%;">
  <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:#e07b39;margin-bottom:8px;">❌ Reciclaje mecánico</div>
  <div style="font-size:0.82rem;color:#555;line-height:1.6;">
    Descartado por <strong>inviabilidad técnica</strong>. Los polímeros fluviales han sufrido fotooxidación severa que degrada sus propiedades mecánicas. El biofouling, la humedad y la mezcla heterogénea generan un balance de emisiones netas negativo (Schyns &amp; Shaver, 2021).
  </div>
</div>""", unsafe_allow_html=True)
        with col_j2:
            st.markdown(f"""
<div style="background:white;border-radius:12px;padding:16px;border:1px solid #E8E5DC;height:100%;">
  <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:#e07b39;margin-bottom:8px;">❌ Pirólisis / Gasificación</div>
  <div style="font-size:0.82rem;color:#555;line-height:1.6;">
    Ineficiente para residuos fluviales. El alto contenido de humedad consume energía en evaporación. La presencia de PVC genera <strong>ácido clorhídrico (HCl)</strong> que daña las turbinas (Al-Salem et al., 2009).
  </div>
</div>""", unsafe_allow_html=True)
        with col_j3:
            st.markdown(f"""
<div style="background:white;border-radius:12px;padding:16px;border:1px solid #E8E5DC;height:100%;">
  <div style="font-size:0.72rem;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:{COLOR_PRIMARY};margin-bottom:8px;">✅ Waste-to-Energy</div>
  <div style="font-size:0.82rem;color:#555;line-height:1.6;">
    Solución óptima. Las poliolefinas (HDPE, LDPE, PP) tienen un <strong>PCI de 40–44 MJ/kg</strong>, comparable al gasoil. Planta de ciclo combinado con sistema de filtrado de gases. η = 0.25 (Arena et al., 2015).
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Fórmula del TFG ──
    st.markdown("### Fórmula de cálculo (§2.8.3)")
    st.latex(r"E_{Elect} = \sum_{i=1}^{n} \left( M_i \cdot PCI_i \right) \cdot \eta_{Planta}")
    st.markdown(f"""
<div style='background:rgba(23,87,74,0.06);border-radius:12px;padding:16px 22px;
            border-left:4px solid {COLOR_PRIMARY};margin:10px 0 24px 0;font-size:0.88rem;color:#444;line-height:2;'>
  <b>Donde:</b><br>
  <b>E<sub>Elect</sub></b> — Energía eléctrica neta generada (MJ)<br>
  <b>M<sub>i</sub></b> — Masa recolectada del polímero <i>i</i> (kg)<br>
  <b>PCI<sub>i</sub></b> — Poder Calorífico Inferior del polímero <i>i</i> (MJ/kg) · Fuente: <em>Phyllis2/TNO</em><br>
  <b>η<sub>Planta</sub></b> — Rendimiento eléctrico global de la planta = <b>0.25</b> (Arena et al., 2015)
</div>
    """, unsafe_allow_html=True)

    # ── Tabla PCI de referencia ──
    st.markdown("### Poderes Caloríficos Inferiores (Phyllis2/TNO)")
    pci_data = [
        {"Polímero": "HDPE", "PCI (MJ/kg)": 43.56, "Equivalencia": "Combustible alto rendimiento (similar al gasoil)"},
        {"Polímero": "LDPE", "PCI (MJ/kg)": 43.50, "Equivalencia": "Combustible alto rendimiento"},
        {"Polímero": "PP",   "PCI (MJ/kg)": 43.41, "Equivalencia": "Combustible alto rendimiento"},
        {"Polímero": "PS",   "PCI (MJ/kg)": 40.72, "Equivalencia": "Alto rendimiento, combustión rápida"},
        {"Polímero": "EPS",  "PCI (MJ/kg)": 40.72, "Equivalencia": "Igual PCI másico que PS (misma matriz estirénica)"},
        {"Polímero": "PET",  "PCI (MJ/kg)": 21.85, "Equivalencia": "Rendimiento medio (oxígeno en estructura)"},
        {"Polímero": "PVC",  "PCI (MJ/kg)": 21.65, "Equivalencia": "Rendimiento bajo (cloro ignífugo)"},
    ]
    df_pci = pd.DataFrame(pci_data)
    st.dataframe(df_pci, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Entrada de datos ──
    st.markdown("### Calcular energía recuperable")
    st.info("Introduce los kg de cada polímero de la campaña para calcular el potencial energético.")

    # Prellenar con la última campaña si existe
    hist = load_historial()
    kg_defaults = {}
    if not hist.empty:
        last = hist.sort_values("Fecha").iloc[-1]
        tipos = [t.strip() for t in str(last["Tipos"]).split(",")]
        cantidades = parse_list_string(last["Cantidades (kg)"])
        if len(tipos) == len(cantidades):
            kg_defaults = dict(zip(tipos, cantidades))

    p_keys = list(PCI.keys())
    cols_inp = st.columns(4)
    kg_vals = {}
    for i, pol in enumerate(p_keys):
        default_val = float(kg_defaults.get(pol, 0.0))
        kg_vals[pol] = cols_inp[i % 4].number_input(
            f"{pol}", min_value=0.0, max_value=100000.0,
            value=default_val, step=0.5, format="%.2f",
            key=f"wte_{pol}"
        )

    if not hist.empty:
        st.caption(f"💡 Valores prellenados con la última campaña registrada ({hist.sort_values('Fecha').iloc[-1]['Fecha'].strftime('%d/%m/%Y %H:%M')}).")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ Calcular Potencial Energético", type="primary", use_container_width=True):

        activos = {p: kg for p, kg in kg_vals.items() if kg > 0}
        if not activos:
            st.warning("⚠️ Introduce al menos un valor de kg mayor a 0.")
        else:
            # Cálculo por polímero
            resultados = []
            for pol, kg in activos.items():
                pci_val  = PCI.get(pol, 0)
                e_mj     = kg * pci_val * ETA_PLANTA
                e_kwh    = e_mj * MJ_TO_KWH
                resultados.append({
                    "Polímero":      pol,
                    "Masa (kg)":     kg,
                    "PCI (MJ/kg)":   pci_val,
                    "E bruta (MJ)":  kg * pci_val,
                    "E neta (MJ)":   e_mj,
                    "E neta (kWh)":  e_kwh,
                })
            df_res = pd.DataFrame(resultados)

            total_kg   = df_res["Masa (kg)"].sum()
            total_mj   = df_res["E neta (MJ)"].sum()
            total_kwh  = df_res["E neta (kWh)"].sum()
            total_bruta= df_res["E bruta (MJ)"].sum()

            # ── KPIs ──
            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(metric_card("Masa total", f"{total_kg:.1f} kg",   "⚖️"),         unsafe_allow_html=True)
            k2.markdown(metric_card("Energía bruta", f"{total_bruta:.0f} MJ", "🔥"),    unsafe_allow_html=True)
            k3.markdown(metric_card("Energía neta", f"{total_mj:.1f} MJ",   "⚡", "accent"), unsafe_allow_html=True)
            k4.markdown(metric_card("Potencia eléctrica", f"{total_kwh:.1f} kWh", "💡", "warn"), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Gráfico de barras por polímero ──
            col_g1, col_g2 = st.columns([1.4, 1])
            with col_g1:
                fig_bar = px.bar(
                    df_res, x="Polímero", y="E neta (kWh)",
                    color="E neta (kWh)",
                    color_continuous_scale=["#c9eac6", COLOR_ACCENT, COLOR_PRIMARY],
                    title="Energía eléctrica neta por polímero (kWh)",
                    text=df_res["E neta (kWh)"].apply(lambda x: f"{x:.1f}"),
                )
                fig_bar.update_traces(textposition="outside")
                fig_bar.update_layout(coloraxis_showscale=False, showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_g2:
                # Gráfico donut de distribución de energía
                fig_pie = px.pie(
                    df_res, names="Polímero", values="E neta (kWh)",
                    title="Distribución de energía",
                    color_discrete_sequence=px.colors.sequential.Teal,
                    hole=0.45
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)

            # ── Tabla detallada ──
            st.markdown("### Desglose por polímero")
            st.dataframe(
                df_res.style.format({
                    "Masa (kg)": "{:.2f}", "PCI (MJ/kg)": "{:.2f}",
                    "E bruta (MJ)": "{:.2f}", "E neta (MJ)": "{:.2f}",
                    "E neta (kWh)": "{:.2f}",
                }),
                use_container_width=True, hide_index=True
            )

            # ── Equivalencias energéticas ──
            st.markdown("### Equivalencias energéticas")
            CONSUMO_HOGAR_KWH  = 3500   # kWh/año hogar medio español (REE)
            CONSUMO_LED_H      = 0.01   # kWh por hora de bombilla LED 10W
            COCHE_ELEC_KM      = 0.2    # kWh/km vehículo eléctrico medio

            hogares_dias  = (total_kwh / CONSUMO_HOGAR_KWH) * 365
            horas_led     = total_kwh / CONSUMO_LED_H
            km_electrico  = total_kwh / COCHE_ELEC_KM

            e1, e2, e3 = st.columns(3)
            e1.markdown(metric_card(
                "Días de hogar abastecido",
                f"{hogares_dias:.1f} días",
                "🏠"
            ), unsafe_allow_html=True)
            e2.markdown(metric_card(
                "Horas de bombilla LED",
                f"{horas_led:,.0f} h",
                "💡", "accent"
            ), unsafe_allow_html=True)
            e3.markdown(metric_card(
                "Km en vehículo eléctrico",
                f"{km_electrico:,.0f} km",
                "🚗", "warn"
            ), unsafe_allow_html=True)

            st.markdown(f"""
<div style='background:rgba(23,87,74,0.07);border-radius:12px;padding:14px 20px;
            border-left:4px solid {COLOR_ACCENT};margin-top:16px;font-size:0.88rem;color:#2a6b5a;line-height:1.7;'>
  <b>⚡ Resumen:</b> La campaña generaría <b>{total_kwh:.1f} kWh</b> de energía eléctrica neta,
  suficiente para abastecer un hogar español durante <b>{hogares_dias:.1f} días</b>.
  Rendimiento de planta η = {ETA_PLANTA} · Fuente PCI: Phyllis2/TNO · Arena et al. (2015).
</div>
            """, unsafe_allow_html=True)


# ---- MODELO DE CÁLCULO ----
elif selec == "Modelo de Cálculo":
    plastics = load_plastics()
    st.title("🧮 Modelo Matemático IIAE")
    st.markdown("Metodología científica del *Índice de Impacto Ambiental Evitado*. Biobardas / UMH Elche &amp; Universidad de Montevideo.")

    tab1, tab2, tab3, tab4 = st.tabs(["Fórmula IIAE", "Criterios y Pesos", "Tabla de Polímeros", "Simulador"])

    with tab1:
        st.markdown("### Fórmula Principal")
        st.latex(r"\text{IIAE} = (P_{MA} \cdot 0{,}30) + (P_{MI} \cdot 0{,}25) + (P_{RE} \cdot 0{,}30) + (P_{PA} \cdot 0{,}15)")

        st.markdown(f"""
<div style='background:rgba(71,215,172,0.08);border-radius:12px;padding:18px 22px;
            border-left:4px solid {COLOR_PRIMARY};margin:10px 0 20px 0;'>
  <b>Donde:</b>
  <ul style='margin:8px 0 0 0;line-height:2;'>
    <li><b>P<sub>MA</sub> – Daño Macroplástico (30%):</b> Impacto físico inmediato: flotabilidad, enredo e ingestión.</li>
    <li><b>P<sub>MI</sub> – Daño Microplástico (25%):</b> Tendencia a fragmentarse en partículas irrecuperables.</li>
    <li><b>P<sub>RE</sub> – Riesgo Ecológico (30%):</b> Toxicidad química por lixiviación y adsorción de contaminantes.</li>
    <li><b>P<sub>PA</sub> – Persistencia Ambiental (15%):</b> Vida media del residuo en el ecosistema.</li>
  </ul>
</div>
        """, unsafe_allow_html=True)

        st.markdown("### Fórmulas Auxiliares")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Persistencia Acumulada:**")
            st.latex(r"\text{Persist.} = \sum_{i} M_i \times V_i")
            st.caption("M_i = kg recogidos del material i, V_i = vida media en años.")
        with c2:
            st.markdown("**Fauna Protegida (estimada):**")
            st.latex(r"\text{Fauna} = \text{IIAE}_{total} \times 0{,}03")
            st.caption("Coeficiente empírico basado en densidad de fauna en ríos afectados.")

        st.markdown("---")
        st.markdown("### Referencias Científicas")
        refs = [
            ("Wilcox et al. (2016)", "Identifica el impacto físico como la causa más documentada de mortalidad directa en fauna marina y fluvial. Base del criterio P_MA."),
            ("Gall & Thompson (2015)", "El 100% de tortugas y el 40% de aves interactúan casi exclusivamente con plásticos flotantes. Sustenta la ponderación de flotabilidad."),
            ("Song et al. (2017)", "Describe el proceso sinérgico UV + abrasión mecánica que genera fragmentación. El EPS pierde el 76.5% de su volumen en solo 6 meses. Base del criterio P_MI."),
            ("Fu et al. (2021)", "Descubre la interacción π-π del poliestireno con hidrocarburos aromáticos. Sustenta la alta adsorción de PS y EPS."),
            ("Xia et al. (2023)", "Demuestra que polímeros amorfos (LDPE) adsorben contaminantes en su interior. Base de la ponderación de adsorción en P_RE."),
            ("Chamas et al. (2020)", "Calcula las Tasas de Degradación Superficial Específica (SSDR) de cada polímero. Base completa del criterio P_PA."),
            ("Hermabessiere et al. (2017)", "El PVC puede contener hasta el 50% de su peso en aditivos químicos. Sustenta la máxima puntuación de lixiviación del PVC."),
            ("Oluwoye et al. (2023)", "El fondo del río actúa como 'cápsula del tiempo': sin UV y con bajas temperaturas, la degradación se detiene casi por completo."),
        ]
        for autor, desc in refs:
            st.markdown(f"- **{autor}:** {desc}")

    with tab2:
        st.markdown("### Distribución de Pesos del IIAE")

        pesos_data = [
            {"Criterio": "P_MA – Daño Macroplástico", "Peso (%)": 30,
             "Justificación": "Daño físico inmediato y letal; causa más frecuente de mortalidad directa documentada."},
            {"Criterio": "P_MI – Daño Microplástico",  "Peso (%)": 25,
             "Justificación": "La fragmentación hace el residuo irrecuperable; premia capturar plásticos frágiles (EPS) a tiempo."},
            {"Criterio": "P_RE – Riesgo Ecológico",    "Peso (%)": 30,
             "Justificación": "Toxicidad invisible pero devastadora; altera la cadena trófica de forma persistente."},
            {"Criterio": "P_PA – Persistencia Ambiental", "Peso (%)": 15,
             "Justificación": "Daño a largo plazo; el IIAE prioriza lo que mata hoy sobre el daño generacional."},
        ]
        df_pesos = pd.DataFrame(pesos_data)
        st.dataframe(df_pesos, use_container_width=True, hide_index=True)

        fig_pie_pesos = px.pie(
            df_pesos, names="Criterio", values="Peso (%)",
            title="Distribución de Pesos del Índice IIAE",
            color_discrete_sequence=COLOR_SEQ, hole=0.4
        )
        fig_pie_pesos.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie_pesos, use_container_width=True)

        st.markdown("### Subcriterios de cada componente")
        st.markdown(f"""
<div style='display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:10px;'>
  <div style='background:#f0f8f4;border-radius:10px;padding:14px;border-top:3px solid {COLOR_PRIMARY};'>
    <b>P_MA – Macroplástico</b><br/>
    <small>1.1 Flotabilidad &nbsp;·&nbsp; 1.2 Potencial de Enredo &nbsp;·&nbsp; 1.3 Potencial de Ingestión</small>
  </div>
  <div style='background:#f0f8f4;border-radius:10px;padding:14px;border-top:3px solid {COLOR_ACCENT};'>
    <b>P_MI – Microplástico</b><br/>
    <small>2.1 Tasa de Fragmentación &nbsp;·&nbsp; 2.2 Exposición Superficial (UV)</small>
  </div>
  <div style='background:#f0f8f4;border-radius:10px;padding:14px;border-top:3px solid {COLOR_WARN};'>
    <b>P_RE – Riesgo Ecológico</b><br/>
    <small>3.1 Lixiviación de Aditivos &nbsp;·&nbsp; 3.2 Adsorción de Contaminantes</small>
  </div>
  <div style='background:#f0f8f4;border-radius:10px;padding:14px;border-top:3px solid #888;'>
    <b>P_PA – Persistencia</b><br/>
    <small>Vida media proyectada según Chamas et al. (2020) y Oluwoye et al. (2023)</small>
  </div>
</div>
        """, unsafe_allow_html=True)

    with tab3:
        st.markdown("**Índices IIAE por polímero — Tabla Final del TFG (Biobardas / UMH Elche &amp; Univ. de Montevideo):**")

        tabla_oficial = [
            {"Rg": "🥇 1", "Polímero": "EPS",  "P_MA": 4.00, "P_MI": 5.00, "P_RE": 4.25, "P_PA": 1.50, "IIAE": 3.95, "Vida (años)": "~50",   "Peligrosidad": "🔴 Alta"},
            {"Rg": "🥈 2", "Polímero": "PP",   "P_MA": 4.58, "P_MI": 4.88, "P_RE": 3.00, "P_PA": 2.25, "IIAE": 3.83, "Vida (años)": "~80",   "Peligrosidad": "🔴 Alta"},
            {"Rg": "🥉 3", "Polímero": "LDPE", "P_MA": 4.92, "P_MI": 3.25, "P_RE": 3.50, "P_PA": 2.75, "IIAE": 3.75, "Vida (años)": "~100",  "Peligrosidad": "🔴 Alta"},
            {"Rg": "4",    "Polímero": "PS",   "P_MA": 2.25, "P_MI": 3.50, "P_RE": 4.25, "P_PA": 1.50, "IIAE": 3.05, "Vida (años)": "~50",   "Peligrosidad": "🟡 Media"},
            {"Rg": "5",    "Polímero": "HDPE", "P_MA": 3.00, "P_MI": 3.25, "P_RE": 2.25, "P_PA": 4.00, "IIAE": 2.99, "Vida (años)": "~800",  "Peligrosidad": "🟡 Media"},
            {"Rg": "6",    "Polímero": "PVC",  "P_MA": 1.16, "P_MI": 1.00, "P_RE": 3.25, "P_PA": 5.00, "IIAE": 2.32, "Vida (años)": ">2500", "Peligrosidad": "🟡 Media"},
            {"Rg": "7",    "Polímero": "PET",  "P_MA": 1.25, "P_MI": 1.13, "P_RE": 1.00, "P_PA": 1.00, "IIAE": 1.11, "Vida (años)": "~20",   "Peligrosidad": "🟢 Baja"},
        ]
        df_oficial = pd.DataFrame(tabla_oficial)
        st.dataframe(
            df_oficial.style.format({"P_MA": "{:.2f}", "P_MI": "{:.2f}",
                                     "P_RE": "{:.2f}", "P_PA": "{:.2f}", "IIAE": "{:.2f}"}),
            use_container_width=True, hide_index=True
        )

        st.markdown("#### Radar de Criterios — Todos los Polímeros")
        cats_r   = ["P_MA", "P_MI", "P_RE", "P_PA"]
        labels_r = ["Macroplástico", "Microplástico", "Riesgo Eco.", "Persistencia"]
        fig_rad_all = go.Figure()
        for row in tabla_oficial:
            vals = [row[c] for c in cats_r] + [row[cats_r[0]]]
            fig_rad_all.add_trace(go.Scatterpolar(
                r=vals, theta=labels_r + [labels_r[0]],
                fill='toself', name=row["Polímero"]
            ))
        fig_rad_all.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5.5])),
            title="Perfil de Riesgo por Criterio – Todos los Polímeros",
            height=480
        )
        st.plotly_chart(fig_rad_all, use_container_width=True)

        df_bar_iiae = pd.DataFrame(tabla_oficial).sort_values("IIAE")
        fig_bar_iiae = px.bar(
            df_bar_iiae, x="IIAE", y="Polímero", orientation='h',
            title="Ranking IIAE Final",
            color="IIAE",
            color_continuous_scale=["#c9eac6", COLOR_ACCENT, COLOR_PRIMARY],
            text="IIAE"
        )
        fig_bar_iiae.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_bar_iiae.update_layout(coloraxis_showscale=False, xaxis_range=[0, 4.5])
        st.plotly_chart(fig_bar_iiae, use_container_width=True)

    with tab4:
        st.markdown("**Simula el impacto de distintos escenarios de recogida:**")
        sim_col1, sim_col2 = st.columns(2)
        with sim_col1:
            sim_mat = st.selectbox("Material", list(plastics.keys()))
            sim_kg  = st.slider("Kilos recogidos", 1, 500, 50)
        with sim_col2:
            dat       = plastics[sim_mat]
            sim_iiae  = sim_kg * dat["indice"]
            sim_fauna = sim_iiae * COEF_FAUNA
            sim_pers  = sim_kg * dat["vida"]
            st.markdown(metric_card("IIAE simulado",     f"{sim_iiae:.2f}", "🌿"), unsafe_allow_html=True)
            st.markdown(metric_card("Fauna protegida",   f"{sim_fauna:.1f}", "🐟", "accent"), unsafe_allow_html=True)
            st.markdown(metric_card("Años persistencia", f"{sim_pers:,}", "⏳", "warn"), unsafe_allow_html=True)

        # Desglose de criterios si el material tiene los datos completos
        if all(k in dat for k in ["pma", "pmi", "pre", "ppa"]):
            st.markdown(f"#### Desglose de criterios — {sim_mat}")
            df_des = pd.DataFrame({
                "Criterio":    ["P_MA (Macro)", "P_MI (Micro)", "P_RE (Ecológico)", "P_PA (Persistencia)"],
                "Puntuación":  [dat["pma"], dat["pmi"], dat["pre"], dat["ppa"]],
                "Peso":        [0.30, 0.25, 0.30, 0.15],
            })
            df_des["Aportación al IIAE"] = df_des["Puntuación"] * df_des["Peso"]
            fig_des = px.bar(
                df_des, x="Criterio", y="Aportación al IIAE",
                color="Criterio", title=f"Composición del IIAE — {sim_mat} ({sim_kg} kg)",
                color_discrete_sequence=COLOR_SEQ, text="Aportación al IIAE"
            )
            fig_des.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_des.update_layout(showlegend=False)
            st.plotly_chart(fig_des, use_container_width=True)
