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
    page_title="Modelo IIAE Biobardas",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
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
custom_template.layout.plot_bgcolor  = '#fcfcf8'
custom_template.layout.paper_bgcolor = COLOR_BG
custom_template.layout.font          = dict(color=COLOR_PRIMARY, family="Montserrat, Arial, sans-serif")
custom_template.layout.xaxis        = dict(gridcolor=COLOR_GRID, zeroline=False, showgrid=True)
custom_template.layout.yaxis        = dict(gridcolor=COLOR_GRID, zeroline=False, showgrid=True)
custom_template.layout.legend       = dict(bgcolor='rgba(255,255,255,0.5)', bordercolor=COLOR_GRID)
custom_template.layout.margin       = dict(t=50, b=40, l=40, r=40)

pio.templates["biobardas"] = custom_template
pio.templates.default      = "biobardas"

# --- CSS ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

html, body, .stApp {{
    background: linear-gradient(135deg, #f9f7e3 0%, #e7e7c0 100%) !important;
    font-family: 'Montserrat', sans-serif;
    color: {COLOR_PRIMARY};
}}

h1, h2, h3, h4, h5 {{
    color: {COLOR_PRIMARY} !important;
    font-weight: 700;
    letter-spacing: -0.5px;
}}

.block-container {{
    background-color: {COLOR_BG};
    border-radius: 25px;
    padding: 2.5rem 2rem;
    box-shadow: 0 10px 30px -5px rgba(23,87,74,0.09);
    margin-top: 20px;
}}

/* SIDEBAR */
[data-testid="stSidebar"] {{
    background-color: #fdfdfa;
    border-right: 1px solid {COLOR_GRID};
}}
[data-testid="stSidebar"] .block-container {{
    background: transparent;
    box-shadow: none;
    padding: 1.5rem 1rem;
}}

/* BOTONES SIDEBAR */
[data-testid="stSidebar"] button {{
    width: 100%;
    background-color: transparent;
    color: {COLOR_PRIMARY};
    text-align: left;
    padding: 8px 15px;
    border: 1px solid transparent;
    border-radius: 10px;
    transition: all 0.2s ease;
    font-family: 'Montserrat', sans-serif;
    font-weight: 500;
}}
[data-testid="stSidebar"] button:hover {{
    background-color: #e7e7c0;
    border-color: {COLOR_GRID};
}}
[data-testid="stSidebar"] button[kind="primary"] {{
    background-color: {COLOR_PRIMARY} !important;
    color: white !important;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(23,87,74,0.25);
    font-weight: 600;
}}

/* TABLAS */
.stDataFrame {{
    border: 1px solid {COLOR_GRID} !important;
    border-radius: 12px !important;
    overflow: hidden;
}}
[data-testid="stDataFrame"] thead th {{
    background-color: #e7e7c0 !important;
    color: {COLOR_PRIMARY} !important;
    font-weight: 700 !important;
    border-bottom: 2px solid {COLOR_PRIMARY} !important;
}}

/* TARJETAS MÉTRICAS */
.metric-card {{
    background: linear-gradient(145deg, #ffffff, #f0f0eb);
    border-radius: 16px;
    padding: 20px 16px;
    border-left: 5px solid {COLOR_PRIMARY};
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    text-align: center;
    margin-bottom: 15px;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.metric-card:hover {{
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(23,87,74,0.15);
}}
.metric-card.accent {{ border-left-color: {COLOR_ACCENT}; }}
.metric-card.warn   {{ border-left-color: {COLOR_WARN}; }}
.metric-value {{
    font-size: 1.75em;
    font-weight: 800;
    color: {COLOR_PRIMARY};
    margin: 0;
    line-height: 1.2;
}}
.metric-label {{
    font-size: 0.88em;
    color: #666;
    margin-top: 6px;
    font-weight: 500;
}}
.metric-icon {{ font-size: 1.4em; margin-bottom: 4px; }}

/* FORMULARIOS */
.stNumberInput input, .stTextInput input {{
    border-radius: 8px !important;
    border: 1px solid {COLOR_GRID} !important;
    font-family: 'Montserrat', sans-serif !important;
}}
.stNumberInput input:focus, .stTextInput input:focus {{
    border-color: {COLOR_PRIMARY} !important;
    box-shadow: 0 0 0 2px rgba(23,87,74,0.15) !important;
}}

/* BOTÓN PRINCIPAL */
button[kind="primary"] {{
    background-color: {COLOR_PRIMARY} !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Montserrat', sans-serif !important;
    letter-spacing: 0.3px;
    transition: all 0.2s !important;
}}
button[kind="primary"]:hover {{
    background-color: #0f3d32 !important;
    box-shadow: 0 4px 14px rgba(23,87,74,0.3) !important;
}}

/* EXPANDERS */
details {{
    border-radius: 12px !important;
    border: 1px solid {COLOR_GRID} !important;
    padding: 4px 8px;
}}

.stAlert {{ border-radius: 12px; }}
hr {{ border-color: {COLOR_GRID}; border-style: dashed; margin: 25px 0; }}
footer {{ visibility: hidden; }}

/* PROGRESS BAR */
.stProgress > div > div {{
    background-color: {COLOR_PRIMARY} !important;
    border-radius: 4px;
}}
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. CONSTANTES Y DATOS
# ==========================================

PLASTIC_FILE      = "data_plasticos.json"
HIST_FILE         = "historial_recolecciones.csv"
BOTELLA_PET_KG    = 0.025
COEF_FAUNA        = 0.03
HIST_COLUMNS      = ["Fecha", "Tipos", "Cantidades (kg)", "Impacto total", "Fauna afectada"]

DEF_PLASTICS = {
    'EPS':  {"indice": 4.14, "vida": 50},
    'PP':   {"indice": 3.92, "vida": 80},
    'PS':   {"indice": 3.16, "vida": 50},
    'LDPE': {"indice": 3.12, "vida": 100},
    'HDPE': {"indice": 2.37, "vida": 100},
    'PVC':  {"indice": 2.32, "vida": 200},
    'PET':  {"indice": 1.42, "vida": 15},
}

COLOR_SEQ = [COLOR_PRIMARY, COLOR_ACCENT, '#a8d5b0', '#e7e7c0', '#f5c06a', '#a0a080', '#c9eac6']


# ==========================================
# 3. UTILIDADES Y LÓGICA
# ==========================================

def load_plastics() -> dict:
    """Carga plásticos desde JSON. Sin cache para reflejar cambios inmediatos."""
    if os.path.exists(PLASTIC_FILE):
        try:
            with open(PLASTIC_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and data:
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
    """Carga historial CSV con manejo robusto de errores."""
    if not os.path.exists(HIST_FILE) or os.path.getsize(HIST_FILE) == 0:
        return pd.DataFrame(columns=HIST_COLUMNS)
    try:
        hist = pd.read_csv(HIST_FILE, header=None, names=HIST_COLUMNS)
        hist["Fecha"] = pd.to_datetime(hist["Fecha"], errors='coerce')
        hist["Impacto total"] = pd.to_numeric(hist["Impacto total"], errors='coerce').fillna(0)
        hist["Fauna afectada"] = pd.to_numeric(hist["Fauna afectada"], errors='coerce').fillna(0)
        hist = hist.dropna(subset=["Fecha"])
        return hist
    except Exception as e:
        st.warning(f"Aviso al leer historial: {e}")
        return pd.DataFrame(columns=HIST_COLUMNS)


def save_historial(fecha: str, tipos: list, cantidades: list, total: float, fauna: float) -> None:
    try:
        with open(HIST_FILE, 'a', newline='') as f:
            csv.writer(f).writerow([fecha, ", ".join(tipos), ", ".join(map(str, cantidades)), total, fauna])
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
              autor: str = "Equipo Biobardas") -> bytes:
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
    pdf.cell(0, 8, f'Fecha: {datetime.date.today().strftime("%d/%m/%Y")}   |   Autor: {autor}', ln=1)
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
    "👣 Huella de Carbono":   "Huella de Carbono",
    "🧮 Modelo de Cálculo":   "Modelo de Cálculo",
}

with st.sidebar:
    st.markdown(
        f"<h2 style='text-align:center;color:{COLOR_PRIMARY};margin-bottom:8px;line-height:1.3'>🌿 IIAE<br>Biobardas</h2>"
        f"<p style='text-align:center;font-size:0.78em;color:#888;margin-bottom:20px;'>Sistema de Gestión Ambiental</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    if "page" not in st.session_state:
        st.session_state["page"] = "Inicio"

    for label, key in PAGINAS.items():
        is_active = st.session_state["page"] == key
        btn_type  = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state["page"] = key
            st.rerun()

    st.markdown("---")
    st.markdown(
        f"<p style='font-size:0.75em;color:#aaa;text-align:center;'>v2.0 · {datetime.date.today().year}</p>",
        unsafe_allow_html=True
    )

selec = st.session_state["page"]


# ==========================================
# 5. PÁGINAS
# ==========================================

# ---- INICIO ----
if selec == "Inicio":
    col_txt, col_img = st.columns([1.6, 1])

    with col_txt:
        st.title("🌿 IIAE Biobardas")
        st.markdown(
            f"<h3 style='color:{COLOR_ACCENT};font-weight:600;margin-top:-10px'>"
            "Innovación aplicada a la protección de nuestros ríos</h3>",
            unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown(f"""
        <div style='background:rgba(71,215,172,0.1);padding:22px;border-radius:15px;
                    border-left:5px solid {COLOR_PRIMARY};'>
          <h4 style='margin-top:0;color:{COLOR_PRIMARY}'>Bienvenido al sistema de gestión</h4>
          <p style='margin-bottom:10px'>Esta herramienta cuantifica científicamente el beneficio ambiental
          de las labores de limpieza en ríos mediante el <strong>Índice de Impacto Ambiental Evitado (IIAE)</strong>.</p>
          <ul style='margin:0;padding-left:20px;line-height:2'>
            <li><b>Calcula</b> el IIAE ponderado por material y persistencia</li>
            <li><b>Analiza</b> la peligrosidad real más allá del peso</li>
            <li><b>Visualiza</b> tendencias acumuladas e historial</li>
            <li><b>Genera</b> informes técnicos en PDF</li>
            <li><b>Estima</b> la huella de CO₂ evitada</li>
          </ul>
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
            # Placeholder visual si no hay imagen
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,{COLOR_PRIMARY},{COLOR_ACCENT});
                        border-radius:20px;height:280px;display:flex;align-items:center;
                        justify-content:center;'>
              <span style='font-size:6em'>🌊</span>
            </div>
            """, unsafe_allow_html=True)


# ---- ANÁLISIS AMBIENTAL ----
elif selec == "Análisis Ambiental":
    plastics = load_plastics()
    st.title("📊 Análisis de Nueva Recogida")

    # ── Gestión de materiales ──
    with st.expander("⚙️ Gestión de Índices y Materiales"):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Materiales configurados:**")
            df_p = pd.DataFrame.from_dict(plastics, orient='index').reset_index()
            df_p.columns = ["Material", "Índice IIAE", "Vida (años)"]
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
    st.subheader("📦 Pesos recogidos por material (kg)")

    # ── Formulario de cálculo ──
    with st.form("calc_form"):
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
            save_historial(
                datetime.date.today().isoformat(),
                list(df["Plástico"]),
                list(df["Kg recogidos"]),
                tot_imp, tot_fau
            )

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
            st.session_state['ftot'], st.session_state['kgtot']
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
    st.title("📈 Dashboard de Impacto Acumulado")

    # Controles superiores
    col_del, col_exp, _ = st.columns([1, 1, 3])
    if col_del.button("⚠️ Borrar Historial", type="secondary"):
        if os.path.exists(HIST_FILE):
            os.remove(HIST_FILE)
            st.success("Historial borrado.")
            st.rerun()

    hist = load_historial()

    if hist.empty:
        st.info("📭 No hay datos históricos. Registra tu primera campaña en 'Análisis Ambiental'.")
        st.stop()

    # Columna de kg calculada robustamente
    hist["kgs"] = hist["Cantidades (kg)"].apply(lambda s: sum(parse_list_string(s)))

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
            KgTotal=("kgs", "sum")
        ).reset_index()
        fig_line = px.bar(
            df_mes, x="Mes", y="Impacto", color_discrete_sequence=[COLOR_PRIMARY],
            title="Impacto IIAE por Mes", text="Campañas",
            hover_data={"KgTotal": ":.1f", "Campañas": True}
        )
        fig_line.update_traces(texttemplate='%{text} camp.', textposition='outside')
        st.plotly_chart(fig_line, use_container_width=True)

    with tab_s:
        hist_s = hist.sort_values("Fecha").copy()
        hist_s["IIAE Acumulado"] = hist_s["Impacto total"].cumsum()
        hist_s["Kg Acumulados"]  = hist_s["kgs"].cumsum()
        fig_area = px.area(
            hist_s, x="Fecha", y="IIAE Acumulado",
            title="Impacto Positivo Acumulado (IIAE)",
            color_discrete_sequence=[COLOR_ACCENT]
        )
        st.plotly_chart(fig_area, use_container_width=True)

    with tab_tbl:
        st.dataframe(
            hist[["Fecha", "Tipos", "Cantidades (kg)", "Impacto total", "Fauna afectada", "kgs"]]
            .rename(columns={"kgs": "Kg Total"})
            .style.format({"Impacto total": "{:.2f}", "Fauna afectada": "{:.2f}", "Kg Total": "{:.2f}"}),
            use_container_width=True, hide_index=True
        )

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


# ---- HUELLA DE CARBONO ----
elif selec == "Huella de Carbono":
    st.title("👣 Huella de Carbono Evitada")
    st.markdown("Comparativa de emisiones CO₂ equivalente al reciclar vs. producir plástico virgen.")

    col_in, _ = st.columns([1, 2])
    with col_in:
        kg_in = st.number_input("Kg de plástico gestionado:", value=100.0, min_value=0.1, step=10.0, format="%.1f")

    FACTORES = {
        "Reciclaje Ideal":  (0.85, 1.75),
        "Reciclaje en Río": (1.30, 2.35),
        "Plástico Virgen":  (1.85, 3.35),
    }

    rows = [
        {
            "Escenario": name,
            "CO₂ Mínimo (kg)": kg_in * mn,
            "CO₂ Máximo (kg)": kg_in * mx,
            "CO₂ Medio (kg)":  kg_in * (mn + mx) / 2
        }
        for name, (mn, mx) in FACTORES.items()
    ]
    df_c = pd.DataFrame(rows)

    # Gráfico de rango con error bars
    fig = go.Figure()
    colors = [COLOR_ACCENT, COLOR_PRIMARY, COLOR_WARN]
    for i, row in df_c.iterrows():
        mid = row["CO₂ Medio (kg)"]
        err = row["CO₂ Máximo (kg)"] - mid
        fig.add_trace(go.Bar(
            name       = row["Escenario"],
            x          = [row["Escenario"]],
            y          = [mid],
            error_y    = dict(type='data', array=[err], visible=True),
            marker_color = colors[i],
            text       = f"{mid:.1f} kg",
            textposition='auto',
        ))
    fig.update_layout(
        title      = f"Emisiones estimadas para {kg_in:.1f} kg de plástico (kg CO₂e)",
        showlegend = False,
        barmode    = 'group'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabla resumen
    st.dataframe(
        df_c.set_index("Escenario").style.format("{:.1f}"),
        use_container_width=True
    )

    # Ahorro neto (usando valores medios)
    ahorro = df_c.loc[2, "CO₂ Medio (kg)"] - df_c.loc[1, "CO₂ Medio (kg)"]
    if ahorro > 0:
        st.success(f"✅ **Ahorro neto estimado:** ~{ahorro:.1f} kg CO₂e respecto a producir plástico virgen.")
        st.markdown(f"> Equivale a **{ahorro/0.21:.0f} km** en coche de combustión (aprox. 0.21 kg CO₂/km).")
    else:
        st.warning("⚠️ El balance CO₂ depende de la eficiencia del proceso de reciclaje.")


# ---- MODELO DE CÁLCULO ----
elif selec == "Modelo de Cálculo":
    plastics = load_plastics()
    st.title("🧮 Modelo Matemático IIAE")
    st.markdown("Metodología científica utilizada para los cálculos del sistema.")

    tab1, tab2, tab3 = st.tabs(["Fórmulas", "Parámetros", "Simulador"])

    with tab1:
        st.markdown("### 1. Índice de Impacto Ambiental Evitado")
        st.latex(r"\text{IIAE} = \sum_{i=1}^{n} \left[ M_i \cdot \left( P_{M_i} + P_{\mu P_i} + P_{E_i} \right) \right]")
        st.caption("Suma ponderada de la masa por factores: Macroplástico (P_M), Microplástico (P_μP) y Riesgo Ecológico (P_E).")

        st.markdown("### 2. Persistencia Acumulada en el Medio")
        st.latex(r"\text{Persistencia} = \sum_{i=1}^{n} \left( M_i \times V_i \right)")
        st.caption("M_i = masa del material i (kg), V_i = vida media en el medio (años).")

        st.markdown("### 3. Estimación de Fauna Protegida")
        st.latex(r"\text{Fauna} = \text{IIAE}_{\text{total}} \times 0.03")
        st.caption("Coeficiente empírico basado en densidad de fauna en ríos afectados.")

        st.markdown("### 4. Equivalencia en Botellas PET")
        st.latex(r"\text{Botellas} = \frac{M_{\text{total}}}{0.025 \text{ kg/botella}}")

    with tab2:
        st.markdown("**Tabla de Referencia de Materiales:**")
        df_ref = pd.DataFrame([
            {"Material": k, "Índice IIAE": v["indice"], "Vida Media (años)": v["vida"],
             "Peligrosidad": "🔴 Alta" if v["indice"] >= 3.5 else ("🟡 Media" if v["indice"] >= 2.5 else "🟢 Baja")}
            for k, v in sorted(plastics.items(), key=lambda x: -x[1]["indice"])
        ])
        st.dataframe(df_ref, use_container_width=True, hide_index=True)

        # Gráfico de índices
        fig_idx = px.bar(
            df_ref.sort_values("Índice IIAE", ascending=True),
            x="Índice IIAE", y="Material", orientation='h',
            title="Índices IIAE por Material", color="Índice IIAE",
            color_continuous_scale=["#c9eac6", COLOR_ACCENT, COLOR_PRIMARY]
        )
        fig_idx.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_idx, use_container_width=True)

    with tab3:
        st.markdown("**Simula el impacto de distintos escenarios:**")
        sim_col1, sim_col2 = st.columns(2)
        with sim_col1:
            sim_mat = st.selectbox("Material", list(plastics.keys()))
            sim_kg  = st.slider("Kilos recogidos", 1, 500, 50)
        with sim_col2:
            dat       = plastics[sim_mat]
            sim_iiae  = sim_kg * dat["indice"]
            sim_fauna = sim_iiae * COEF_FAUNA
            sim_pers  = sim_kg * dat["vida"]
            st.markdown(metric_card("IIAE simulado",       f"{sim_iiae:.2f}", "🌿"), unsafe_allow_html=True)
            st.markdown(metric_card("Fauna protegida",     f"{sim_fauna:.1f}", "🐟", "accent"), unsafe_allow_html=True)
            st.markdown(metric_card("Años persistencia",   f"{sim_pers:,}", "⏳", "warn"), unsafe_allow_html=True)
