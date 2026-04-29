import streamlit as st
import os
from datetime import datetime, timedelta

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Sistema SST",
    page_icon="🦺",
    layout="wide"
)

# =========================
# BANNER
# =========================
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
.small-text {
    color: gray;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

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
# 📤 CARGA REGISTROS (FUNCIONAL)
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:

    actividad = st.selectbox("Actividad", actividades)

    # 🔥 SIMPLE Y FUNCIONAL (NO SE ROMPE)
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
    )

    if st.button("Guardar archivo"):

        ruta = os.path.join(base_registros, actividad, tipo)
        os.makedirs(ruta, exist_ok=True)

        ruta_archivo = os.path.join(ruta, archivo.name)

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        st.success(f"✔ Guardado en REGISTROS/{actividad}/{tipo}")

# =========================
# 🔎 BUSCADOR (IMPORTANTE)
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
# DOCUMENTACIÓN + CONTROL
# =========================
if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    col1, col2 = st.columns(2)

    # BASE
    with col1:
        st.markdown("### 📄 Documentación base")

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
                    st.download_button("Descargar", f, file_name=nombre)

        requisitos = ["procedimiento", "permiso", "checklist", "emergencia"]

        faltantes = [
            r for r in requisitos
            if not any(r in a[0].lower() for a in archivos)
        ]

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Documentación completa")

    # REGISTROS
    with col2:
        st.markdown("### 📊 Estado registros")

        requisitos = ["permiso", "ats", "checklist"]
        faltantes = []

        carpeta_reg = os.path.join(base_registros, actividad_sel)

        for r in requisitos:
            ok = False

            if os.path.exists(carpeta_reg):
                for root, _, files in os.walk(carpeta_reg):
                    if any(r in f.lower() for f in files):
                        ok = True

            if not ok:
                faltantes.append(r)

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Registros completos")

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
