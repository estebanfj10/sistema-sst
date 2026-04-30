import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta

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
# GITHUB
# =========================
def subir_a_github(ruta, nombre, contenido):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    data = {"message": f"Subida {nombre}", "content": contenido_base64}
    headers = {"Authorization": f"token {token}"}

    r = requests.put(url, json=data, headers=headers)
    return r.status_code in [200, 201]

def obtener_subtipos_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

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
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

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
# REGISTROS GITHUB
# =========================
def obtener_registros_github(tipo):

    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    resultados = []

    if not token or not repo:
        return resultados

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
                        carpeta = item["path"].split("/")[-2]

                        resultados.append({
                            "nombre": item["name"],
                            "url": item["download_url"],
                            "subtipo": carpeta
                        })
        except:
            pass

    recorrer(f"documentos/registros/{tipo}")
    return resultados

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
    tipos = ["general"]

# =========================
# CARGA
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

        with open(os.path.join(ruta, archivo.name), "wb") as f:
            f.write(archivo.getbuffer())

        subir_a_github(
            f"documentos/registros/{tipo}/{subtipo}",
            archivo.name,
            archivo.getbuffer()
        )

        st.success("✔ Guardado")

# =========================
# CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

# =========================
# 📄 BASE
# =========================
st.markdown("### 📄 Documentación base")

archivos_base = []
carpeta_base = os.path.join(base_dir, tipo_sel)

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
        with open(ruta, "rb") as file:
            st.download_button(f"📥 Descargar {nombre}", file, nombre)

# =========================
# 📊 REGISTROS
# =========================
st.markdown("### 📊 Registros")

archivos_reg = []
reg_github = obtener_registros_github(tipo_sel)

if reg_github:
    for item in reg_github:
        nombre = item["nombre"]
        subtipo = item["subtipo"]
        url = item["url"]

        archivos_reg.append((nombre, subtipo))

        st.write(f"📁 {subtipo} → {nombre}")

        try:
            r = requests.get(url)
            if r.status_code == 200:
                st.download_button(
                    f"📥 Descargar {nombre}",
                    r.content,
                    nombre,
                    key=f"{nombre}"
                )
        except:
            st.error(f"Error al cargar {nombre}")
else:
    st.warning("⚠️ No hay registros")

# =========================
# 🚨 SEMÁFORO (NUEVO)
# =========================
st.markdown("## 🚨 Estado general SST")

def evaluar_estado(tipo, base, reg):

    criticos = [
        "altura","excavacion","izaje",
        "trabajo en caliente","espacio confinado","electricidad"
    ]

    if tipo not in criticos:
        return "ℹ️ NO CRÍTICO"

    req_base = ["procedimiento","permiso","ats","checklist","emergencia"]
    req_reg = ["permiso","ats","checklist","capacitacion"]

    base_ok = all(any(r in normalizar(a[0]) for a in base) for r in req_base)
    reg_ok = all(any(r in normalizar(a[0]) for a in reg) for r in req_reg)

    if base_ok and reg_ok:
        return "🟢 COMPLETO"
    if base_ok or reg_ok:
        return "🟡 PARCIAL"
    return "🔴 CRÍTICO"

estado = evaluar_estado(tipo_sel, archivos_base, archivos_reg)

if "🟢" in estado:
    st.success(estado)
elif "🟡" in estado:
    st.warning(estado)
elif "🔴" in estado:
    st.error(estado)
else:
    st.info(estado)
