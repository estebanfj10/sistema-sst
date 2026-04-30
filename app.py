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
# 🔥 NUEVO: LECTURA GITHUB REGISTROS
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

# =========================
# 📊 REGISTROS (CORREGIDO)
# =========================
st.markdown("### 📊 Registros")

archivos_reg = []

# 🔥 GITHUB
reg_github = obtener_registros_github(tipo_sel)

if reg_github:

    for item in reg_github:
        archivos_reg.append((item["nombre"], item["subtipo"]))

        st.write(f"📁 {item['subtipo']} → {item['nombre']}")
        st.markdown(f"[📥 Descargar]({item['url']})")

# 🔹 LOCAL (fallback)
else:

    carpeta_reg = os.path.join(reg_dir, tipo_sel)

    if os.path.exists(carpeta_reg):
        for root, _, files in os.walk(carpeta_reg):
            for f in files:
                if f.endswith(".pdf"):
                    subtipo = os.path.basename(root)
                    archivos_reg.append((f, subtipo))

                    st.write(f"📁 {subtipo} → {f}")

                    with open(os.path.join(root, f), "rb") as file:
                        st.download_button(
                            f"📥 Descargar {f}",
                            data=file,
                            file_name=f,
                            key=f"reg_{subtipo}_{f}"
                        )

if not archivos_reg:
    st.warning("⚠️ No hay registros")

# =========================
# 📋 CONTROL REGISTROS
# =========================
st.markdown("### 📋 Control registros")

criticos = [
    "altura","excavacion","izaje",
    "trabajo en caliente","espacio confinado","electricidad"
]

if tipo_sel in criticos:

    requisitos = ["permiso","ats","checklist"]
    faltantes = [
        r for r in requisitos
        if not any(r in a[0].lower() for a in archivos_reg)
    ]

    if faltantes:
        st.error(f"❌ Faltan: {', '.join(faltantes)}")
    else:
        st.success("✔ Registros completos")

else:
    if archivos_reg:
        st.success("✔ Tiene registros")
    else:
        st.error("❌ Sin registros")
