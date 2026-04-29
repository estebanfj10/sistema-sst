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
# FUNCIONES
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

def subir_archivo(ruta, nombre, contenido):
    if not token or not repo:
        st.error("❌ Falta configurar GITHUB_TOKEN o GITHUB_REPO")
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"

    contenido_base64 = base64.b64encode(contenido).decode()

    data = {
        "message": f"Subida {nombre}",
        "content": contenido_base64
    }

    r = requests.put(url, json=data, headers=headers)

    return r.status_code in [200, 201]

# =========================
# 📂 CARGA REGISTROS
# =========================
st.markdown("## 📂 Cargar Registro")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

actividades_reg = listar_carpetas("documentos/registros")

# 🔥 fallback si GitHub falla
if not actividades_reg:
    actividades_reg = ["excavacion", "altura", "electricidad"]

if archivo:

    actividad = st.selectbox("Actividad", actividades_reg)

    subcarpetas = listar_carpetas(f"documentos/registros/{actividad}")

    if not subcarpetas:
        subcarpetas = ["ats", "permiso", "checklist"]

    tipo = st.selectbox("Carpeta destino", subcarpetas)

    nueva = st.text_input("➕ Nueva carpeta (opcional)")

    if nueva:
        tipo = nueva.lower()

    if st.button("Guardar en REGISTROS"):

        ruta = f"documentos/registros/{actividad}/{tipo}"

        ok = subir_archivo(ruta, archivo.name, archivo.getbuffer())

        if ok:
            st.success(f"✔ Guardado en {actividad}/{tipo}")
        else:
            st.error("❌ No se pudo subir a GitHub")

# =========================
# 🔎 CONSULTA (RECUPERADA)
# =========================
st.markdown("## 🔎 Consulta de documentación")

base_dir = "documentos"

actividades_local = []
if os.path.exists(base_dir):
    actividades_local = [
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
    ]

actividad_sel = st.selectbox("Seleccionar actividad", actividades_local)

if actividad_sel:

    carpeta = os.path.join(base_dir, actividad_sel)

    archivos = []

    for root, _, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".pdf"):
                archivos.append(f)

    if archivos:
        st.markdown("### 📄 Documentación base")
        for f in archivos:
            st.write("📄", f)
    else:
        st.warning("No hay documentos")

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

st.sidebar.markdown("### 📁 Actividades")
for act in actividades_local:
    st.sidebar.markdown(f"📁 {act}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📂 Registros")

registros = listar_carpetas("documentos/registros")

if registros:
    for r in registros:
        st.sidebar.markdown(f"📂 {r}")
else:
    st.sidebar.markdown("⚠️ No se pudieron cargar")
