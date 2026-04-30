import streamlit as st
import os
import matplotlib.pyplot as plt

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime

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
# PDF
# =========================
def generar_pdf(tipos, base_dir, reg_dir, criticos):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elementos = []

    if os.path.exists("banner.png"):
        elementos.append(Image("banner.png", width=500, height=120))
        elementos.append(Spacer(1, 10))

    elementos.append(Paragraph("REPORTE SISTEMA SST", styles["Title"]))
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
    elementos.append(Spacer(1, 20))

    data = [["Tipo", "Estado"]]

    for tipo in tipos:

        base_files = []
        reg_files = []

        if os.path.exists(os.path.join(base_dir, tipo)):
            for _, _, files in os.walk(os.path.join(base_dir, tipo)):
                base_files += [f for f in files if f.endswith(".pdf")]

        if os.path.exists(os.path.join(reg_dir, tipo)):
            for _, _, files in os.walk(os.path.join(reg_dir, tipo)):
                reg_files += [f for f in files if f.endswith(".pdf")]

        tipo_norm = normalizar(tipo)

        if tipo_norm in criticos:

            req_base = ["procedimiento","permiso","checklist","emergencia","ats"]
            req_reg = ["permiso","ats","checklist","capacitacion"]

            falt_base = [r for r in req_base if not any(r in normalizar(f) for f in base_files)]
            falt_reg = [r for r in req_reg if not any(r in normalizar(f) for f in reg_files)]

            if not base_files and not reg_files:
                estado = "CRITICO"
            elif falt_base or falt_reg:
                estado = "PARCIAL"
            else:
                estado = "OK"

        else:
            if not base_files and not reg_files:
                estado = "CRITICO"
            elif not base_files or not reg_files:
                estado = "PARCIAL"
            else:
                estado = "OK"

        data.append([tipo.upper(), estado])

    tabla = Table(data)
    tabla.setStyle(TableStyle([("GRID",(0,0),(-1,-1),1,colors.black)]))

    elementos.append(tabla)
    doc.build(elementos)

    buffer.seek(0)
    return buffer

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
        req_base = {
            "Procedimiento": "procedimiento",
            "Permiso de trabajo": "permiso",
            "Checklist": "checklist",
            "Plan de emergencia": "emergencia",
            "ATS": "ats"
        }

        faltantes = []
        presentes = []

        for nombre, clave in req_base.items():
            if any(clave in normalizar(f[0]) for f in base_files):
                presentes.append(nombre)
            else:
                faltantes.append(nombre)

        if presentes:
            st.info("✔ Presentes: " + ", ".join(presentes))

        if faltantes:
            st.error("❌ Faltan: " + ", ".join(faltantes))
        else:
            st.success("✔ Documentación base completa")

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

reg_files.sort(key=lambda x: os.path.getmtime(x[1]), reverse=True)

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
        req_reg = {
            "Permiso firmado": "permiso",
            "ATS": "ats",
            "Checklist": "checklist",
            "Capacitación": "capacitacion"
        }

        faltantes = []
        presentes = []

        for nombre, clave in req_reg.items():
            if any(clave in normalizar(f[0]) for f in reg_files):
                presentes.append(nombre)
            else:
                faltantes.append(nombre)

        if presentes:
            st.info("✔ Presentes: " + ", ".join(presentes))

        if faltantes:
            st.error("❌ Faltan: " + ", ".join(faltantes))
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
        req_reg = ["permiso","ats","checklist","capacitacion"]

        falt_base = [r for r in req_base if not any(r in normalizar(f) for f in base_files)]
        falt_reg = [r for r in req_reg if not any(r in normalizar(f) for f in reg_files)]

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
ax.pie([ok, parcial, critico],
       labels=["OK","Parcial","Crítico"],
       autopct="%1.0f%%",
       colors=["#2ecc71","#f1c40f","#e74c3c"])
ax.axis("equal")

st.pyplot(fig)

# =========================
# PDF
# =========================
st.markdown("### 📄 Reporte SST")

pdf = generar_pdf(tipos, base_dir, reg_dir, criticos)

st.download_button(
    "📥 Descargar reporte PDF",
    data=pdf,
    file_name="reporte_sst.pdf",
    mime="application/pdf"
)
