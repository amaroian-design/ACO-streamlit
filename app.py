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
            payload = {
                "cost_per_trade": str(comision),
                "upload_id": st.session_state.upload_id  # <--- ESTA LÍNEA FALTA
            }
            try:
                response = requests.post(API_URL, files=files, headers=headers, data=payload, timeout=120)

                st.write(f"Código de respuesta del servidor: {response.status_code}")
                st.write(f"Contenido: {response.text}")
                
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
# 3. RESULTADOS Y PAGO (CON LOGICA DE REGISTRO OBLIGATORIO)
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
    st.subheader("📄 Reporte de Auditoría")
    
    # PASO 1: Aceptar términos
    acepto = st.checkbox("Acepto que este reporte es un diagnóstico matemático.")

    if acepto:
        # PASO 2: Verificar si el usuario está logueado
        if "jwt" not in st.session_state:
            st.warning("👋 ¡Casi listo! Para procesar tu pago y enviarte el PDF, por favor inicia sesión o regístrate.")
            
            tab1, tab2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
            
            with tab1:
                email_l = st.text_input("Email", key="login_email")
                pass_l = st.text_input("Password", type="password", key="login_pass")
                if st.button("Entrar y Continuar"):
                    # Llamada a tu API de login
                    r = requests.post(f"{API_URL.replace('/upload','')}/auth/login", 
                                     json={"email": email_l.lower(), "password": pass_l})
                    if r.status_code == 200:
                        st.session_state.jwt = r.json()["token"]
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")

            with tab2:
                email_r = st.text_input("Nuevo Email", key="reg_email")
                pass_r = st.text_input("Nueva Contraseña", type="password", key="reg_pass")
                if st.button("Registrarse y Continuar"):
                    r = requests.post(f"{API_URL.replace('/upload','')}/auth/register", 
                                     json={"email": email_r.lower(), "password": pass_r})
                    if r.status_code == 201:
                        st.session_state.jwt = r.json()["token"]
                        st.success("¡Cuenta creada!")
                        st.rerun()
                    else:
                        st.error("Error al crear cuenta (quizás ya existe)")
        
        else:
            # PASO 3: Usuario ya está logueado, mostramos botón de pago
            pay_url = f"https://ahr-aoc-backend.onrender.com/api/create-checkout?upload_id={st.session_state.upload_id}"
            
            # Obtenemos el email del estado o de una variable segura
            display_email = st.session_state.get('login_email', 'Usuario Autenticado')

            st.markdown(f"""
            <div style="background-color:#1e1e1e;padding:25px;border-radius:10px;border:2px solid #2e7d32;text-align:center;">
                <h3 style="color:white;margin-bottom:10px;">🛡️ Auditoría Completa Lista</h3>
                <p style="color:#22c55e; font-weight:bold; margin-bottom:20px;">Sesión activa: {display_email}</p>
                <a href="{pay_url}" target="_blank" style="background-color:#2e7d32;color:white;padding:14px 40px;text-decoration:none;border-radius:8px;font-weight:bold;display:inline-block;box-shadow: 0 4px 15px rgba(46,125,50,0.3);">
                    PAGAR Y DESCARGAR REPORTE 💳
                </a>
            </div>
            """, unsafe_allow_html=True)
            st.balloons()
            st.info("💡 Haz clic en el botón de arriba. Se abrirá la pasarela segura de Stripe en una nueva pestaña.")
    else:
        st.info("💡 Por favor, acepte los términos arriba para habilitar la descarga.")
        
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
