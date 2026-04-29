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
.card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

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


def sugerir_tipos_github(actividad):
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
            return [i["name"] for i in data if i["type"] == "dir"]
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

actividades = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

# =========================
# 📤 CARGA (UNIFICADA)
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    # LOCAL
    carpeta_local = os.path.join(base_registros, actividad)
    os.makedirs(carpeta_local, exist_ok=True)

    tipos_locales = [
        d for d in os.listdir(carpeta_local)
        if os.path.isdir(os.path.join(carpeta_local, d))
    ]

    # GITHUB
    tipos_github = sugerir_tipos_github(actividad)

    # UNIFICACIÓN
    tipos = sorted(list(set(tipos_locales + tipos_github)))

    if not tipos:
        tipos = ["permiso", "ats", "checklist"]

    tipo = st.selectbox("Tipo", tipos)

    nuevo = st.text_input("O crear nuevo tipo")

    if nuevo:
        tipo = nuevo.lower().strip()

    if st.button("Guardar archivo"):

        ruta = os.path.join(base_registros, actividad, tipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        ok = subir_a_github(
            f"documentos/registros/{actividad}/{tipo}",
            archivo.name,
            archivo.getbuffer()
        )

        if ok:
            st.success(f"✔ Guardado en {actividad}/{tipo}")
        else:
            st.warning("⚠ Guardado local OK")

# =========================
# 🔎 CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

actividad_sel = st.selectbox("Seleccionar actividad", actividades)

if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    # BASE
    carpeta = os.path.join(base_dir, actividad_sel)
    archivos = []

    for root, _, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".pdf"):
                archivos.append((f, os.path.join(root, f)))

    st.markdown("### 📄 Documentación base")

    if not archivos:
        st.warning("⚠️ No hay documentación base")
    else:
        for nombre, ruta in archivos:
            st.markdown(f"<div class='card'>📄 {nombre}</div>", unsafe_allow_html=True)

    # CONTROL BASE
    st.markdown("### 📋 Control documentación base")

    criticas = [
        "altura","excavacion","izaje",
        "trabajo en caliente","espacio confinado","electricidad"
    ]

    if actividad_sel.lower() in criticas:
        requisitos = ["procedimiento","permiso","checklist","emergencia"]
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
    st.markdown("### 📊 Registros")

    carpeta_reg = os.path.join(base_registros, actividad_sel)
    archivos_reg = []

    if os.path.exists(carpeta_reg):
        for root, _, files in os.walk(carpeta_reg):
            for f in files:
                if f.endswith(".pdf"):
                    archivos_reg.append(f)

    if actividad_sel.lower() in criticas:
        requisitos = ["permiso","ats","checklist"]
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
