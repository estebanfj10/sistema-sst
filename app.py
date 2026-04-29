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
# GITHUB CONFIG
# =========================
token = st.secrets.get("GITHUB_TOKEN")
repo = st.secrets.get("GITHUB_REPO")

# =========================
# FUNCIONES GITHUB
# =========================
def obtener_carpetas_github(ruta):
    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
    headers = {"Authorization": f"token {token}"}

    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            return [item["name"] for item in data if item["type"] == "dir"]
    except:
        pass

    return []

def subir_a_github(ruta, nombre, contenido):
    if not token or not repo:
        return False

    try:
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
        contenido_base64 = base64.b64encode(contenido).decode()

        data = {
            "message": f"Subida {nombre}",
            "content": contenido_base64
        }

        headers = {"Authorization": f"token {token}"}
        r = requests.put(url, json=data, headers=headers)

        return r.status_code in [200, 201]
    except:
        return False

# =========================
# BASE LOCAL
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_registros, exist_ok=True)

actividades = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

# =========================
# 📂 CARGA REGISTROS (CORRECTA)
# =========================
st.markdown("## 📂 Cargar REGISTRO")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    # 🔥 ACTIVIDADES DE REGISTROS DESDE GITHUB
    actividades_reg = obtener_carpetas_github("documentos/registros")

    if not actividades_reg:
        actividades_reg = actividades  # fallback

    actividad = st.selectbox("Actividad (REGISTROS)", actividades_reg)

    # 🔥 SUBCARPETAS REALES
    tipos = obtener_carpetas_github(f"documentos/registros/{actividad}")

    if not tipos:
        tipos = ["ats", "permiso", "checklist"]

    tipo = st.selectbox("Carpeta destino", tipos)

    nuevo_tipo = st.text_input("➕ Crear nueva carpeta (opcional)")

    if nuevo_tipo:
        tipo = nuevo_tipo.lower()

    if st.button("Guardar en REGISTROS"):

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

        st.success(f"✔ Guardado en REGISTROS/{actividad}/{tipo}")

# =========================
# 🔎 BUSCADOR
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
# DOCUMENTACIÓN BASE + CONTROL
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
                    archivos.append(f)

        if not archivos:
            st.warning("⚠️ No hay documentación base")
        else:
            for f in archivos:
                st.write("📄", f)

        requisitos = ["procedimiento", "permiso", "checklist", "emergencia"]
        faltantes = [r for r in requisitos if not any(r in a.lower() for a in archivos)]

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Documentación completa")

    # REGISTROS
    with col2:
        st.markdown("### 📊 Estado registros")

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
