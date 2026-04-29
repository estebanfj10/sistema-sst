import streamlit as st
import os
import requests
import base64

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

st.title("🦺 Sistema SST")

# =========================
# GITHUB CONFIG
# =========================
token = st.secrets.get("GITHUB_TOKEN")
repo = st.secrets.get("GITHUB_REPO")

headers = {"Authorization": f"token {token}"} if token else {}

# =========================
# FUNCION LISTAR CARPETAS
# =========================
def listar_carpetas(ruta):
    if not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"

    try:
        r = requests.get(url, headers=headers)

        if r.status_code == 200:
            data = r.json()
            return [item["name"] for item in data if item["type"] == "dir"]
    except:
        pass

    return []

# =========================
# SUBIR ARCHIVO
# =========================
def subir_archivo(ruta, nombre, contenido):
    if not token or not repo:
        st.error("❌ Falta GITHUB_TOKEN o GITHUB_REPO")
        return

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"

    contenido_base64 = base64.b64encode(contenido).decode()

    data = {
        "message": f"Subida {nombre}",
        "content": contenido_base64
    }

    r = requests.put(url, json=data, headers=headers)

    if r.status_code in [200, 201]:
        st.success("✔ Archivo subido correctamente")
    else:
        st.error(f"❌ Error GitHub: {r.status_code}")

# =========================
# 📂 CARGA DE REGISTROS
# =========================
st.markdown("## 📂 Cargar Registro")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

# 🔥 ACTIVIDADES DESDE GITHUB
actividades_reg = listar_carpetas("documentos/registros")

if archivo and actividades_reg:

    actividad = st.selectbox("Actividad", actividades_reg)

    # 🔥 SUBCARPETAS
    subcarpetas = listar_carpetas(f"documentos/registros/{actividad}")

    if not subcarpetas:
        subcarpetas = ["(sin carpetas)"]

    tipo = st.selectbox("Carpeta destino", subcarpetas)

    nueva = st.text_input("➕ Nueva carpeta (opcional)")

    if nueva:
        tipo = nueva.lower()

    if st.button("Guardar en REGISTROS"):

        ruta_final = f"documentos/registros/{actividad}/{tipo}"

        subir_archivo(ruta_final, archivo.name, archivo.getbuffer())

# =========================
# 📁 SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

# ACTIVIDADES (documentos base)
st.sidebar.markdown("### 📁 Actividades")

base_dir = "documentos"

if os.path.exists(base_dir):
    actividades_local = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
    ]

    for act in actividades_local:
        st.sidebar.markdown(f"📁 {act}")

# REGISTROS DESDE GITHUB
st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Registros")

registros = listar_carpetas("documentos/registros")

if registros:
    for r in registros:
        st.sidebar.markdown(f"📂 {r}")
else:
    st.sidebar.markdown("⚠️ No se pudieron cargar")
