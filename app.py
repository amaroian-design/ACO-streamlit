import streamlit as st
import pandas as pd
import requests
import os
import time
import uuid

# 1. CONFIGURACIÓN Y SECRETOS
st.set_page_config(page_title="AOC Diagnostic Portal", page_icon="🛡️")

API_URL = st.secrets["API_URL"]
API_KEY = st.secrets["API_KEY"]

# 2. INICIALIZACIÓN DE ESTADO (Anti-Caos)
if "jwt" not in st.session_state:
    st.session_state.jwt = None

def init_diagnostic_state():
    defaults = {
        "diagnostico_listo": False,
        "archivo_cargado": False,
        "columna_pesos": None,
        "upload_id": None,
        "result_data": None,
        "file_bytes": None,
        "run_count": 0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_diagnostic_state()

# 3. ESTILOS CSS PROFESIONALES
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 6px; height: 3em; background-color: #2e7d32; color: white; font-weight: bold; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    h1 { font-family: sans-serif; }
</style>
""", unsafe_allow_html=True)

# 4. FUNCIONES AUXILIARES RESCATADAS
def classify_activity(x):
    if x < 0.05: return "Low"
    elif x < 0.15: return "Moderate"
    elif x < 0.35: return "High"
    else: return "Critical"

# 5. NAVEGACIÓN LATERAL
with st.sidebar:
    st.markdown("<h1 style='color: #2e7d32;'>🛡️ AOC Diagnostic</h1>", unsafe_allow_html=True)
    st.divider()
    
    if st.session_state.jwt:
        menu = st.radio("🏠 Menú Principal", ["🚀 Nuevo Diagnóstico", "📂 Mis Reportes", "🔒 Cerrar Sesión"])
    else:
        menu = st.radio("🏠 Menú Principal", ["🚀 Nuevo Diagnóstico", "🔐 Login / Registro"])
    
    st.divider()
    st.header("⚙️ Configuración")
    comision = st.number_input("Comisión + Spread por trade (USD):", min_value=0.0, value=15.0, step=1.0)

# 6. LÓGICA DE PANTALLAS
if menu == "🔒 Cerrar Sesión":
    st.session_state.jwt = None
    st.rerun()

elif menu == "🔐 Login / Registro":
    st.title("🔐 Acceso al Portal")
    t1, t2 = st.tabs(["Iniciar Sesión", "Crear Cuenta"])
    
    with t1:
        e_l = st.text_input("Email", key="l_email").lower()
        p_l = st.text_input("Password", type="password", key="l_pass")
        if st.button("Entrar y Continuar"):
            r = requests.post(f"{API_URL.replace('/upload','')}/auth/login", json={"email": e_l, "password": p_l})
            if r.status_code == 200:
                st.session_state.jwt = r.json()["token"]
                st.success("¡Sesión iniciada!")
                st.rerun()
            else: st.error("Credenciales incorrectas")

    with t2:
        e_r = st.text_input("Nuevo Email", key="r_email").lower()
        p_r = st.text_input("Nueva Contraseña", type="password", key="r_pass")
        if st.button("Registrarse"):
            r = requests.post(f"{API_URL.replace('/upload','')}/auth/register", json={"email": e_r, "password": p_r})
            if r.status_code == 201:
                st.success("¡Cuenta creada! Por favor inicia sesión.")
            else: st.error("Error al registrar (el usuario ya existe).")

elif menu == "📂 Mis Reportes":
    st.title("📂 Mis Auditorías Compradas")
    if not st.session_state.jwt:
        st.warning("⚠️ Por favor, inicia sesión para ver tus reportes guardados.")
    else:
        headers = {"Authorization": f"Bearer {st.session_state.jwt}"}
        try:
            r = requests.get(f"{API_URL.replace('/upload','')}/api/my-reports", headers=headers)
            if r.status_code == 200:
                reports = r.json()
                if not reports: st.info("Aún no tienes reportes comprados.")
                # Busca esta parte en tu código y asegúrate de que use link_button correctamente
                for rep in reports:
                    col1, col2 = st.columns([3, 1])
                    col1.markdown(f"🗓️ **Fecha:** {rep['created_at']}  \n💰 **Inversión:** ${rep['amount']} USD")
                    if rep['url']: 
                        col2.link_button("📄 Descargar", rep['url'], help="Haz clic para descargar tu auditoría")
                    st.divider()
            else: st.error("Error al obtener reportes.")
        except: st.error("Error de conexión con el servidor.")

elif menu == "🚀 Nuevo Diagnóstico":
    st.title("🛡️ AOC / AHR: Portal de Auditoría")
    
    st.info("**AOC Diagnostic™**: Evaluación de presión estructural de adaptación. No provee señales de inversión.")

    # 1. LOGICA DE CARGA
    uploaded_file = st.file_uploader("Suba su archivo CSV de operaciones", type=["csv"])
    
    if uploaded_file and not st.session_state.archivo_cargado:
        st.session_state.upload_id = uuid.uuid4().hex
        st.session_state.file_bytes = uploaded_file.getvalue()
        df = pd.read_csv(uploaded_file)
        # Identificar columna de datos (la primera que no sea tiempo)
        col = [c for c in df.columns if "time" not in c.lower()][0]
        st.session_state.columna_pesos = pd.to_numeric(df[col], errors="coerce").fillna(0)
        st.session_state.archivo_cargado = True
        st.rerun()

    # 2. BOTÓN DE EJECUCIÓN 
    if st.session_state.archivo_cargado and not st.session_state.diagnostico_listo:
        if st.button("🚀 Generar Diagnóstico Profesional"):
            with st.spinner("Analizando estructura de adaptación..."):
                files = {"file": ("data.csv", st.session_state.file_bytes, "text/csv")}
                data = {"cost_per_trade": str(comision), "upload_id": st.session_state.upload_id}
                try:
                    r = requests.post(API_URL, files=files, data=data, headers={"x-api-key": API_KEY}, timeout=120)
                    if r.status_code == 200:
                        st.session_state.result_data = r.json()
                        st.session_state.diagnostico_listo = True
                        st.rerun()
                    else: st.error(f"Error en API: {r.text}")
                except Exception as e: st.error(f"Error de conexión: {e}")

    # 3. RESULTADOS
    if st.session_state.diagnostico_listo:
        res = st.session_state.result_data
        st.success("✅ Análisis estructural completado")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Activity Level", res["structural_activity"])
        c2.metric("System Status", res["system_status"])
        c3.metric("Efficiency", f"{res['efficiency_band']}%")
        
        st.line_chart(st.session_state.columna_pesos)

        # 4. BLOQUE DE PAGO SEGURO
        st.markdown("---")
        st.subheader("📄 Obtener Reporte de Auditoría Full")
        acepto = st.checkbox("Acepto que este reporte es un diagnóstico matemático estructural.")

        if acepto:
            if not st.session_state.jwt:
                st.warning("👋 ¡Casi listo! Inicia sesión en el menú lateral para procesar tu pago y recibir el PDF.")
            else:
                email_para_stripe = st.session_state.get('l_email') or st.session_state.get('r_email')
                pay_url = f"https://ahr-aoc-backend.onrender.com/api/create-checkout?upload_id={st.session_state.upload_id}&email={email_para_stripe}"
                st.markdown(f"""
                <div style="background-color:#1e1e1e;padding:25px;border-radius:10px;border:2px solid #2e7d32;text-align:center;">
                    <h3 style="color:white;margin-bottom:10px;">🛡️ Auditoría Completa Lista</h3>
                    <p style="color:#22c55e; font-weight:bold; margin-bottom:20px;">Sesión activa: Lista para procesar</p>
                    <a href="{pay_url}" target="_blank" style="background-color:#2e7d32;color:white;padding:14px 40px;text-decoration:none;border-radius:8px;font-weight:bold;display:inline-block;">
                        PAGAR Y DESCARGAR REPORTE 💳
                    </a>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
        else:
            st.info("💡 Por favor, acepte los términos arriba para habilitar la pasarela de pago.")

# 7. FOOTER LEGAL (SIEMPRE VISIBLE)
st.markdown("---")
st.caption("AOC / AHR Suite v1.1 — Proprietary Structural Diagnostics Framework")
with st.expander("⚖️ Términos y Condiciones de Uso"):
    st.caption("""
    **1. Naturaleza:** Diagnóstico estructural matemático. No es asesoramiento financiero.
    **2. Responsabilidad:** El desarrollador no se hace responsable por pérdidas financieras.
    **3. Privacidad:** Los CSV se procesan en memoria y no se almacenan permanentemente sin pago.
    **4. Proyecciones:** Los cálculos son proyecciones basadas en datos históricos.
    """)

