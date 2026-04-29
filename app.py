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
# GITHUB
# =========================
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

def obtener_subtipos_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{tipo}"

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
                if item["type"] == "dir"
            ]
    except:
        pass

    return []

# =========================
# VENCIMIENTOS
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
        return "🔴 VENCIDO"
    elif (fecha_vencimiento - hoy).days <= 30:
        return "🟡 POR VENCER"
    else:
        return "🟢 VIGENTE"

# =========================
# BASE
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(base_registros, exist_ok=True)

actividades = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

# =========================
# 📤 CARGA (CORRECTA)
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    tipo = st.selectbox("Tipo", actividades)

    subtipos = obtener_subtipos_github(tipo)

    if not subtipos:
        st.warning("⚠️ No se encontraron subcarpetas en GitHub")
        subtipos = ["otros"]

    subtipo = st.selectbox("Subtipo", subtipos)

    if st.button("Guardar archivo"):

        ruta = os.path.join(base_registros, tipo, subtipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        ok = subir_a_github(
            f"documentos/registros/{tipo}/{subtipo}",
            archivo.name,
            archivo.getbuffer()
        )

        if ok:
            st.success(f"✔ Guardado en {tipo}/{subtipo}")
        else:
            st.warning("⚠ Guardado local OK")

# =========================
# RESTO DEL SISTEMA
# =========================
st.markdown("### 🔎 Búsqueda")

consulta = st.text_input("Buscar actividad")

actividad_sel = None

if consulta:
    for act in actividades:
        if act in consulta.lower():
            actividad_sel = act
            break

    if not actividad_sel:
        actividad_sel = st.selectbox("Elegir:", actividades)

if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    col1, col2 = st.columns(2)

    # BASE
    with col1:
        st.markdown("### 📄 Documentación base")

        carpeta = os.path.join(base_dir, actividad_sel)
        archivos = []

        for root, dirs, files in os.walk(carpeta):
            for file in files:
                if file.endswith(".pdf"):
                    archivos.append((file, os.path.join(root, file), root))

        if not archivos:
            st.warning("⚠️ No hay documentación base")

        # CONTROL INTELIGENTE BASE
        st.markdown("### 📋 Control documentación base")

        criticas = [
            "altura", "excavacion", "izaje",
            "trabajo en caliente", "espacio confinado", "electricidad"
        ]

        if actividad_sel.lower() in criticas:
            requisitos = ["procedimiento", "permiso", "checklist", "emergencia"]
            faltantes = [r for r in requisitos if not any(r in a[0].lower() for a in archivos)]

            if faltantes:
                st.error(f"❌ Faltan: {', '.join(faltantes)}")
            else:
                st.success("✔ Completo")
        else:
            if archivos:
                st.success("✔ Tiene documentación")
            else:
                st.error("❌ Falta documentación")

    # REGISTROS
    with col2:
        st.markdown("### 📊 Estado real (REGISTROS)")

        carpeta_reg = os.path.join(base_registros, actividad_sel)
        archivos_reg = []

        if os.path.exists(carpeta_reg):
            for root, dirs, files in os.walk(carpeta_reg):
                for file in files:
                    if file.endswith(".pdf"):
                        archivos_reg.append(file)

        if actividad_sel.lower() in criticas:
            requisitos = ["permiso", "ats", "checklist"]
            faltantes = [r for r in requisitos if not any(r in a.lower() for a in archivos_reg)]

            if faltantes:
                st.error(f"❌ Faltan: {', '.join(faltantes)}")
            else:
                st.success("✔ Registros completos")
        else:
            if archivos_reg:
                st.success("✔ Tiene registros")
            else:
                st.error("❌ Falta registro")
