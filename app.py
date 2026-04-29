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
# 🔥 FUNCIONES GITHUB
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
# BASE
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(base_registros, exist_ok=True)

# =========================
# TIPOS (CARPETAS)
# =========================
tipos = [
    "ats",
    "caliente",
    "electricidad",
    "espacio confinado",
    "excavacion",
    "general",
    "herramientas",
    "izaje"
]

# =========================
# 📤 CARGA REGISTROS
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    tipo = st.selectbox("Tipo", tipos)

    # 🔥 SUBTIPOS DINÁMICOS DESDE GITHUB
    subtipos = obtener_subtipos_github(tipo)

    if not subtipos:
        st.warning("⚠️ No se encontraron subcarpetas en GitHub")
        subtipos = ["otros"]

    subtipo = st.selectbox("Subtipo", subtipos)

    if st.button("Guardar archivo"):

        ruta = os.path.join(base_registros, tipo, subtipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        # LOCAL
        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        # GITHUB
        ok = subir_a_github(
            f"documentos/registros/{tipo}/{subtipo}",
            archivo.name,
            archivo.getbuffer()
        )

        if ok:
            st.success(f"✔ Guardado en {tipo}/{subtipo} (GitHub OK)")
        else:
            st.warning("⚠ Guardado local OK, pero falló GitHub")

# =========================
# 📂 VISUAL REGISTROS
# =========================
st.markdown("## 📂 Registros cargados")

for tipo in tipos:

    carpeta_tipo = os.path.join(base_registros, tipo)

    if os.path.exists(carpeta_tipo):

        st.markdown(f"### 📁 {tipo}")

        for root, dirs, files in os.walk(carpeta_tipo):
            for f in files:
                if f.endswith(".pdf"):
                    st.write("📄", f)

# =========================
# ALERTAS
# =========================
st.markdown("---")
st.markdown("## 🚨 Alertas")

alertas = []

for root, _, files in os.walk(base_registros):
    for f in files:
        if f.endswith(".pdf"):
            estado = evaluar_vencimiento(os.path.join(root, f), f)
            if estado and ("🔴" in estado or "🟡" in estado):
                alertas.append(f"{estado} - {f}")

if alertas:
    for a in alertas:
        st.write(a)
else:
    st.success("✔ Sin alertas")

# =========================
# PANEL
# =========================
st.markdown("---")
st.markdown("## 📊 Panel")

total = len(tipos)
docs = sum(len(files) for _, _, files in os.walk(base_registros))

c1, c2 = st.columns(2)
c1.metric("Tipos", total)
c2.metric("Registros", docs)

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

for t in tipos:
    st.sidebar.markdown(f"📁 {t}")
