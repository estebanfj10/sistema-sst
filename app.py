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

# GRÁFICO
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

    headers = {"Authorization": f"token {token}"}

    r = requests.put(url, json={"message": nombre, "content": contenido_base64}, headers=headers)

    if r.status_code not in [200, 201]:
        st.warning("⚠️ Error al subir a GitHub")

# =========================
# FUNCIONES GITHUB
# =========================
def obtener_subtipos_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN", None)
    repo = st.secrets.get("GITHUB_REPO", None)

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{tipo}"
    headers = {"Authorization": f"token {token}"}

    try:
        r = requests.get(url, headers=headers)
        return [i["name"] for i in r.json() if i["type"] == "dir"]
    except:
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
        return [i["name"] for i in r.json() if i["type"] == "dir"]
    except:
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
            color = colors.green
        elif estado == "PARCIAL":
            parcial += 1
            color = colors.yellow
        else:
            critico_count += 1
            color = colors.red

        data.append([tipo.upper(), estado])
        colores_filas.append(color)

    tabla = Table(data)

    estilo = [("GRID", (0,0), (-1,-1), 1, colors.black)]

    for i, color in enumerate(colores_filas, start=1):
        estilo.append(("BACKGROUND", (1,i), (1,i), color))

    tabla.setStyle(TableStyle(estilo))

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

tipos += obtener_tipos_github()
tipos = sorted(list(set(tipos)))

if not tipos:
    st.warning("⚠️ No hay categorías cargadas")
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
# CONSULTA + CONTROL
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

# BASE
st.markdown("### 📄 Documentación base")

base_files = []

if os.path.exists(os.path.join(base_dir, tipo_sel)):
    for root, _, files in os.walk(os.path.join(base_dir, tipo_sel)):
        for f in files:
            if f.endswith(".pdf"):
                base_files.append((f, os.path.join(root, f)))

if base_files:
    for nombre, ruta in base_files:
        with open(ruta, "rb") as f:
            st.download_button(nombre, f.read(), file_name=nombre)
else:
    st.warning("⚠️ Sin documentación base")

# CONTROL BASE
st.markdown("### 📋 Control documentación base")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

if tipo_sel in criticos:

    if not base_files:
        st.error("❌ No hay documentación base")
    else:
        req = ["procedimiento","permiso","checklist","emergencia","ats"]
        falt = [r for r in req if not any(r in f[0].lower() for f in base_files)]

        if falt:
            st.error(f"❌ Faltan: {', '.join(falt)}")
        else:
            st.success("✔ Completo")

# REGISTROS
st.markdown("### 📊 Registros")

reg_files = []

if os.path.exists(os.path.join(reg_dir, tipo_sel)):
    for root, _, files in os.walk(os.path.join(reg_dir, tipo_sel)):
        for f in files:
            if f.endswith(".pdf"):
                reg_files.append((f, os.path.join(root, f)))

if reg_files:
    for nombre, ruta in reg_files:
        with open(ruta, "rb") as f:
            st.download_button(nombre, f.read(), file_name=nombre)
else:
    st.warning("⚠️ Sin registros")

# CONTROL REGISTROS
st.markdown("### 📋 Control registros")

if tipo_sel in criticos:

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

    if os.path.exists(os.path.join(base_dir, tipo)):
        for _, _, files in os.walk(os.path.join(base_dir, tipo)):
            base_files += [f for f in files if f.endswith(".pdf")]

    if os.path.exists(os.path.join(reg_dir, tipo)):
        for _, _, files in os.walk(os.path.join(reg_dir, tipo)):
            reg_files += [f for f in files if f.endswith(".pdf")]

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

# =========================
# PDF
# =========================
st.markdown("### 📄 Reporte SST")

pdf = generar_pdf(tipos, base_dir, reg_dir, criticos)

st.download_button("📥 Descargar PDF", pdf, "reporte_sst.pdf")
