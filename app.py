import streamlit as st
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from fpdf import FPDF
from io import BytesIO
import os, json, csv, calendar
import datetime

# ==========================================
# 1. CONFIGURACIÓN VISUAL Y ESTILOS (CSS)
# ==========================================

st.set_page_config(page_title="Modelo IIAE Biobardas", page_icon="🌿", layout="wide")

# --- COLORES CORPORATIVOS ---
COLOR_PRIMARY = '#17574A'    # Verde Oscuro
COLOR_ACCENT = '#47d7ac'     # Verde Menta
COLOR_BG = '#F4F3EE'         # Beige Fondo
COLOR_GRID = '#dcdcc0'       # Beige Oscuro (Bordes)

# --- TEMPLATE DE PLOTLY (Para gráficos elegantes sin fondo blanco) ---
PLOTLY_TEMPLATE = go.layout.Template()
PLOTLY_TEMPLATE.layout.plot_bgcolor = '#fcfcf8' # Fondo del área del gráfico (casi transparente)
PLOTLY_TEMPLATE.layout.paper_bgcolor = COLOR_BG # Fondo externo igual a la app
PLOTLY_TEMPLATE.layout.font.color = COLOR_PRIMARY
PLOTLY_TEMPLATE.layout.font.family = "Montserrat, Arial, sans-serif"
PLOTLY_TEMPLATE.layout.xaxis.gridcolor = COLOR_GRID
PLOTLY_TEMPLATE.layout.yaxis.gridcolor = COLOR_GRID
PLOTLY_TEMPLATE.layout.xaxis.zeroline = False
PLOTLY_TEMPLATE.layout.yaxis.zeroline = False
PLOTLY_TEMPLATE.layout.legend.bgcolor = 'rgba(255,255,255,0.5)'
PLOTLY_TEMPLATE.layout.legend.bordercolor = COLOR_GRID
PLOTLY_TEMPLATE.layout.margin = dict(t=50, b=40, l=40, r=40)
# Asignar template globalmente
px.defaults.template = PLOTLY_TEMPLATE
go.layout.template = PLOTLY_TEMPLATE

