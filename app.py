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
h1, h2, h3 {color: #1f4e79;}

.card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    margin-bottom: 10px;
}

.small-text {
    color: gray;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# GITHUB CONFIG
# =========================
token = st.secrets.get("GITHUB_TOKEN")
repo = st.secrets.get("GITHUB_REPO")

# =========================
# FUNCION: LEER CARPETAS GITHUB
# =========================
def obtener_tipos_desde_github(actividad):
    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{actividad}"
    headers = {"Authorization": f"token {token}"}

    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return [item["name"] for item in data if item["type"] == "dir"]
    except:
        return []

    return []

# =========================
# FUNCION SUBIR GITHUB
# =========================
def subir_a_github(ruta, nombre_archivo, contenido):
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
    nombre = nombre.lower()

    vigencias = {
        "capacitacion": 365,
        "aviso": 180,
        "seguro": 365,
        "vtv": 365,
        "licencia": 365*5,
        "apto": 365
    }

    tipo = next((t for t in vigencias if t in nombre), None)
    if not tipo:
        return None

    fecha = datetime.fromtimestamp(os.path.getmtime(ruta))
    venc = fecha + timedelta(days=vigencias[tipo])
    hoy = datetime.now()

    if hoy > venc:
        return "🔴 VENCIDO"
    elif (venc - hoy).days <= 30:
        return "🟡 POR VENCER"
    return "🟢 VIGENTE"

# =========================
# BASE
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_registros, exist_ok=True)

actividades = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

# =========================
# CARGA
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    tipos_base = ["ats", "permiso", "checklist"]

    tipos_github = obtener_tipos_desde_github(actividad)

    tipos = sorted(list(set(tipos_base + tipos_github)))

    tipo = st.selectbox("Tipo de registro", tipos)

    nuevo_tipo = st.text_input("➕ Crear nuevo tipo")

    if nuevo_tipo:
        tipo = nuevo_tipo.lower()

    if st.button("Guardar archivo"):

        # LOCAL
        ruta_local = os.path.join(base_registros, actividad, tipo)
        os.makedirs(ruta_local, exist_ok=True)

        ruta_archivo = os.path.join(ruta_local, archivo.name)

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        # GITHUB
        subir_a_github(
            f"documentos/registros/{actividad}/{tipo}",
            archivo.name,
            archivo.getbuffer()
        )

        st.success(f"✔ Guardado en {actividad}/{tipo}")

# =========================
# BUSCAR
# =========================
st.markdown("### 🔎 Buscar actividad")

consulta = st.text_input("")

actividad_sel = None

if consulta:
    for act in actividades:
        if act in consulta.lower():
            actividad_sel = act
            break

    if not actividad_sel:
        actividad_sel = st.selectbox("Seleccionar:", actividades)

# =========================
# DOCUMENTACION
# =========================
if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    col1, col2 = st.columns(2)

    # BASE
    with col1:
        st.markdown("### 📄 Documentación base")

        carpeta = os.path.join(base_dir, actividad_sel)
        archivos = []

        for root, _, files in os.walk(carpeta):
            for f in files:
                if f.endswith(".pdf"):
                    archivos.append((f, os.path.join(root, f)))

        if not archivos:
            st.warning("⚠️ No hay documentación base")
        else:
            for nombre, ruta in archivos:
                st.markdown(f"<div class='card'>📄 {nombre}</div>", unsafe_allow_html=True)

        requisitos = ["procedimiento", "permiso", "checklist", "emergencia"]
        faltantes = [r for r in requisitos if not any(r in a[0].lower() for a in archivos)]

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Completo")

    # REGISTROS
    with col2:
        st.markdown("### 📊 Registros")

        requisitos = ["ats", "permiso", "checklist"]
        faltantes = []

        carpeta_reg = os.path.join(base_registros, actividad_sel)

        for r in requisitos:
            ok = False
            if os.path.exists(carpeta_reg):
                for root, _, files in os.walk(carpeta_reg):
                    if any(r in f.lower() for f in files):
                        ok = True
            if not ok:
                faltantes.append(r)

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Registros completos")

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Actividades")

for act in actividades:
    st.sidebar.markdown(f"📁 {act}")
