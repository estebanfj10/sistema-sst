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
h1 {color: #1f4e79;}
.card {
    background: white;
    padding: 15px;
    border-radius: 10px;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🔥 GITHUB
# =========================
def subir_a_github(ruta, nombre_archivo, contenido):

    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return False

    try:
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre_archivo}"

        contenido_base64 = base64.b64encode(contenido).decode()

        data = {
            "message": f"Subida {nombre_archivo}",
            "content": contenido_base64
        }

        headers = {"Authorization": f"token {token}"}

        r = requests.put(url, json=data, headers=headers)

        return r.status_code in [200, 201]

    except:
        return False

# =========================
# VENCIMIENTOS
# =========================
def evaluar_vencimiento(ruta, nombre):

    vigencias = {
        "capacitacion": 365,
        "programa": 365,
        "aviso": 180,
        "seguro": 365,
        "vtv": 365,
        "licencia": 365*5,
        "apto": 365,
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
# 📤 CARGA REGISTROS
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    tipo = st.selectbox(
        "Tipo de registro",
        [
            "ats",
            "permiso",
            "checklist",
            "capacitacion",
            "inspeccion",
            "incidente",
            "mantenimiento"
        ]
    )

    if st.button("Guardar archivo"):

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
            st.success(f"✔ Guardado en REGISTROS/{actividad}/{tipo} (GitHub OK)")
        else:
            st.warning("⚠ Guardado local OK, pero falló GitHub")

# =========================
# 🔎 BUSCADOR
# =========================
st.markdown("### 🔎 Búsqueda")

consulta = st.text_input("Buscar actividad")

actividad_sel = None

if consulta:
    for act in actividades:
        if act in consulta.lower():
            actividad_sel = act
            break

    if not actividad_sel:
        actividad_sel = st.selectbox("Seleccionar:", actividades)

# =========================
# DOCUMENTACIÓN BASE + CONTROL
# =========================
if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    carpeta = os.path.join(base_dir, actividad_sel)
    archivos = []

    for root, _, files in os.walk(carpeta):
        for f in files:
            if f.endswith(".pdf"):
                archivos.append((f, os.path.join(root, f)))

    if not archivos:
        st.warning("⚠️ No hay documentación base")
    else:
        for nombre, ruta in archivos:
            st.markdown(f"<div class='card'>📄 {nombre}</div>", unsafe_allow_html=True)

            with open(ruta, "rb") as f:
                st.download_button("📥 Descargar", f, file_name=nombre)

    requisitos = ["procedimiento", "permiso", "checklist", "emergencia"]

    faltantes = [
        r for r in requisitos
        if not any(r in a[0].lower() for a in archivos)
    ]

    if faltantes:
        st.error(f"❌ Faltan: {', '.join(faltantes)}")
    else:
        st.success("✔ Documentación completa")

# =========================
# 📂 REGISTROS (VISUAL)
# =========================
    st.markdown("### 📂 Registros cargados")

    carpeta_reg = os.path.join(base_registros, actividad_sel)

    if os.path.exists(carpeta_reg):

        tipos = [
            d for d in os.listdir(carpeta_reg)
            if os.path.isdir(os.path.join(carpeta_reg, d))
        ]

        if tipos:
            for t in tipos:
                ruta_tipo = os.path.join(carpeta_reg, t)

                archivos = [
                    f for f in os.listdir(ruta_tipo)
                    if f.endswith(".pdf")
                ]

                st.write(f"📁 {t} ({len(archivos)})")

        else:
            st.info("No hay registros en esta actividad")

    else:
        st.info("No hay registros para esta actividad")

# =========================
# ALERTAS
# =========================
st.markdown("---")
st.markdown("## 🚨 Alertas")

alertas = []

for root, _, files in os.walk(base_registros):
    for f in files:
        if f.endswith(".pdf"):
            estado = evaluar_vencimiento(os.path.join(root, f), f)
            if estado and ("🔴" in estado or "🟡" in estado):
                alertas.append(f"{estado} - {f}")

if alertas:
    for a in alertas:
        st.write(a)
else:
    st.success("✔ Sin alertas")

# =========================
# PANEL
# =========================
st.markdown("---")
st.markdown("## 📊 Panel")

total = len(actividades)
docs = sum(len(files) for _, _, files in os.walk(base_registros))

c1, c2 = st.columns(2)
c1.metric("Actividades", total)
c2.metric("Registros", docs)

# =========================
# SIDEBAR
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

for act in actividades:
    st.sidebar.markdown(f"📁 {act}")