# --- CSS INYECTADO ---
st.markdown(f"""
<style>
    /* FUENTE Y FONDO GENERAL */
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
    
    body, .stApp {{
        background: linear-gradient(135deg, #f9f7e3 0%, #e7e7c0 100%);
        font-family: 'Montserrat', sans-serif;
        color: {COLOR_PRIMARY};
    }}

    /* ENCABEZADOS */
    h1, h2, h3, h4, h5 {{ color: {COLOR_PRIMARY} !important; font-weight: 700; letter-spacing: -0.5px; }}
    [data-testid="stHeader"] {{ background-color: transparent; }}

    /* CONTENEDORES (Tarjetas blancas/beige) */
    .block-container {{
        background-color: {COLOR_BG};
        border-radius: 25px;
        padding: 3rem 2rem;
        box-shadow: 0 10px 30px -5px rgba(23, 87, 74, 0.08);
        margin-top: 20px;
    }}

    /* BARRA LATERAL */
    [data-testid="stSidebar"] {{
        background-color: #fdfdfa;
        border-right: 1px solid {COLOR_GRID};
    }}
    /* Botones de Navegación */
    [data-testid="stSidebar"] button {{
        width: 100%;
        background-color: transparent;
        color: {COLOR_PRIMARY};
        text-align: left;
        padding-left: 15px;
        border: 1px solid transparent;
        transition: all 0.2s;
    }}
    [data-testid="stSidebar"] button:hover {{
        background-color: #e7e7c0;
        border-radius: 10px;
        color: {COLOR_PRIMARY};
    }}
    /* Botón Activo (Primary) */
    [data-testid="stSidebar"] button[kind="primary"] {{
        background-color: {COLOR_PRIMARY} !important;
        color: white !important;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(23, 87, 74, 0.2);
    }}

    /* TABLAS (Dataframes) - Adiós al estilo default */
    .stDataFrame {{ 
        border: 1px solid {COLOR_GRID} !important;
        border-radius: 12px !important;
        overflow: hidden;
    }}
    [data-testid="stDataFrame"] {{ background-color: #fcfcf9 !important; }}
    [data-testid="stDataFrame"] thead th {{
        background-color: #e7e7c0 !important;
        color: {COLOR_PRIMARY} !important;
        font-weight: 700 !important;
        border-bottom: 2px solid {COLOR_PRIMARY} !important;
    }}

    /* TARJETAS DE MÉTRICAS (KPIs) */
    .metric-card {{
        background: linear-gradient(145deg, #ffffff, #f0f0eb);
        border-radius: 16px;
        padding: 20px;
        border-left: 6px solid {COLOR_PRIMARY};
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 15px;
        transition: transform 0.2s;
    }}
    .metric-card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 20px rgba(23,87,74,0.15); }}
    .metric-value {{ font-size: 1.8em; font-weight: 800; color: {COLOR_PRIMARY}; margin: 0; }}
    .metric-label {{ font-size: 0.95em; color: #555; margin-top: 5px; font-weight: 500; }}

    /* ALERTAS Y OTROS */
    .stAlert {{ border-radius: 12px; border: 1px solid {COLOR_GRID}; }}
    hr {{ border-color: {COLOR_GRID}; border-style: dashed; margin: 30px 0; }}
    
    /* Footer oculto */
    footer {{ visibility: hidden; }}
    
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. LÓGICA Y DATOS (NO TOCAR)
# ==========================================

PLASTIC_FILE = "data_plasticos.json"
DEF_PLASTICS = {
    'EPS': {"indice":4.14, "vida":50}, 'PP': {"indice":3.92, "vida":80},
    'PS': {"indice":3.16, "vida":50}, 'LDPE': {"indice":3.12, "vida":100},
    'HDPE': {"indice":2.37, "vida":100}, 'PVC': {"indice":2.32, "vida":200},
    'PET': {"indice":1.42, "vida":15}
}
COEF_FAUNA = 0.03
HIST_FILE = "historial_recolecciones.csv"
BOTELLA_PET_KG = 0.025
LONGITUD_RIO_EQ = 50

# --- Utilidades ---

@st.cache_data
def load_plastics():
    if os.path.exists(PLASTIC_FILE):
        try:
            with open(PLASTIC_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and data: return data
        except: pass
    return DEF_PLASTICS.copy()

def save_plastics(data):
    with open(PLASTIC_FILE,'w') as f: json.dump(data, f)

def load_data_historial():
    if os.path.exists(HIST_FILE) and os.path.getsize(HIST_FILE) > 0:
        try:
            hist = pd.read_csv(HIST_FILE, header=None, parse_dates=[0])
            hist.columns = ["Fecha", "Tipos", "Cantidades (kg)", "Impacto total", "Fauna afectada"]
            return hist
        except: return pd.DataFrame()
    return pd.DataFrame()

def save_data_historial(fecha, tipos, cantidades_str, total, ftot):
    with open(HIST_FILE, 'a', newline='') as f:
        w = csv.writer(f)
        w.writerow([fecha, tipos, cantidades_str, total, ftot])

def calc_total_persistence(hist_df, current_plastics):
    total_p = 0
    if hist_df.empty: return 0
    p_data = {**DEF_PLASTICS, **current_plastics}
    for _, row in hist_df.iterrows():
        try:
            # Limpieza robusta de cadenas para evitar errores
            kgs = [float(x.strip()) for x in str(row["Cantidades (kg)"]).replace('[','').replace(']','').split(", ")]
            typs = str(row["Tipos"]).split(", ")
            pers = [p_data.get(t.strip(), {"vida":10}).get('vida',10) for t in typs]
            if len(kgs) == len(pers): total_p += sum([k*p for k,p in zip(kgs, pers)])
        except: continue
    return total_p

# Helper para tarjetas HTML
def metric_card(label, value):
    return f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

# --- PDF ---
def crear_pdf_visual(df, total, ftot, kgtot, autor="Pedro Juan García Navarro"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(23,87,74)
    pdf.cell(0, 14, 'Informe Ambiental IIAE', ln=1, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(65,81,49)
    pdf.cell(0, 10, f'Fecha: {datetime.date.today()}', ln=1)
    pdf.cell(0, 10, f'Autor: {autor}', ln=1)
    pdf.ln(6)
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(201,234,198)
    pdf.set_text_color(23,87,74)
    pdf.cell(0, 12, f'Impacto IIAE: {total:.2f}', ln=1, fill=True)
    pdf.set_fill_color(231,231,192)
    pdf.cell(0, 12, f'Peso Total: {kgtot:.2f} kg', ln=1, fill=True)
    pdf.ln(8)
    
    # Tabla
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(255,255,255)
    headers = ['Plastico', 'Kg', 'IIAE Parcial', 'Fauna', 'Vida']
    w = [35, 30, 35, 30, 30]
    for i,h in enumerate(headers): pdf.cell(w[i], 10, h, border=1)
    pdf.ln()
    pdf.set_font('Arial', '', 11)
    for _, row in df.iterrows():
        pdf.cell(w[0], 10, str(row['Plástico']), 1)
        pdf.cell(w[1], 10, f"{row['Kg recogidos']:.2f}", 1)
        pdf.cell(w[2], 10, f"{row['Impacto total']:.2f}", 1)
        pdf.cell(w[3], 10, f"{row['Fauna afectada']:.2f}", 1)
        pdf.cell(w[4], 10, str(row['Persistencia (años)']), 1, ln=1)
    
    if os.path.exists("bar_impacto.png"):
        pdf.ln(10)
        pdf.image("bar_impacto.png", w=170)
    if os.path.exists("radar_impacto.png"):
        pdf.ln(5)
        pdf.image("radar_impacto.png", w=170)
        
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 3. NAVEGACIÓN LATERAL (Limpia)
# ==========================================

paginas = ["Inicio", "Análisis Ambiental", "Panel de Resultados", "Huella de Carbono","Modelo de Cálculo"]

with st.sidebar:
    st.markdown(f"<h2 style='text-align:center; color:{COLOR_PRIMARY}; margin-bottom:20px;'>🌿 IIAE<br>Biobardas</h2>", unsafe_allow_html=True)
    
    if "sidebar_page" not in st.session_state: st.session_state["sidebar_page"] = "Inicio"
    
    for p in paginas:
        if st.session_state["sidebar_page"] == p:
            # Botón activo (Primary style)
            st.button(f"📌 {p}", key=p, use_container_width=True, type="primary")
        else:
            if st.button(p, key=p, use_container_width=True):
                st.session_state["sidebar_page"] = p
                st.rerun()
                
    selec = st.session_state["sidebar_page"]

# ==========================================
# 4. CONTENIDO DE PÁGINAS
# ==========================================

# --- INICIO ---
if selec == "Inicio":
    col_txt, col_img = st.columns([1.5, 1])
    with col_txt:
        st.title("IIAE Biobardas")
        st.markdown(f"<h3 style='color:{COLOR_ACCENT}'>Innovación aplicada a la protección de nuestros ríos</h3>", unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"""
        <div style='background-color:rgba(231,231,192,0.3); padding:25px; border-radius:15px; border-left:5px solid {COLOR_PRIMARY};'>
        <h4 style='margin-top:0'>Bienvenido al sistema de gestión.</h4>
        <p>Esta herramienta digital permite cuantificar científicamente el beneficio ambiental de las labores de limpieza en ríos.</p>
        <ul>
            <li><b>Calcula</b> el Índice de Impacto Ambiental Evitado (IIAE).</li>
            <li><b>Analiza</b> la peligrosidad real de los materiales más allá del peso.</li>
            <li><b>Genera</b> informes técnicos visuales y PDF.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with col_img:
        if os.path.exists("dibujo_rio_biobarda.png"):
            st.image("dibujo_rio_biobarda.png", use_container_width=True)

# --- ANÁLISIS AMBIENTAL ---
elif selec == "Análisis Ambiental":
    plastics = load_plastics()
    st.title("📊 Análisis de Nueva Recogida")
    
    # Configuración (Colapsable estilizado)
    with st.expander("⚙️ Gestión de Índices y Materiales"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Parámetros actuales:**")
            st.dataframe(pd.DataFrame.from_dict(plastics, orient='index').reset_index().rename(columns={'index':'Tipo'}), use_container_width=True, hide_index=True)
        with c2:
            st.markdown("**Añadir material:**")
            nn = st.text_input("Nombre")
            ni = st.number_input("Índice IIAE", 1.0, 10.0, step=0.1)
            nv = st.number_input("Vida (años)", 1, 1000)
            if st.button("Guardar Nuevo", use_container_width=True):
                if nn: 
                    plastics[nn] = {"indice":ni, "vida":nv}
                    save_plastics(plastics)
                    st.rerun()
            if st.button("Restablecer Valores Originales", use_container_width=True):
                save_plastics(DEF_PLASTICS)
                st.rerun()
    
    st.markdown("---")
    st.subheader("📦 Introduce los pesos recogidos (kg)")
    
    with st.form("calc_form"):
        # Grid de inputs
        cols = st.columns(4)
        cantidades = {}
        p_keys = list(plastics.keys())
        for i, p in enumerate(p_keys):
            cantidades[p] = cols[i%4].number_input(f"{p}", min_value=0.0, step=0.5, format="%.2f", help=f"IIAE: {plastics[p]['indice']}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn_calc = st.form_submit_button("Calcular Impacto", use_container_width=True, type="primary")
        
    if btn_calc:
        kg_total = sum(cantidades.values())
        if kg_total == 0:
            st.warning("⚠️ Introduce al menos una cantidad mayor a 0.")
        else:
            # LÓGICA DE CÁLCULO COMPLETA
            res = []
            for p, kg in cantidades.items():
                if kg > 0:
                    dat = plastics[p]
                    imp = kg * dat["indice"]
                    res.append({
                        "Plástico": p, "Kg recogidos": kg, "Índice IIAE": dat["indice"],
                        "Impacto total": imp, "Fauna afectada": imp * COEF_FAUNA,
                        "Persistencia (años)": dat["vida"]
                    })
            df = pd.DataFrame(res)
            
            # Guardar
            tot_imp = df["Impacto total"].sum()
            tot_fau = df["Fauna afectada"].sum()
            suma_pers = (df['Kg recogidos'] * df['Persistencia (años)']).sum()
            
            st.session_state.update({'df': df, 'total': tot_imp, 'ftot': tot_fau, 'kgtot': kg_total})
            
            save_data_historial(datetime.date.today().isoformat(), ", ".join(df["Plástico"]), 
                                ", ".join(map(str, df["Kg recogidos"])), tot_imp, tot_fau)
            
            # RESULTADOS VISUALES
            st.markdown("### 🏁 Resultados del Análisis")
            
            # Métricas en tarjetas personalizadas
            k1, k2, k3 = st.columns(3)
            k1.markdown(metric_card("Impacto Evitado (IIAE)", f"{tot_imp:.2f}"), unsafe_allow_html=True)
            k2.markdown(metric_card("Peso Total", f"{kg_total:.2f} kg"), unsafe_allow_html=True)
            k3.markdown(metric_card("Fauna Protegida (est.)", f"{tot_fau:.1f}"), unsafe_allow_html=True)
            
            st.info(f"⚡ **Equivalencias:** {int(kg_total/BOTELLA_PET_KG):,} botellas PET | {int(suma_pers):,} años de persistencia plástica evitados.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            g1, g2 = st.columns(2)
            with g1:
                # Gráfico Barras
                fig_bar = px.bar(df, x='Plástico', y='Impacto total', color='Plástico', title="Impacto por Material",
                                 color_discrete_sequence=[COLOR_PRIMARY, COLOR_ACCENT, '#e7e7c0'])
                st.plotly_chart(fig_bar, use_container_width=True)
                fig_bar.write_image("bar_impacto.png")
                
            with g2:
                # Radar Chart
                radar_df = df.copy()
                # Normalizar 0-5 para visualización
                for c in ['Índice IIAE', 'Persistencia (años)']:
                    if radar_df[c].max() > 0:
                        radar_df[c] = (radar_df[c] / radar_df[c].max()) * 5
                
                fig_rad = go.Figure()
                cats = ['Índice IIAE', 'Fauna afectada', 'Persistencia (años)']
                for i, row in radar_df.iterrows():
                    fig_rad.add_trace(go.Scatterpolar(
                        r=[row['Índice IIAE'], row['Fauna afectada'], row['Persistencia (años)']],
                        theta=cats, fill='toself', name=row['Plástico']
                    ))
                fig_rad.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,5])), title="Perfil de Riesgo")
                st.plotly_chart(fig_rad, use_container_width=True)
                fig_rad.write_image("radar_impacto.png")
            
            with st.expander("Ver Tabla Detallada"):
                st.dataframe(df, use_container_width=True)

    if 'df' in st.session_state:
        st.markdown("---")
        pdf_bytes = crear_pdf_visual(st.session_state['df'], st.session_state['total'], st.session_state['ftot'], st.session_state['kgtot'])
        st.download_button("📥 Descargar Informe Oficial (PDF)", pdf_bytes, f"informe_iiae_{datetime.date.today()}.pdf", "application/pdf", use_container_width=True)


