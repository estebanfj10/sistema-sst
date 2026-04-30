import streamlit as st
import os
import requests
import base64
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
# GITHUB LECTURA (CLAVE)
# =========================
def obtener_registros_github(tipo_sel):

    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    estructura = {}

    if not token or not repo:
        return estructura, "local"

    def recorrer(ruta):
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        headers = {"Authorization": f"token {token}"}

        resultado = {}

        try:
            r = requests.get(url, headers=headers)

            if r.status_code == 200:
                for item in r.json():

                    if item["type"] == "dir":
                        sub = recorrer(item["path"])
                        if sub:
                            resultado[item["name"]] = sub

                    elif item["type"] == "file" and item["name"].endswith(".pdf"):
                        resultado.setdefault("archivos", []).append({
                            "nombre": item["name"],
                            "url": item["download_url"]
                        })
        except:
            pass

        return resultado

    ruta = f"documentos/registros/{tipo_sel}"
    data = recorrer(ruta)

    if data:
        return data, "github"

    return {}, "local"

# =========================
# PDF
# =========================
def generar_pdf(tipos, base_dir, reg_dir, criticos):

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elementos = []

    elementos.append(Paragraph("REPORTE SISTEMA SST", styles["Title"]))
    elementos.append(Spacer(1, 10))
    elementos.append(Paragraph(f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", styles["Normal"]))
    elementos.append(Spacer(1, 20))

    data = [["Tipo", "Estado"]]

    for tipo in tipos:

        estructura, _ = obtener_registros_github(tipo)

        archivos = []
        for carpeta in estructura.values():
            for sub in carpeta.values() if isinstance(carpeta, dict) else [carpeta]:
                for item in sub:
                    archivos.append(item["nombre"])

        tipo_norm = normalizar(tipo)

        if tipo_norm in criticos:

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
# BASE
# =========================
base_dir = "documentos"
reg_dir = os.path.join(base_dir, "registros")

os.makedirs(reg_dir, exist_ok=True)

tipos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

# =========================
# CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)
    subcarpeta = st.text_input("Subcarpeta (ej: permisos, ats, checklist)")

    if st.button("Guardar"):
        subir_a_github(
            f"documentos/registros/{tipo}/{subcarpeta}",
            archivo.name,
            archivo.getbuffer()
        )
        st.success("✔ Subido a GitHub")

# =========================
# CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

estructura, origen = obtener_registros_github(tipo_sel)

st.caption(f"Origen: {origen}")

reg_files = []

if estructura:

    for carpeta, contenido in estructura.items():

        if isinstance(contenido, list):

            st.markdown(f"#### 📁 {carpeta}")

            for item in contenido:
                nombre = item["nombre"]
                reg_files.append(nombre)

                st.markdown(f"📄 [{nombre}]({item['url']})")

        else:
            for subcarpeta, archivos in contenido.items():

                st.markdown(f"#### 📁 {subcarpeta}")

                for item in archivos:
                    nombre = item["nombre"]
                    reg_files.append(nombre)

                    st.markdown(f"📄 [{nombre}]({item['url']})")

else:
    st.warning("⚠️ No hay registros")

# =========================
# CONTROL
# =========================
st.markdown("### 📋 Control registros")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

if normalizar(tipo_sel) in criticos:

    if not reg_files:
        st.error("❌ No hay registros")
    else:
        req = {
            "Permiso": "permiso",
            "ATS": "ats",
            "Checklist": "checklist",
            "Capacitación": "capacitacion"
        }

        falt = [k for k,v in req.items() if not any(v in normalizar(f) for f in reg_files)]

        if falt:
            st.error("❌ Faltan: " + ", ".join(falt))
        else:
            st.success("✔ Completo")

# =========================
# DASHBOARD
# =========================
st.markdown("---")
st.markdown("## 📊 Dashboard")

total = len(tipos)
ok = parcial = critico = 0

for tipo in tipos:

    estructura, _ = obtener_registros_github(tipo)

    archivos = []
    for carpeta in estructura.values():
        for sub in carpeta.values() if isinstance(carpeta, dict) else [carpeta]:
            for item in sub:
                archivos.append(item["nombre"])

    if not archivos:
        critico += 1
    else:
        ok += 1

# KPIs
c1, c2, c3 = st.columns(3)
c1.metric("Total", total)
c2.metric("OK", ok)
c3.metric("Crítico", critico)

# TORTA
fig, ax = plt.subplots()
ax.pie([ok, critico], labels=["OK","Crítico"], autopct="%1.0f%%")
ax.axis("equal")
st.pyplot(fig)

# =========================
# PDF
# =========================
st.markdown("### 📄 Reporte")

pdf = generar_pdf(tipos, base_dir, reg_dir, criticos)

st.download_button("📥 Descargar PDF", pdf, "reporte_sst.pdf")
