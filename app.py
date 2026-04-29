import streamlit as st
import os
import requests
import base64

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", layout="wide")
st.title("🦺 Sistema SST")

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


def obtener_subtipos_github(actividad):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{actividad}"

    headers = {"Authorization": f"token {token}"}

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
# BASE
# =========================
base_dir = "documentos"
reg_dir = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(reg_dir, exist_ok=True)

actividades = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

# =========================
# 📤 CARGA (SOLO ESTO CAMBIA)
# =========================
st.markdown("## 📤 Cargar registro")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    # 🔥 ESTE ES EL BLOQUE QUE FUNCIONABA
    subtipos = obtener_subtipos_github(actividad)

    if not subtipos:
        st.warning("⚠️ No se encontraron subcarpetas en GitHub")
        subtipos = ["otros"]

    subtipo = st.selectbox("Subtipo", subtipos)

    if st.button("Guardar"):

        ruta = os.path.join(reg_dir, actividad, subtipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

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
# 🔎 CONSULTA (NO SE TOCA)
# =========================
st.markdown("## 🔎 Consulta")

act_sel = st.selectbox("Seleccionar actividad", actividades)

if act_sel:

    st.markdown(f"### 📁 {act_sel}")

    # BASE
    base_path = os.path.join(base_dir, act_sel)

    archivos_base = []
    for root, _, files in os.walk(base_path):
        for f in files:
            if f.endswith(".pdf"):
                archivos_base.append((f, os.path.join(root, f)))

    st.markdown("### 📄 Base")

    if not archivos_base:
        st.warning("Sin base")
    else:
        for nombre, ruta in archivos_base:
            st.write(nombre)

            with open(ruta, "rb") as f:
                st.download_button(
                    "Descargar",
                    f,
                    file_name=nombre,
                    key=f"base_{nombre}"
                )

    # REGISTROS (ESTE ERA EL QUE FUNCIONABA BIEN)
    st.markdown("### 📄 Registros")

    reg_path = os.path.join(reg_dir, act_sel)

    registros = {}

    if os.path.exists(reg_path):
        for root, _, files in os.walk(reg_path):
            for f in files:
                if f.endswith(".pdf"):

                    subtipo = os.path.basename(root)

                    registros.setdefault(subtipo, []).append((f, root))

    if not registros:
        st.warning("Sin registros")
    else:
        for sub, archivos in registros.items():
            st.write("📁", sub)

            for nombre, ruta in archivos:
                st.write(" -", nombre)
        
