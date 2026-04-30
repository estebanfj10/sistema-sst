import streamlit as st
import os
import requests
import base64
from datetime import datetime
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

st.image("banner.png", use_container_width=True)
st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# NORMALIZAR
# =========================
def normalizar(txt):
    return txt.lower().replace("_"," ").replace("-"," ").strip()

# =========================
# BASE
# =========================
base_dir = "documentos"
reg_dir = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(reg_dir, exist_ok=True)

# =========================
# TIPOS
# =========================
tipos = []
if os.path.exists(reg_dir):
    tipos += [d for d in os.listdir(reg_dir) if os.path.isdir(os.path.join(reg_dir, d))]

if not tipos:
    tipos = ["general"]

# =========================
# CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

# =========================
# BASE
# =========================
st.markdown("### 📄 Documentación base")

base_files = []

ruta_base = os.path.join(base_dir, tipo_sel)

if os.path.exists(ruta_base):
    for root, _, files in os.walk(ruta_base):
        for f in files:
            if f.endswith(".pdf"):
                base_files.append((f, os.path.join(root, f)))

if base_files:
    for nombre, ruta in base_files:
        with open(ruta, "rb") as f:
            st.download_button(f"📄 {nombre}", f.read(), file_name=nombre)
else:
    st.warning("⚠️ No hay documentación base")

# =========================
# CONTROL BASE
# =========================
st.markdown("### 📋 Control documentación base")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

if normalizar(tipo_sel) in criticos:

    if not base_files:
        st.error("❌ No hay documentación base")
    else:
        req = ["procedimiento","permiso","checklist","emergencia","ats"]
        falt = [r for r in req if not any(r in f[0].lower() for f in base_files)]

        if falt:
            st.error(f"❌ Faltan: {', '.join(falt)}")
        else:
            st.success("✔ Completo")

# =========================
# REGISTROS
# =========================
st.markdown("### 📊 Registros")

reg_files = []

ruta_reg = os.path.join(reg_dir, tipo_sel)

if os.path.exists(ruta_reg):
    for root, _, files in os.walk(ruta_reg):
        for f in files:
            if f.endswith(".pdf"):
                reg_files.append((f, os.path.join(root, f)))

if reg_files:
    for nombre, ruta in reg_files:
        with open(ruta, "rb") as f:
            st.download_button(f"📊 {nombre}", f.read(), file_name=nombre)
else:
    st.warning("⚠️ No hay registros")

# =========================
# CONTROL REGISTROS
# =========================
st.markdown("### 📋 Control registros")

if normalizar(tipo_sel) in criticos:

    if not reg_files:
        st.error("❌ No hay registros cargados")
    else:
        req = ["permiso","ats","checklist"]
        falt = [r for r in req if not any(r in f[0].lower() for f in reg_files)]

        if falt:
            st.error(f"❌ Faltan: {', '.join(falt)}")
        else:
            st.success("✔ Registros completos")

# =========================
# DASHBOARD
# =========================
st.markdown("---")
st.markdown("## 📊 Dashboard SST")

total, ok, parcial, critico = len(tipos), 0, 0, 0

for tipo in tipos:

    base_files = []
    reg_files = []

    rb = os.path.join(base_dir, tipo)
    rr = os.path.join(reg_dir, tipo)

    if os.path.exists(rb):
        for _, _, files in os.walk(rb):
            base_files += [f for f in files if f.endswith(".pdf")]

    if os.path.exists(rr):
        for _, _, files in os.walk(rr):
            reg_files += [f for f in files if f.endswith(".pdf")]

    tipo_norm = normalizar(tipo)

    if tipo_norm in criticos:

        req_base = ["procedimiento","permiso","checklist","emergencia","ats"]
        req_reg = ["permiso","ats","checklist"]

        falt_base = [r for r in req_base if not any(r in f.lower() for f in base_files)]
        falt_reg = [r for r in req_reg if not any(r in f.lower() for f in reg_files)]

        if not base_files and not reg_files:
            critico += 1
        elif falt_base or falt_reg:
            parcial += 1
        else:
            ok += 1

    else:
        if not base_files and not reg_files:
            critico += 1
        elif not base_files or not reg_files:
            parcial += 1
        else:
            ok += 1

# KPI
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total", total)
c2.metric("🟢 OK", ok)
c3.metric("🟡 Parcial", parcial)
c4.metric("🔴 Crítico", critico)

# TORTA
fig, ax = plt.subplots()
ax.pie(
    [ok, parcial, critico],
    labels=["OK","Parcial","Crítico"],
    autopct="%1.0f%%",
    colors=["#2ecc71","#f1c40f","#e74c3c"]
)
ax.axis("equal")

st.pyplot(fig)
