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
.small-text {
    color: gray;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🔥 GITHUB
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
            return [item["name"] for item in data if item["type"] == "dir"]
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
# TIPOS
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
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    tipo = st.selectbox("Tipo", tipos)

    subtipos = obtener_subtipos_github(tipo)

    if not subtipos:
        st.warning("⚠️ No hay subcarpetas en GitHub")
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
            st.success(f"✔ Guardado en {tipo}/{subtipo} (GitHub OK)")
        else:
            st.warning("⚠ Guardado local OK, pero falló GitHub")

# =========================
# 🔎 CONSULTA COMPLETA
# =========================
st.markdown("---")
st.markdown("## 🔎 Consulta de documentación")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

if tipo_sel:

    st.markdown(f"## 📁 {tipo_sel.upper()}")

    # -------------------------
    # BASE
    # -------------------------
    st.markdown("### 📄 Documentación base")

    carpeta_base = os.path.join(base_dir, tipo_sel)
    archivos_base = []

    if os.path.exists(carpeta_base):
        for root, dirs, files in os.walk(carpeta_base):
            for f in files:
                if f.endswith(".pdf"):
                    archivos_base.append((f, root))

    if not archivos_base:
        st.warning("⚠️ No hay documentación base")
    else:
        for nombre, ruta in archivos_base:

            st.markdown(f"<div class='card'>📄 <b>{nombre}</b></div>", unsafe_allow_html=True)

            with open(os.path.join(ruta, nombre), "rb") as f:
                st.download_button("📥 Descargar", f, file_name=nombre)

    # CONTROL BASE
    st.markdown("### 📋 Control documentación base")

    requisitos_base = ["procedimiento", "permiso", "checklist"]

    faltantes_base = [
        r for r in requisitos_base
        if not any(r in a[0].lower() for a in archivos_base)
    ]

    if faltantes_base:
        st.error(f"❌ Faltan: {', '.join(faltantes_base)}")
    else:
        st.success("✔ Documentación base completa")

    # -------------------------
    # REGISTROS
    # -------------------------
    st.markdown("### 📄 Registros cargados")

    carpeta_reg = os.path.join(base_registros, tipo_sel)
    archivos_reg = []

    if os.path.exists(carpeta_reg):
        for root, dirs, files in os.walk(carpeta_reg):
            for f in files:
                if f.endswith(".pdf"):
                    archivos_reg.append((f, root))

    if not archivos_reg:
        st.warning("⚠️ No hay registros cargados")
    else:
        for nombre, ruta in archivos_reg:

            subtipo = os.path.basename(ruta)

            st.markdown(f"""
            <div class="card">
                📄 <b>{nombre}</b><br>
                <span class="small-text">Subtipo: {subtipo}</span>
            </div>
            """, unsafe_allow_html=True)

    # CONTROL REGISTROS
    st.markdown("### 📋 Control de registros")

    requisitos = ["ats", "permiso", "checklist"]

    faltantes = [
        r for r in requisitos
        if not any(r in a[0].lower() for a in archivos_reg)
    ]

    if faltantes:
        st.error(f"❌ Faltan: {', '.join(faltantes)}")
    else:
        st.success("✔ Registros completos")

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
