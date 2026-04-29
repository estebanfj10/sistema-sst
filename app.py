import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta

st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")
st.title("🦺 Sistema SST")

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

# =========================
# VENCIMIENTOS
# =========================
def evaluar_vencimiento(ruta, nombre):
    reglas = {"capacitacion":365, "seguro":365, "vtv":365}

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
base_dir = "documentos/registros"
os.makedirs(base_dir, exist_ok=True)

tipos = [
    "ats","caliente","electricidad",
    "espacio confinado","excavacion",
    "general","herramientas","izaje"
]

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
        ruta = os.path.join(base_dir, tipo, subtipo)
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

carpeta = os.path.join(base_dir, tipo_sel)
archivos = []

if os.path.exists(carpeta):
    for root, _, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".pdf"):
                archivos.append((f, root))

# =========================
# 📄 VISUAL
# =========================
st.markdown("### 📄 Registros")

if not archivos:
    st.warning("Sin registros")
else:
    for nombre, ruta in archivos:
        st.write(f"📁 {os.path.basename(ruta)} → {nombre}")

# =========================
# 📋 CONTROL
# =========================
criticos = ["excavacion","electricidad","espacio confinado","izaje","caliente"]

st.markdown("### 📋 Control SST")

if tipo_sel in criticos:
    req = ["permiso","ats","checklist"]
    faltan = [r for r in req if not any(r in a[0].lower() for a in archivos)]

    if faltan:
        st.error(f"❌ Faltan: {', '.join(faltan)}")
    else:
        st.success("✔ Completo")
else:
    if archivos:
        st.success("✔ Tiene registros")
    else:
        st.error("❌ Sin registros")

# =========================
# 🚨 ALERTAS
# =========================
st.markdown("## 🚨 Alertas")

alertas = []

for root, _, files in os.walk(base_dir):
    for f in files:
        estado = evaluar_vencimiento(os.path.join(root, f), f)
        if estado:
            alertas.append(f"{estado} - {f}")

if alertas:
    for a in alertas:
        st.write(a)
else:
    st.success("✔ Sin alertas")
