import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# ESTILOS
# =========================
st.markdown("""
<style>
body {background-color: #eef2f7;}
h1 {color: #1f4e79;}
.card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🔥 FUNCIONES GITHUB
# =========================
def obtener_actividades_github():
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return [
                item["name"]
                for item in data
                if item["type"] == "dir" and item["name"] != "registros"
            ]
    except:
        pass

    return []


def obtener_tipos_github(actividad):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{actividad}"

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    try:
        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            data = r.json()

            carpetas = []
            for item in data:
                if item.get("type") == "dir":
                    carpetas.append(item.get("name"))

            return sorted(carpetas)

        else:
            st.warning(f"GitHub status: {r.status_code}")

    except Exception as e:
        st.error(f"Error GitHub: {e}")

    return []


def subir_a_github(ruta, nombre_archivo, contenido):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return False

    try:
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre_archivo}"

        contenido_base64 = base64.b64encode(contenido).decode()

        data = {
            "message": f"Subida {nombre_archivo}",
            "content": contenido_base64
        }

        headers = {"Authorization": f"token {token}"}

        r = requests.put(url, json=data, headers=headers)

        return r.status_code in [200, 201]

    except:
        return False

# =========================
# VENCIMIENTOS
# =========================
def evaluar_vencimiento(ruta, nombre):
    vigencias = {
        "capacitacion": 365,
        "programa": 365,
        "aviso": 180,
        "seguro": 365,
        "vtv": 365,
        "licencia": 365*5,
        "apto": 365,
    }

    tipo = next((t for t in vigencias if t in nombre.lower()), None)
    if not tipo:
        return None

    fecha = datetime.fromtimestamp(os.path.getmtime(ruta))
    venc = fecha + timedelta(days=vigencias[tipo])

    if datetime.now() > venc:
        return "🔴 VENCIDO"
    elif (venc - datetime.now()).days <= 30:
        return "🟡 POR VENCER"
    else:
        return "🟢 VIGENTE"

# =========================
# BASE LOCAL (no se rompe)
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(base_registros, exist_ok=True)

# =========================
# ACTIVIDADES DESDE GITHUB
# =========================
actividades = obtener_actividades_github()

if not actividades:
    st.warning("⚠️ No se pudieron leer actividades desde GitHub")

# =========================
# 📤 CARGA REGISTROS
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    tipo = st.selectbox(
        "Tipo de registro",
        [
            "ats",
            "permiso",
            "checklist",
            "capacitacion",
            "inspeccion",
            "incidente",
            "mantenimiento"
        ]
    )

    if st.button("Guardar archivo"):

        ruta = os.path.join(base_registros, actividad, tipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        # Guardado local
        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        # Guardado en GitHub
        ok = subir_a_github(
            f"documentos/registros/{actividad}/{tipo}",
            archivo.name,
            archivo.getbuffer()
        )

        if ok:
            st.success("✔ Guardado en GitHub (permanente)")
        else:
            st.warning("⚠ Guardado local OK, pero falló GitHub")

# =========================
# 🔎 BUSCADOR
# =========================
st.markdown("### 🔎 Búsqueda")

actividad_sel = st.selectbox("Seleccionar actividad", actividades)

# =========================
# DOCUMENTACIÓN BASE (local)
# =========================
if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    carpeta = os.path.join(base_dir, actividad_sel)
    archivos = []

    for root, _, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".pdf"):
                archivos.append(f)

    if archivos:
        for f in archivos:
            st.markdown(f"<div class='card'>📄 {f}</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ No hay documentación base")

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

for act in actividades:
    st.sidebar.markdown(f"📁 {act}")
