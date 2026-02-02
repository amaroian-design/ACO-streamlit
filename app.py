import streamlit as st
import pandas as pd
import requests
import os
import time
import uuid
API_URL = st.secrets["API_URL"]
API_KEY = st.secrets["API_KEY"]
API_URL_PDF = st.secrets["API_URL_PDF"]

# -------------------------------------------------
# CONFIGURACIÓN DE PÁGINA (DEBE IR PRIMERO)
# -------------------------------------------------
st.set_page_config(page_title="AOC Diagnostic Portal", page_icon="🛡️")

with st.sidebar:

    st.markdown("""
        <h1 style='color: #2e7d32; text-align: center; font-family: sans-serif;'>
        🛡️ AOC <span style='color: white;'>Diagnostic</span>
        </h1>
        <hr style="border: 1px solid #333;">
    """, unsafe_allow_html=True)
    
# -------------------------------------------------
# ANTI-CAOS: INICIALIZACIÓN DE ESTADO
# -------------------------------------------------
def init_state():
    defaults = {
        "diagnostico_listo": False,
        "run_count": 0,
        "cambios": None,
        "archivo_cargado": False,
        "df_user": None,
        "columna_pesos": None,
        "pdf_requested": False,
        "csv_uploaded_backend": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
# -------------------------------------------------
# ESTILOS
# -------------------------------------------------
st.markdown("""
<style>
.main { background-color: #0e1117; }
.stButton>button {
    width: 100%;
    border-radius: 6px;
    height: 3em;
    background-color: #2e7d32;
    color: white;
    font-weight: bold;
}
.stMetric {
    background-color: #1e1e1e;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #333;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------
def get_exposure_level():
    count = st.session_state.run_count
    if count <= 2:
        return "full"
    elif count <= 5:
        return "reduced"
    else:
        return "minimal"

def classify_activity(x):
    if x < 0.05:
        return "Low"
    elif x < 0.15:
        return "Moderate"
    elif x < 0.35:
        return "High"
    else:
        return "Critical"

def reset_session():
    st.session_state.diagnostico_listo = False
    st.session_state.run_count = 0
    st.session_state.cambios = None
    st.session_state.archivo_cargado = False
    st.session_state.df_user = None
    st.session_state.columna_pesos = None
    st.session_state.pdf_requested = False 
# -------------------------------------------------
# UI – TEXTO PRINCIPAL timeout
# -------------------------------------------------
st.title("🛡️ AOC / AHR: Portal de Auditoría Estructural")

st.info("""
**AOC / AHR Diagnostic™**

Plataforma de diagnóstico estructural.
No provee señales de trading ni recomendaciones de inversión.
""")

st.info("""
🛡️ Adaptive Overcommitment Diagnostic

Este diagnóstico propietario evalúa la **presión estructural de adaptación**
en sistemas automáticos.

Niveles elevados indican posible sobre-reacción a condiciones transitorias,
lo que puede reducir eficiencia operativa y aumentar costos implícitos.

Este diagnóstico no evalúa rentabilidad ni señales.
Evalúa **comportamiento estructural agregado**.

"""
)

with st.sidebar:
    st.header("Configuración")
    comision = st.number_input(
        "Comisión + Spread por trade (USD):",
        min_value=0.0,
        value=15.0,
        step=1.0
    )
#--------------------------------------------------
# 1. LOGICA DE CARGA (CORREGIDA)
# -------------------------------------------------
uploaded_file = st.file_uploader("Suba su archivo CSV", type=["csv"])
if uploaded_file and "upload_id" not in st.session_state:
    st.session_state.cost_per_trade = comision
    st.session_state.upload_id = uuid.uuid4().hex
    st.session_state.file_bytes = uploaded_file.getvalue()
    df = pd.read_csv(uploaded_file)
    # Guardamos la columna de pesos para el gráfico
    col = [c for c in df.columns if "time" not in c.lower()][0]
    st.session_state.columna_pesos = pd.to_numeric(df[col], errors="coerce").fillna(0)
    st.session_state.archivo_cargado = True
    st.rerun()
# -------------------------------------------------
# 2. BOTÓN DE EJECUCIÓN (SOLO SI NO HAY RESULTADOS)
# -------------------------------------------------
if st.session_state.archivo_cargado and not st.session_state.diagnostico_listo:
    if st.button("🚀 Generar Diagnóstico Profesional"):
        with st.spinner("Analizando estructura de adaptación..."):
            files = {"file": ("data.csv", st.session_state.file_bytes, "text/csv")}
            headers = {"x-api-key": API_KEY}
            
            # CORRECCIÓN 1: Hardcoded Value eliminado. Ahora usa la variable 'comision' del input.
            payload = {"cost_per_trade": str(comision)} 

            try:
                response = requests.post(API_URL, files=files, headers=headers, data=payload, timeout=120)
                if response.status_code == 200:
                    st.session_state.result_data = response.json()
                    st.session_state.diagnostico_listo = True
                    st.session_state.csv_uploaded_backend = True
                    st.rerun()
                else:
                    st.error(f"Error en API: {response.status_code}")
            except Exception as e:
                st.error(f"Error de conexión: {e}")

# -------------------------------------------------
# 3. RESULTADOS Y PAGO (PERSISTENTE)
# -------------------------------------------------
if st.session_state.diagnostico_listo:
    res = st.session_state.result_data
    
    st.success("✅ Análisis estructural completado")
    c1, c2, c3 = st.columns(3)
    c1.metric("Activity Level", res["structural_activity"])
    c2.metric("System Status", res["system_status"])
    c3.metric("Efficiency", f"{res['efficiency_band']}%")
    
    st.line_chart(st.session_state.columna_pesos)

    st.markdown("---")
    
    # CORRECCIÓN 2: Checkbox Cosmético -> Checkbox Funcional
    st.subheader("📄 Reporte de Auditoría")
    acepto = st.checkbox("Acepto que este reporte es un diagnóstico matemático y no una recomendación de inversión.")
    
    if acepto:
        # El bloque de pago SOLO se renderiza si el checkbox es True
        pay_url = f"https://ahr-aoc-backend.onrender.com/pagar?upload_id={st.session_state.upload_id}"
        
        st.markdown(f"""
        <div style="background-color:#1e1e1e;padding:25px;border-radius:10px;border:2px solid #2e7d32;text-align:center;margin-top:15px;">
            <h3 style="color:white;margin-bottom:5px;">🛡️ Desbloquear Auditoría Completa</h3>
            <p style="color:#bbb;margin-bottom:20px;">Obtenga el PDF con el mapa de estabilidad y recomendaciones de eficiencia.</p>
            <a href="{pay_url}" target="_blank" style="background-color:#2e7d32;color:white;padding:12px 30px;text-decoration:none;border-radius:5px;font-weight:bold;display:inline-block;transition: 0.3s;">
                PAGAR Y DESCARGAR REPORTE
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Por favor, acepte los términos arriba para habilitar la descarga del reporte completo.")

# ... (Footer y Términos y Condiciones igual)
# -------------------------------------------------
# FOOTER
# -------------------------------------------------
st.markdown("---")
st.caption("""
AOC / AHR Suite v1.1 — Proprietary Structural Diagnostics Framework  
Diagnostic-only. Not investment advice.
""")
st.markdown("---")
st.caption("""
### ⚖️ Términos y Condiciones de Uso - AOC Diagnostic™

**1. Naturaleza del Servicio:** Este portal es una herramienta de diagnóstico estructural y matemático. No constituye, ni debe ser interpretado como, asesoramiento financiero, recomendaciones de inversión, ni señales de compra/venta.

**2. Responsabilidad:** El usuario es el único responsable de las decisiones de inversión o cambios de parámetros que realice en sus algoritmos basándose en este reporte. El desarrollador de AOC Diagnostic™ no se hace responsable por pérdidas financieras resultantes del uso de esta herramienta.

**3. Privacidad:** Los archivos CSV subidos se procesan en memoria y no son almacenados en nuestros servidores tras finalizar la sesión.

**4. Resultados Proyectados:** Los cálculos de "Ahorro Estimado" y "Eficiencia" son proyecciones matemáticas basadas en datos históricos y no garantizan rendimientos futuros.
""")