# --- PANEL DE RESULTADOS (Funcionalidad Completa + Diseño) ---
elif selec == "Panel de Resultados":
    plastics = load_plastics()
    st.title("📈 Dashboard de Impacto Acumulado")
    
    c_reset, _ = st.columns([1,4])
    if c_reset.button("⚠️ Borrar Historial"):
        if os.path.exists(HIST_FILE): os.remove(HIST_FILE)
        st.rerun()
        
    hist = load_data_historial()
    
    if not hist.empty:
        # 1. PROCESAMIENTO ROBUSTO (Limpieza de brackets)
        hist["kgs"] = hist["Cantidades (kg)"].apply(lambda s: sum([float(x.strip()) for x in str(s).replace('[', '').replace(']', '').split(", ")]))
        
        # 2. MÉTRICAS GLOBALES
        t_iiae = hist["Impacto total"].sum()
        t_kg = hist["kgs"].sum()
        t_fauna = hist["Fauna afectada"].sum()
        t_pers = calc_total_persistence(hist, plastics)
        
        # Tarjetas Superiores (Diseño nuevo)
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(metric_card("IIAE Acumulado", f"{t_iiae:,.2f}"), unsafe_allow_html=True)
        m2.markdown(metric_card("Fauna (estimada)", f"{t_fauna:,.0f}"), unsafe_allow_html=True)
        m3.markdown(metric_card("Botellas Eq.", f"{int(t_kg/BOTELLA_PET_KG):,}"), unsafe_allow_html=True)
        m4.markdown(metric_card("Años Persistencia", f"{t_pers:,.0f}"), unsafe_allow_html=True)
        
        st.markdown("---")
        
        # --- SECCIÓN 1: EVOLUCIÓN (Pestañas) ---
        st.subheader("📅 Evolución Temporal")
        tab_m, tab_s = st.tabs(["Mensual", "Tendencia Acumulada"])
        
        hist["Mes"] = hist["Fecha"].dt.to_period("M").astype(str)
        
        with tab_m:
            df_mes = hist.groupby("Mes")["Impacto total"].sum().reset_index()
            fig_line = px.bar(df_mes, x="Mes", y="Impacto total", title="Impacto Ambiental por Mes", 
                              color_discrete_sequence=[COLOR_PRIMARY])
            st.plotly_chart(fig_line, use_container_width=True)
            
        with tab_s:
            hist_sorted = hist.sort_values("Fecha")
            hist_sorted["Acumulado"] = hist_sorted["Impacto total"].cumsum()
            fig_area = px.area(hist_sorted, x="Fecha", y="Acumulado", title="Impacto Positivo Acumulado (IIAE)", 
                               color_discrete_sequence=[COLOR_ACCENT])
            st.plotly_chart(fig_area, use_container_width=True)
            
        # --- SECCIÓN 2: PELIGROSIDAD Y GRÁFICOS (Funcionalidad completa) ---
        st.markdown("---")
        st.subheader("⚖️ Análisis de Peligrosidad Real")
        
        # Preparar datos desglosados
        all_tips, all_kgs = [], []
        for _, r in hist.iterrows():
            all_tips.extend(str(r["Tipos"]).split(", "))
            all_kgs.extend([float(x.strip()) for x in str(r["Cantidades (kg)"]).replace('[','').replace(']','').split(", ")])
            
        df_items = pd.DataFrame({"Plástico": all_tips, "Kg": all_kgs})
        df_grp = df_items.groupby("Plástico")["Kg"].sum().reset_index()
        
        # Agrupar para el Pie Chart (<5%)
        tot_kg_pie = df_grp['Kg'].sum()
        df_grp['Tipo Agrupado'] = df_grp.apply(lambda r: r['Plástico'] if r['Kg'] >= tot_kg_pie * 0.05 else 'Otros', axis=1)
        df_pie_final = df_grp.groupby('Tipo Agrupado')['Kg'].sum().reset_index()
        
        # Calcular métricas de impacto (Lógica de df_peligro corregida)
        p_idx = {k: v['indice'] for k,v in plastics.items()}
        df_grp["Índice"] = df_grp["Plástico"].map(lambda x: p_idx.get(x, 1.0))
        df_grp["Impacto Real"] = df_grp["Kg"] * df_grp["Índice"]
        
        # Tabla Clasificada por IMPACTO
        df_peligro = df_grp.sort_values("Impacto Real", ascending=False)
        
        # Columnas para gráficos
        c_pie, c_table = st.columns([1, 1.5])
        with c_pie:
            fig_pie = px.pie(df_pie_final, names="Tipo Agrupado", values="Kg", title="Distribución por Peso", 
                             color_discrete_sequence=[COLOR_PRIMARY, COLOR_ACCENT, '#e7e7c0', '#a0a080'])
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with c_table:
            st.markdown("**Ranking de Riesgo (Ordenado por IIAE):**")
            # Tabla estilizada
            st.dataframe(
                df_peligro[["Plástico", "Kg", "Impacto Real"]].style.format({"Kg":"{:.1f} kg", "Impacto Real":"{:.1f}"}),
                use_container_width=True,
                height=300
            )
            st.caption("Nota: Observa cómo plásticos ligeros pueden tener alto impacto.")

        # Gráfico Comparativo Peso vs Impacto
        st.markdown("#### 🆚 Discrepancia: Peso (Kg) vs Daño (IIAE)")
        df_melt = df_peligro.melt(id_vars="Plástico", value_vars=["Kg", "Impacto Real"], var_name="Métrica", value_name="Valor")
        fig_comp = px.bar(df_melt, x="Plástico", y="Valor", color="Métrica", barmode="group",
                          color_discrete_map={"Kg": "#e7e7c0", "Impacto Real": COLOR_PRIMARY})
        st.plotly_chart(fig_comp, use_container_width=True)
            
        # ALERTAS Y RECOMENDACIONES
        st.markdown("### 🔔 Alertas del Sistema")
        st.info("✅ Sistema de monitorización activo.")
        
        if len(hist) >= 3:
            media = hist['Impacto total'].mean()
            max_val = hist['Impacto total'].max()
            if max_val > 1.5 * media:
                fecha_max = hist.loc[hist['Impacto total'].idxmax(), 'Fecha'].date()
                st.warning(f"⚠️ **Recogida Anómala ({fecha_max}):** El impacto ({max_val:.1f}) supera el 1.5x de la media.")
                
            top_polluter = df_peligro.iloc[0]
            if top_polluter["Impacto Real"] > t_iiae * 0.5:
                st.error(f"🚨 **Riesgo Crítico:** El material **{top_polluter['Plástico']}** genera más del 50% del daño ambiental acumulado. Priorizar su reducción.")
        else:
            st.caption("Registra al menos 3 campañas para activar alertas avanzadas.")

        with st.expander("Ver Historial Bruto Completo"):
            st.dataframe(hist, use_container_width=True)

    else:
        st.info("No hay datos históricos. Registra tu primera campaña en 'Análisis Ambiental'.")


