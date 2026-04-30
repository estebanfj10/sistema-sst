import streamlit as st
import os
import requests
import base64
from datetime import datetime
from io import BytesIO

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# GRÁFICO TORTA
import matplotlib.pyplot as plt

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

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

    ok = parcial = critico_count = 0
    colores_filas = []

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
            if not base_files and not reg_files:
                estado = "CRITICO"
            elif not base_files or not reg_files:
                estado = "PARCIAL"
        else:
            if not base_files and not reg_files:
                estado = "CRITICO"
            elif not base_files or not reg_files:
                estado = "PARCIAL"

        if estado == "OK":
            ok += 1
            color = colors.green
        elif estado == "PARCIAL":
            parcial += 1
            color = colors.yellow
        else:
            critico_count += 1
            color = colors.red

        data.append([tipo.upper(), estado])
        colores_filas.append(color)

    elementos.append(Paragraph(f"OK: {ok} | Parcial: {parcial} | Crítico: {critico_count}", styles["Heading2"]))
    elementos.append(Spacer(1, 15))

    tabla = Table(data)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ]

    for i, color in enumerate(colores_filas, start=1):
        estilo.append(("BACKGROUND", (1, i), (1, i), color))

    tabla.setStyle(TableStyle(estilo))

    elementos.append(tabla)
    elementos.append(Spacer(1, 20))

    if critico_count > 0:
        conclusion = "Sistema con tareas críticas"
    elif parcial > 0:
        conclusion = "Sistema con tareas incompletas"
    else:
        conclusion = "Sistema en condiciones óptimas"

    elementos.append(Paragraph(conclusion, styles["Heading2"]))

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

# TIPOS
tipos = []
if os.path.exists(reg_dir):
    tipos += [d for d in os.listdir(reg_dir) if os.path.isdir(os.path.join(reg_dir, d))]
tipos += obtener_tipos_github()
tipos = sorted(list(set(tipos)))
if not tipos:
    tipos = ["general"]

# =========================
# CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)
    subtipos = obtener_subtipos_github(tipo) or ["otros"]
    subtipo = st.selectbox("Subtipo", subtipos)

    if st.button("Guardar"):
        ruta = os.path.join(reg_dir, tipo, subtipo)
        os.makedirs(ruta, exist_ok=True)

        with open(os.path.join(ruta, archivo.name), "wb") as f:
            f.write(archivo.getbuffer())

        subir_a_github(f"documentos/registros/{tipo}/{subtipo}", archivo.name, archivo.getbuffer())
        st.success("✔ Guardado")

# =========================
# DASHBOARD
# =========================
st.markdown("---")
st.markdown("## 📊 Dashboard SST")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

total, ok, parcial, critico = len(tipos), 0, 0, 0

for tipo in tipos:

    base_files = []
    reg_files = []

    if os.path.exists(os.path.join(base_dir, tipo)):
        for _, _, files in os.walk(os.path.join(base_dir, tipo)):
            base_files += [f for f in files if f.endswith(".pdf")]

    if os.path.exists(os.path.join(reg_dir, tipo)):
        for _, _, files in os.walk(os.path.join(reg_dir, tipo)):
            reg_files += [f for f in files if f.endswith(".pdf")]

    estado = "OK"

    if tipo in criticos:
        if not base_files and not reg_files:
            estado = "CRITICO"
        elif not base_files or not reg_files:
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

# KPI
c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"<div style='background:#1f4e79;color:white;padding:15px;border-radius:10px;text-align:center'><h3>Total</h3><h2>{total}</h2></div>", unsafe_allow_html=True)
c2.markdown(f"<div style='background:#2ecc71;color:white;padding:15px;border-radius:10px;text-align:center'><h3>OK</h3><h2>{ok}</h2></div>", unsafe_allow_html=True)
c3.markdown(f"<div style='background:#f1c40f;color:black;padding:15px;border-radius:10px;text-align:center'><h3>Parcial</h3><h2>{parcial}</h2></div>", unsafe_allow_html=True)
c4.markdown(f"<div style='background:#e74c3c;color:white;padding:15px;border-radius:10px;text-align:center'><h3>Crítico</h3><h2>{critico}</h2></div>", unsafe_allow_html=True)

# TORTA
st.markdown("### 📊 Distribución de estados")

labels = ["OK", "Parcial", "Crítico"]
sizes = [ok, parcial, critico]
colors_pie = ["#2ecc71", "#f1c40f", "#e74c3c"]

fig, ax = plt.subplots()
ax.pie(sizes, labels=labels, autopct="%1.0f%%", colors=colors_pie, startangle=90)
ax.axis("equal")

st.pyplot(fig)

# PDF
st.markdown("### 📄 Reporte SST")

pdf = generar_pdf(tipos, base_dir, reg_dir, criticos)

st.download_button("📥 Descargar reporte PDF", pdf, "reporte_sst.pdf", "application/pdf")
