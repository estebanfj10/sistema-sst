import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta

# =========================
# 🧱 CONFIG
# =========================
st.set_page_config(
    page_title="Sistema SST",
    page_icon="🦺",
    layout="wide"
)

# =========================
# 🖼️ BANNER
# =========================
if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# 🎨 ESTILOS
# =========================
st.markdown("""
<style>
body {background-color: #eef2f7;}

h1 {color: #1f4e79; font-weight: 700;}
h2, h3 {color: #1f4e79;}

.card {
    background: white;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 12px;
}

.small-text {
    color: gray;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🚀 SUBIR A GITHUB (OPCIONAL)
# =========================
def subir_a_github(ruta, nombre_archivo, contenido):

    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    # 👉 si no hay config, no rompe
    if not token or not repo:
        return "local"

    try:
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre_archivo}"

        contenido_base64 = base64.b64encode(contenido).decode()

        data = {
            "message": f"Subida {nombre_archivo}",
            "content": contenido_base64
        }

        headers = {"Authorization": f"token {token}"}

        r = requests.put(url, json=data, headers=headers)

        if r.status_code in [200, 201]:
            return "github"
        else:
            return "error"

    except:
        return "error"

# =========================
# 🚨 VENCIMIENTOS
# =========================
def evaluar_vencimiento(ruta_archivo, nombre_archivo):

    nombre = nombre_archivo.lower()

    vigencias = {
        "capacitacion": 365,
        "programa": 365,
        "aviso": 180,
        "seguro": 365,
        "vtv": 365,
        "licencia": 365 * 5,
        "apto": 365,
    }

    tipo_detectado = None

    for tipo in vigencias:
        if tipo in nombre:
            tipo_detectado = tipo
            break

    if not tipo_detectado:
        return None

    fecha_archivo = datetime.fromtimestamp(os.path.getmtime(ruta_archivo))
    fecha_vencimiento = fecha_archivo + timedelta(days=vigencias[tipo_detectado])
    hoy = datetime.now()

    if hoy > fecha_vencimiento:
        estado = "🔴 VENCIDO"
    elif (fecha_vencimiento - hoy).days <= 30:
        estado = "🟡 POR VENCER"
    else:
        estado = "🟢 VIGENTE"

    return estado

# =========================
# 📁 BASE LOCAL
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(base_registros, exist_ok=True)

actividades_disponibles = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

if not actividades_disponibles:
    st.warning("⚠️ No hay actividades cargadas en DOCUMENTOS")

# =========================
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo_subido = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo_subido:

    actividad_final = st.selectbox("Actividad", actividades_disponibles)
    tipo_final = st.text_input("Tipo de documento")

    if st.button("Guardar archivo"):

        # 👉 guardado local (SIEMPRE)
        ruta_local = os.path.join(base_registros, actividad_final, tipo_final)
        os.makedirs(ruta_local, exist_ok=True)

        ruta_completa = os.path.join(ruta_local, archivo_subido.name)

        with open(ruta_completa, "wb") as f:
            f.write(archivo_subido.getbuffer())

        # 👉 intento GitHub
        estado = subir_a_github(
            f"documentos/registros/{actividad_final}/{tipo_final}",
            archivo_subido.name,
            archivo_subido.getbuffer()
        )

        if estado == "github":
            st.success("✔ Guardado en GitHub + local")
        elif estado == "local":
            st.success("✔ Guardado local (sin GitHub)")
        else:
            st.warning("⚠️ Guardado local, error en GitHub")

# =========================
# 🔎 BUSCADOR
# =========================
st.markdown("### 🔎 Búsqueda")

consulta = st.text_input("Buscar actividad")

actividad_detectada = None

if consulta:
    for act in actividades_disponibles:
        if act in consulta.lower():
            actividad_detectada = act
            break

    if not actividad_detectada:
        actividad_detectada = st.selectbox("Elegir:", actividades_disponibles)

# =========================
# 📁 DOCUMENTOS
# =========================
if actividad_detectada:

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📄 Documentación base")

    with col2:
        st.markdown("### 📊 Estado registros")

# =========================
# 🚨 ALERTAS
# =========================
st.markdown("---")
st.markdown("## 🚨 Alertas")

alertas = []

for root, dirs, files in os.walk(base_registros):
    for file in files:
        if file.endswith(".pdf"):
            estado = evaluar_vencimiento(os.path.join(root, file), file)
            if estado and ("🔴" in estado or "🟡" in estado):
                alertas.append(f"{estado} - {file}")

if alertas:
    for a in alertas:
        color = "#ff4d4d" if "🔴" in a else "#ffa500"

        st.markdown(f"""
        <div style="background:{color}; padding:10px; border-radius:10px; color:white;">
            {a}
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✔ Sin alertas")

# =========================
# 📊 PANEL
# =========================
st.markdown("---")
st.markdown("## 📊 Panel")

total = len(actividades_disponibles)

docs = sum([
    len(files)
    for _, _, files in os.walk(base_registros)
])

c1, c2 = st.columns(2)

with c1:
    st.markdown(f"<div class='card'>👷 Actividades<br><h2>{total}</h2></div>", unsafe_allow_html=True)

with c2:
    st.markdown(f"<div class='card'>📄 Registros<br><h2>{docs}</h2></div>", unsafe_allow_html=True)

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

for act in actividades_disponibles:
    st.sidebar.markdown(f"📁 **{act}**")