# --- HUELLA DE CARBONO ---
elif selec == "Huella de Carbono":
    st.title("👣 Huella de Carbono Evitada")
    st.markdown("Comparativa de emisiones de CO₂ equivalente al reciclar vs. producir plástico virgen.")
    
    kg_in = st.number_input("Kg de plástico gestionado:", value=100.0, step=10.0)
    
    if kg_in > 0:
        factors = {
            "Reciclaje Ideal": (0.85, 1.75),
            "Reciclaje Río": (1.30, 2.35),
            "Plástico Virgen": (1.85, 3.35)
        }
        rows = []
        for name, (mn, mx) in factors.items():
            rows.append({"Escenario": name, "Mínimo": kg_in*mn, "Máximo": kg_in*mx})
        
        df_c = pd.DataFrame(rows)
        
        # Gráfico de Rangos
        fig = go.Figure()
        for _, r in df_c.iterrows():
            color = COLOR_PRIMARY if "Virgen" in r["Escenario"] else COLOR_ACCENT
            fig.add_trace(go.Bar(
                name=r["Escenario"], x=[r["Escenario"]], y=[r["Máximo"]],
                base=[0],
                marker_color=color,
                opacity=0.8,
                text=f"{r['Máximo']:.1f}",
                textposition='auto'
            ))
            # Barra superpuesta para el rango visual
            fig.add_trace(go.Bar(
                name=r["Escenario"]+"_min", x=[r["Escenario"]], y=[r["Mínimo"]],
                marker_color=color,
                opacity=0.4,
                showlegend=False,
                hoverinfo='skip'
            ))
            
        fig.update_layout(title=f"Emisiones estimadas para {kg_in} kg (kg CO₂e)", barmode='overlay')
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla estilizada
        st.dataframe(df_c.set_index("Escenario").style.format("{:.1f}"), use_container_width=True)
        
        ahorro = df_c.loc[2, "Mínimo"] - df_c.loc[1, "Máximo"]
        if ahorro > 0:
            st.success(f"✅ Ahorro neto estimado: Al menos **{ahorro:.1f} kg de CO₂** evitados respecto a plástico virgen.")
        else:
            st.warning("⚠️ El balance de CO₂ depende de la eficiencia del proceso de reciclaje.")


