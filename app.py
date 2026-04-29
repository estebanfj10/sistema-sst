import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# GITHUB
# =========================
def subir_a_github(ruta, nombre, contenido):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    data = {
        "message": f"Subida {nombre}",
        "content": contenido_base64
    }

    headers = {"Authorization": f"token {token}"}
    r = requests.put(url, json=data, headers=headers)

    return r.status_code in [200, 201]

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
# 📤 CARGA (ESTABLE)
# =========================
st.markdown("## 📤 Cargar registro")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    # 🔹 SUBCARPETAS REALES (LOCAL)
    carpeta_act = os.path.join(base_registros, actividad)
    os.makedirs(carpeta_act, exist_ok=True)

    subcarpetas = [
        d for d in os.listdir(carpeta_act)
        if os.path.isdir(os.path.join(carpeta_act, d))
    ]

    if not subcarpetas:
        subcarpetas = ["general"]

    subtipo = st.selectbox("Subtipo", subcarpetas)

    if st.button("Guardar"):

        ruta = os.path.join(base_registros, actividad, subtipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        # LOCAL
        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        # GITHUB
        ok = subir_a_github(
            f"documentos/registros/{actividad}/{subtipo}",
            archivo.name,
            archivo.getbuffer()
        )

        if ok:
            st.success("✔ Guardado en GitHub")
        else:
            st.warning("⚠ Guardado solo local")

# =========================
# 🔎 CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

actividad_sel = st.selectbox("Seleccionar actividad", actividades)

if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    # =========================
    # BASE
    # =========================
    carpeta = os.path.join(base_dir, actividad_sel)
    archivos_base = []

    for root, _, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".pdf"):
                archivos_base.append((f, os.path.join(root, f)))

    st.markdown("### 📄 Documentación base")

    if not archivos_base:
        st.warning("⚠️ No hay documentación base")
    else:
        for nombre, ruta in archivos_base:

            st.write("📄", nombre)

            with open(ruta, "rb") as f:
                st.download_button(
                    label=f"Descargar {nombre}",
                    data=f,
                    file_name=nombre,
                    key=nombre
                )

    # =========================
    # REGISTROS
    # =========================
    st.markdown("### 📄 Registros")

    carpeta_reg = os.path.join(base_registros, actividad_sel)

    if os.path.exists(carpeta_reg):

        for root, dirs, files in os.walk(carpeta_reg):
            for f in files:
                if f.endswith(".pdf"):
                    subtipo = os.path.basename(root)
                    st.write(f"📁 {subtipo} → {f}")
