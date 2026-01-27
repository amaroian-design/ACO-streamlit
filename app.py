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

# Insertar el logo en la barra lateral o en el encabezado
with st.sidebar:
    # Si tienes el archivo de imagen:
    # st.image("logo_aoc.png", width=200) 
    
    # Si quieres usar un título estilizado como logo por ahora:
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

# -------------------------------------------------
# INPUT: CARGA DE ARCHIVO
# -------------------------------------------------
uploaded_file = st.file_uploader("Suba su archivo CSV", type=["csv"])
if uploaded_file is not None and not st.session_state.archivo_cargado:

    upload_id = uuid.uuid4().hex
    st.session_state.upload_id = upload_id

if uploaded_file is not None and not st.session_state.archivo_cargado:
    try:
        st.session_state.file_bytes = uploaded_file.getvalue()
        df_user = pd.read_csv(uploaded_file)
        col = [c for c in df_user.columns if "time" not in c.lower()][0]
        pesos = pd.to_numeric(df_user[col], errors="coerce").fillna(0)

        st.session_state.df_user = df_user
        st.session_state.columna_pesos = pesos
        st.session_state.cambios = pesos.diff().abs() > 1e-5
        st.session_state.archivo_cargado = True

        st.success(f"✅ Archivo cargado correctamente ({len(df_user)} registros).")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
        st.stop()

def upload_csv_to_backend(file_bytes, upload_id):

    files = {
        "file": ("data.csv", file_bytes, "text/csv")
    }

    data = {
        "upload_id": upload_id
    }

    r = requests.post(
        "https://ahr-aoc-backend.onrender.com/upload",
        files=files,
        data=data,
        timeout=60
    )

    return r.status_code == 200

ok = upload_csv_to_backend(
    st.session_state.file_bytes,
    st.session_state.upload_id
)

if ok:
    st.success("Archivo registrado para pago ✅")

# -------------------------------------------------
# BOTÓN DE EJECUCIÓN
# -------------------------------------------------
if st.session_state.archivo_cargado and not st.session_state.diagnostico_listo:
    if st.button("🚀 Generar Diagnóstico Profesional"):
        st.session_state.run_count += 1
        st.session_state.diagnostico_listo = True
        st.rerun()

# -------------------------------------------------
# RESULTADOS (CONTENEDOR AISLADO 🔒) API
# -------------------------------------------------
results_container = st.container()

with results_container:
    if st.session_state.diagnostico_listo:
        pesos = st.session_state.columna_pesos
        level = get_exposure_level()

        try:
            requests.get("https://aoc-diagnostic-api.onrender.com", timeout=90)
            time.sleep(1)
        except:
            pass
        # -----------------------------
        # LLAMADA A LA API
        # -----------------------------
        if st.session_state.run_count > 5:
            st.warning("Usage limit reached for this session.")
            st.stop()

        with st.spinner("🛡️ Initializing secure diagnostic engine..."):
            # Usamos los bytes guardados en el estado
            files = {"file": ("data.csv", st.session_state.file_bytes, "text/csv")}
            headers = {"x-api-key": API_KEY}
            
            # Enviamos el costo como un diccionario simple para que Form lo reciba
            payload = {"cost_per_trade": str(comision)} 
            
            try:
                response = requests.post(
                    API_URL,
                    files=files,
                    headers=headers,
                    data=payload, # <--- Esto ahora coincide con Form en la API
                    timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                else:
                    st.error(f"❌ API error {response.status_code}")
                    st.stop()

            except requests.exceptions.ReadTimeout:
                st.warning("⏳ Diagnostic engine is warming up. Please wait ~30s and try again.")
                st.stop()
            except Exception as e:
                st.error(f"❌ Unexpected connection error: {e}")
                st.stop()

                st.error(f"❌ API error {response.status_code}")
                st.code(response.text)
                st.stop()

        if st.session_state.run_count >= 3:
            st.info("🛡️ Outputs agregados para preservar integridad diagnóstica.")

        # -----------------------------
        # RESULTADOS
        # -----------------------------
        st.subheader("🔍 Structural Activity Overview")

        st.metric(
            "Structural Activity Level",
            result["structural_activity"]
        )

        st.metric(
            "System Status",
            result["system_status"]
        )

        st.metric(
            "Efficiency Band",
            f"{result['efficiency_band']}%"
        )

        st.caption(result["diagnostic_scope"])

        # -----------------------------
        # VISUALIZACIÓN CONTROLADA
        # -----------------------------
        if level == "full":
            st.line_chart(pesos.rename("Decision Trajectory"))
        elif level == "reduced":
            st.info("Visual trajectory omitted (aggregated mode).")
        else:
            st.success("✅ System-level health assessment completed.")

        # -----------------------------
        # DESCARGA DE PDF (CORREGIDO)
        # -----------------------------
        st.markdown("---")
        st.subheader("📄 Diagnostic Report")

        acepto = st.checkbox(
            "I acknowledge this report is diagnostic-only and non-advisory."
        )

        if acepto:
            # Quitamos el 'and st.button' del condicional principal para que el botón de descarga persista
            if st.button("📥 Generate PDF Report"):
                with st.spinner("Generating secure diagnostic report..."):
                    file_bytes = uploaded_file.getvalue()
                    files = {"file": ("data.csv", file_bytes, "text/csv")}
                    headers = {"x-api-key": API_KEY}
                    payload = {"cost_per_trade": comision}

                    try:
                        response = requests.post(
                            API_URL_PDF,
                            files=files,
                            headers=headers,
                            data=payload,
                            timeout=60
                        )

                        if response.status_code == 200:
                            st.success("✅ Report generated!")
                            # El botón de descarga debe estar fuera de cualquier lógica de 'limpieza'
                            st.download_button(
                                label="📩 Click here to Download PDF",
                                data=response.content,
                                file_name="Reporte_AOC.pdf",
                                mime="application/pdf"
                            )
                        else:
                            st.error(f"❌ API error {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

            if st.button("🗑️ Limpiar sesión"):
                reset_session()
                st.rerun()

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