# --- MODELO DE CÁLCULO (LaTeX Correcto) ---
elif selec == "Modelo de Cálculo":
    plastics = load_plastics()
    st.title("🧮 Modelo Matemático IIAE")
    st.markdown("Metodología científica utilizada para los cálculos.")
    
    st.markdown("### 1. Fórmula Principal (IIAE)")
    st.latex(r"\text{IIAE} = \sum_{i=1}^{n} \left[ M_i \cdot \left( P_{M_i} + P_{\mu P_i} + P_{E_i} \right) \right]")
    st.caption("Suma ponderada de la masa por factores de Macroplástico, Microplástico y Riesgo Ecológico.")
    
    st.markdown("### 2. Persistencia en el Medio")
    st.latex(r"\text{Persistencia Acumulada} = \sum (Masa_i \times VidaMedia_i)")
    
    st.markdown("### 3. Estimación de Fauna Protegida")
    st.latex(r"\text{Fauna} = \text{IIAE} \times 0.03")
    st.caption("Coeficiente empírico basado en densidad de fauna en ríos afectados.")
    
    st.markdown("---")
    st.subheader("Parámetros de Referencia")
    df_p = pd.DataFrame([{"Material": k, "Índice IIAE": v["indice"], "Vida Media (años)": v["vida"]} for k,v in plastics.items()])
    st.dataframe(df_p, use_container_width=True)
