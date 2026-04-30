import streamlit as st
import os
import requests
import base64
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# NORMALIZAR
# =========================
def normalizar(txt):
    return txt.lower().replace("_"," ").replace("-"," ").strip()

# =========================
# 🔥 FUNCIÓN CORREGIDA (ÚNICO CAMBIO REAL)
# =========================
def obtener_registros_github(tipo_sel):

    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    reg_files = []

    if not token or not repo:
        return reg_files

    def recorrer(ruta):

        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        headers = {"Authorization": f"token {token}"}

        try:
            r = requests.get(url, headers=headers)

            if r.status_code == 200:
                for item in r.json():

                    if item["type"] == "dir":
                        recorrer(item["path"])

                    elif item["type"] == "file" and item["name"].endswith(".pdf"):
                        reg_files.append(item["name"])

        except:
            pass

    recorrer(f"documentos/registros/{tipo_sel}")

    return reg_files

# =========================
# GITHUB SUBIDA
# =========================
def subir_a_github(ruta, nombre, contenido):

    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"

    contenido_base64 = base64.b64encode(contenido).decode()

    headers = {"Authorization": f"token {token}"}

    requests.put(url, json={
        "message": f"Subida {nombre}",
        "content": contenido_base64
    }, headers=headers)

# =========================
# PDF
# =========================
def generar_pdf(tipos, criticos):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elementos = []

    elementos.append(Paragraph("REPORTE SST", styles["Title"]))
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
    elementos.append(Spacer(1, 20))

    data = [["Tipo", "Estado"]]

    for tipo in tipos:

        archivos = obtener_registros_github(tipo)

        if normalizar(tipo) in criticos:

            req = ["permiso","ats","checklist","capacitacion"]
            falt = [r for r in req if not any(r in normalizar(f) for f in archivos)]

            if not archivos:
                estado = "CRITICO"
            elif falt:
                estado = "PARCIAL"
            else:
                estado = "OK"
        else:
            estado = "OK" if archivos else "CRITICO"

        data.append([tipo.upper(), estado])

    tabla = Table(data)
    tabla.setStyle(TableStyle([("GRID",(0,0),(-1,-1),1,colors.black)]))

    elementos.append(tabla)
    doc.build(elementos)

    buffer.seek(0)
    return buffer

# =========================
# TIPOS
# =========================
tipos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

criticos = tipos

# =========================
# CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)
    carpeta = st.text_input("Subcarpeta (permisos / ats / checklist)")

    if st.button("Guardar"):
        subir_a_github(
            f"documentos/registros/{tipo}/{carpeta}",
            archivo.name,
            archivo.getbuffer()
        )
        st.success("✔ Subido")

# =========================
# CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

reg_files = obtener_registros_github(tipo_sel)

if reg_files:
    for f in reg_files:
        st.write("📄", f)
else:
    st.warning("⚠️ No hay registros")

# =========================
# CONTROL
# =========================
st.markdown("### 📋 Control")

if normalizar(tipo_sel) in criticos:

    if not reg_files:
        st.error("❌ No hay registros")
    else:
        req = ["permiso","ats","checklist","capacitacion"]
        falt = [r for r in req if not any(r in normalizar(f) for f in reg_files)]

        if falt:
            st.error("❌ Faltan: " + ", ".join(falt))
        else:
            st.success("✔ Completo")

# =========================
# DASHBOARD
# =========================
st.markdown("---")
st.markdown("## 📊 Dashboard")

ok = critico = 0

for tipo in tipos:

    archivos = obtener_registros_github(tipo)

    if archivos:
        ok += 1
    else:
        critico += 1

fig, ax = plt.subplots()
ax.pie([ok, critico], labels=["OK","Crítico"], autopct="%1.0f%%")
ax.axis("equal")

st.pyplot(fig)

# =========================
# PDF
# =========================
st.markdown("### 📄 Reporte")

pdf = generar_pdf(tipos, criticos)

st.download_button("📥 Descargar PDF", pdf, "reporte_sst.pdf")
