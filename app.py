import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# ESTILOS
# =========================
st.markdown("""
<style>
body {background-color: #eef2f7;}
.card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

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

    data = {
        "message": f"Subida {nombre}",
        "content": contenido_base64
    }

    headers = {"Authorization": f"token {token}"}
    r = requests.put(url, json=data, headers=headers)

    return r.status_code in [200, 201]

# =========================
# VENCIMIENTOS
# =========================
def evaluar_vencimiento(ruta, nombre):
    vigencias = {
        "capacitacion": 365,
        "seguro": 365,
        "vtv": 365,
        "licencia": 365*5,
    }

    tipo = next((t for t in vigencias if t in nombre.lower()), None)
    if not tipo:
        return None

    fecha = datetime.fromtimestamp(os.path.getmtime(ruta))
    venc = fecha + timedelta(days=vigencias[tipo])

    if datetime.now() > venc:
        return "🔴 VENCIDO"
    elif (venc - datetime.now()).days <= 30:
        return "🟡 POR VENCER"
    else:
        return "🟢 VIGENTE"

# =========================
# BASE
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(base_registros, exist_ok=True)

actividades = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

# =========================
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar registro")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    tipo = st.selectbox("Tipo", ["permiso", "ats", "checklist", "capacitacion"])

    if st.button("Guardar"):

        ruta = os.path.join(base_registros, actividad, tipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        ok = subir_a_github(
            f"documentos/registros/{actividad}/{tipo}",
            archivo.name,
            archivo.getbuffer()
        )

        if ok:
            st.success("✔ Guardado en GitHub")
        else:
            st.warning("⚠ Guardado local OK")

# =========================
# 🔎 CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

actividad_sel = st.selectbox("Seleccionar actividad", actividades)

if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    # =========================
    # 📄 BASE
    # =========================
    carpeta = os.path.join(base_dir, actividad_sel)
    archivos = []

    for root, _, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".pdf"):
                archivos.append((f, os.path.join(root, f)))

    st.markdown("### 📄 Documentación base")

    if not archivos:
        st.warning("⚠️ No hay documentación base")
    else:
        for nombre, ruta in archivos:

            st.markdown(f"<div class='card'>📄 {nombre}</div>", unsafe_allow_html=True)

            with open(ruta, "rb") as f:
                st.download_button(
                    label=f"📥 {nombre}",
                    data=f,
                    file_name=nombre,
                    key=f"base_{nombre}"
                )

    # CONTROL BASE
    requisitos_base = ["procedimiento", "permiso", "checklist"]

    faltantes_base = [
        r for r in requisitos_base
        if not any(r in a[0].lower() for a in archivos)
    ]

    if faltantes_base:
        st.error(f"❌ Faltan: {', '.join(faltantes_base)}")
    else:
        st.success("✔ Base completa")

    # =========================
    # 📄 REGISTROS (ARREGLADO)
    # =========================
    st.markdown("### 📄 Registros")

    carpeta_reg = os.path.join(base_registros, actividad_sel)

    registros = {}

    if os.path.exists(carpeta_reg):

        for root, dirs, files in os.walk(carpeta_reg):
            for f in files:
                if f.endswith(".pdf"):

                    subtipo = os.path.basename(root)

                    if subtipo not in registros:
                        registros[subtipo] = []

                    registros[subtipo].append((f, os.path.join(root, f)))

    if not registros:
        st.warning("⚠️ No hay registros")
    else:
        for subtipo, archivos_reg in registros.items():

            st.markdown(f"#### 📁 {subtipo.upper()}")

            for nombre, ruta in archivos_reg:

                st.markdown(f"<div class='card'>📄 {nombre}</div>", unsafe_allow_html=True)

                with open(ruta, "rb") as f:
                    st.download_button(
                        label=f"📥 {nombre}",
                        data=f,
                        file_name=nombre,
                        key=f"{subtipo}_{nombre}"
                    )

    # CONTROL REGISTROS
    requisitos = ["permiso", "ats", "checklist"]

    faltantes = []

    for r in requisitos:
        encontrado = False

        for archivos_reg in registros.values():
            if any(r in nombre.lower() for nombre, _ in archivos_reg):
                encontrado = True
                break

        if not encontrado:
            faltantes.append(r)

    if faltantes:
        st.error(f"❌ Faltan: {', '.join(faltantes)}")
    else:
        st.success("✔ Registros completos")

# =========================
# ALERTAS
# =========================
st.markdown("## 🚨 Alertas")

alertas = []

for root, _, files in os.walk(base_registros):
    for f in files:
        if f.endswith(".pdf"):
            estado = evaluar_vencimiento(os.path.join(root, f), f)
            if estado and "🔴" in estado:
                alertas.append(f"{estado} - {f}")

if alertas:
    for a in alertas:
        st.write(a)
else:
    st.success("✔ Sin vencimientos")

# =========================
# PANEL
# =========================
st.markdown("## 📊 Panel")

docs = sum(len(files) for _, _, files in os.walk(base_registros))

c1, c2 = st.columns(2)
c1.metric("Actividades", len(actividades))
c2.metric("Registros", docs)

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

for act in actividades:
    st.sidebar.write(act)
