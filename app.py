import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

# 🔥 BANNER
st.image("banner.png", use_container_width=True)

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# GITHUB
# =========================
def subir_a_github(ruta, nombre, contenido):
    token = st.secrets.get("GITHUB_TOKEN", None)
    repo = st.secrets.get("GITHUB_REPO", None)

    if not token or not repo:
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    data = {"message": f"Subida {nombre}", "content": contenido_base64}
    headers = {"Authorization": f"token {token}"}

    r = requests.put(url, json=data, headers=headers)
    return r.status_code in [200, 201]


def obtener_subtipos_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN", None)
    repo = st.secrets.get("GITHUB_REPO", None)

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{tipo}"
    headers = {"Authorization": f"token {token}"}

    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return [i["name"] for i in r.json() if i["type"] == "dir"]
    except:
        pass

    return []


def obtener_tipos_github():
    token = st.secrets.get("GITHUB_TOKEN", None)
    repo = st.secrets.get("GITHUB_REPO", None)

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros"
    headers = {"Authorization": f"token {token}"}

    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return [i["name"] for i in r.json() if i["type"] == "dir"]
    except:
        pass

    return []

# =========================
# VENCIMIENTOS
# =========================
def evaluar_vencimiento(ruta, nombre):
    reglas = {
        "capacitacion":365,
        "seguro":365,
        "vtv":365,
        "licencia":365*5
    }

    tipo = next((t for t in reglas if t in nombre.lower()), None)
    if not tipo:
        return None

    fecha = datetime.fromtimestamp(os.path.getmtime(ruta))
    venc = fecha + timedelta(days=reglas[tipo])

    if datetime.now() > venc:
        return "🔴 VENCIDO"
    elif (venc - datetime.now()).days <= 30:
        return "🟡 POR VENCER"
    return "🟢 VIGENTE"

# =========================
# BASE
# =========================
base_dir = "documentos"
reg_dir = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(reg_dir, exist_ok=True)

# =========================
# TIPOS AUTOMÁTICOS
# =========================
tipos = []

if os.path.exists(reg_dir):
    tipos += [
        d for d in os.listdir(reg_dir)
        if os.path.isdir(os.path.join(reg_dir, d))
    ]

tipos += obtener_tipos_github()
tipos = sorted(list(set(tipos)))

if not tipos:
    tipos = ["general"]

# =========================
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)

    subtipos = obtener_subtipos_github(tipo)
    if not subtipos:
        subtipos = ["otros"]

    subtipo = st.selectbox("Subtipo", subtipos)

    if st.button("Guardar"):
        ruta = os.path.join(reg_dir, tipo, subtipo)
        os.makedirs(ruta, exist_ok=True)

        path = os.path.join(ruta, archivo.name)

        with open(path, "wb") as f:
            f.write(archivo.getbuffer())

        subir_a_github(
            f"documentos/registros/{tipo}/{subtipo}",
            archivo.name,
            archivo.getbuffer()
        )

        st.success("✔ Guardado")

# =========================
# 🔎 CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

# BASE
st.markdown("### 📄 Documentación base")

carpeta_base = os.path.join(base_dir, tipo_sel)
archivos_base = []

if os.path.exists(carpeta_base):
    for root, _, files in os.walk(carpeta_base):
        for f in files:
            if f.endswith(".pdf"):
                archivos_base.append((f, os.path.join(root, f)))

if not archivos_base:
    st.warning("⚠️ No hay documentación base")
else:
    for nombre, ruta in archivos_base:
        st.write(f"📄 {nombre}")
        with open(ruta, "rb") as f:
            st.download_button(f"📥 Descargar {nombre}", f, file_name=nombre)

# REGISTROS
st.markdown("### 📊 Registros")

carpeta_reg = os.path.join(reg_dir, tipo_sel)
archivos_reg = []

if os.path.exists(carpeta_reg):
    for root, _, files in os.walk(carpeta_reg):
        for f in files:
            if f.endswith(".pdf"):
                archivos_reg.append((f, os.path.join(root, f)))

if not archivos_reg:
    st.warning("⚠️ No hay registros")
else:
    for nombre, ruta in archivos_reg:
        subtipo = os.path.basename(os.path.dirname(ruta))
        st.write(f"📁 {subtipo} → {nombre}")
        with open(ruta, "rb") as f:
            st.download_button(f"📥 Descargar {nombre}", f, file_name=nombre)

# =========================
# CONTROL
# =========================
criticos = [
    "altura","excavacion","izaje",
    "trabajo en caliente","espacio confinado","electricidad"
]

# =========================
# DASHBOARD
# =========================
st.markdown("---")
st.markdown("## 📊 Dashboard SST")

total = len(tipos)
ok = 0
parcial = 0
critico = 0

for tipo in tipos:

    base_files = []
    reg_files = []

    carpeta_base = os.path.join(base_dir, tipo)
    if os.path.exists(carpeta_base):
        for _, _, files in os.walk(carpeta_base):
            base_files += [f for f in files if f.endswith(".pdf")]

    carpeta_reg = os.path.join(reg_dir, tipo)
    if os.path.exists(carpeta_reg):
        for _, _, files in os.walk(carpeta_reg):
            reg_files += [f for f in files if f.endswith(".pdf")]

    estado = "OK"

    if tipo in criticos:

        req_base = ["procedimiento","permiso","checklist","emergencia"]
        falt_base = [r for r in req_base if not any(r in f.lower() for f in base_files)]

        req_reg = ["permiso","ats","checklist"]
        falt_reg = [r for r in req_reg if not any(r in f.lower() for f in reg_files)]

        if not base_files and not reg_files:
            estado = "CRITICO"
        elif falt_base or falt_reg:
            estado = "PARCIAL"

    else:
        if not base_files and not reg_files:
            estado = "CRITICO"
        elif not base_files or not reg_files:
            estado = "PARCIAL"

    if estado == "OK":
        ok += 1
    elif estado == "PARCIAL":
        parcial += 1
    else:
        critico += 1

# MÉTRICAS
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", total)
c2.metric("🟢 OK", ok)
c3.metric("🟡 Parcial", parcial)
c4.metric("🔴 Crítico", critico)

# GRÁFICO
st.markdown("### 📊 Distribución de estados")

data_chart = {
    "Estado": ["OK", "Parcial", "Crítico"],
    "Cantidad": [ok, parcial, critico]
}

st.bar_chart(data_chart, x="Estado", y="Cantidad")
