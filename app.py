import streamlit as st
import os
import requests
import base64
from datetime import datetime, timedelta

# =========================
# 🧱 CONFIG
# =========================
st.set_page_config(
    page_title="Sistema SST",
    page_icon="🦺",
    layout="wide"
)

# =========================
# 🖼️ BANNER
# =========================
if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# 🎨 ESTILOS
# =========================
st.markdown("""
<style>
body {background-color: #eef2f7;}
h1, h2, h3 {color: #1f4e79;}

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
# 🚀 GITHUB (opcional)
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
# 🚨 VENCIMIENTOS
# =========================
def evaluar_vencimiento(ruta_archivo, nombre_archivo):

    nombre = nombre_archivo.lower()

    vigencias = {
        "capacitacion": 365,
        "programa": 365,
        "aviso": 180,
        "seguro": 365,
        "vtv": 365,
        "licencia": 365 * 5,
        "apto": 365,
    }

    tipo_detectado = None

    for tipo in vigencias:
        if tipo in nombre:
            tipo_detectado = tipo
            break

    if not tipo_detectado:
        return None

    fecha_archivo = datetime.fromtimestamp(os.path.getmtime(ruta_archivo))
    fecha_vencimiento = fecha_archivo + timedelta(days=vigencias[tipo_detectado])
    hoy = datetime.now()

    if hoy > fecha_vencimiento:
        return "🔴 VENCIDO"
    elif (fecha_vencimiento - hoy).days <= 30:
        return "🟡 POR VENCER"
    else:
        return "🟢 VIGENTE"

# =========================
# 📁 BASE
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(base_registros, exist_ok=True)

actividades = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

if not actividades:
    st.warning("⚠️ No hay actividades cargadas")

# =========================
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:
    actividad = st.selectbox("Actividad", actividades)
    tipo = st.text_input("Tipo (ats, permiso, checklist...)")

    if st.button("Guardar archivo"):

        # ✔ GUARDADO LOCAL (clave)
        ruta_local = os.path.join(base_registros, actividad, tipo)
        os.makedirs(ruta_local, exist_ok=True)

        ruta_archivo = os.path.join(ruta_local, archivo.name)

        with open(ruta_archivo, "wb") as f:
            f.write(archivo.getbuffer())

        # ☁️ intento GitHub
        subir_a_github(
            f"documentos/registros/{actividad}/{tipo}",
            archivo.name,
            archivo.getbuffer()
        )

        st.success("✔ Archivo guardado")

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
        actividad_sel = st.selectbox("Elegir:", actividades)

# =========================
# 📁 DOCUMENTACIÓN
# =========================
if actividad_sel:

    st.markdown(f"## 📁 {actividad_sel.upper()}")

    col1, col2 = st.columns(2)

    # =========================
    # 📄 DOCUMENTACIÓN BASE
    # =========================
    with col1:
        st.markdown("### 📄 Documentación base")

        carpeta = os.path.join(base_dir, actividad_sel)
        archivos = []

        for root, dirs, files in os.walk(carpeta):
            for file in files:
                if file.endswith(".pdf"):
                    archivos.append((file, os.path.join(root, file), root))

        if not archivos:
            st.warning("⚠️ No hay documentación base")
        else:
            for a, ruta, origen in archivos:

                nombre = a.replace("_", " ").replace(".pdf", "").title()
                origen_carpeta = os.path.basename(origen)

                st.markdown(f"""
                <div class="card">
                    📄 <b>{nombre}</b><br>
                    <span class="small-text">Origen: {origen_carpeta}</span>
                </div>
                """, unsafe_allow_html=True)

                with open(ruta, "rb") as f:
                    st.download_button("📥 Descargar", f, file_name=a)

        # ✔ CONTROL BASE
        st.markdown("### 📋 Control documentación base")

        requisitos_base = ["procedimiento", "permiso", "checklist", "emergencia"]
        faltantes = []

        for r in requisitos_base:
            if not any(r in a[0].lower() for a in archivos):
                faltantes.append(r)

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Completo")

    # =========================
    # 📊 REGISTROS
    # =========================
    with col2:
        st.markdown("### 📊 Estado real (REGISTROS)")

        requisitos = ["permiso", "ats", "checklist"]
        faltantes = []

        carpeta_reg = os.path.join(base_registros, actividad_sel)

        for r in requisitos:
            encontrado = False

            if os.path.exists(carpeta_reg):
                for root, dirs, files in os.walk(carpeta_reg):
                    for file in files:
                        if r in file.lower():
                            encontrado = True

            if not encontrado:
                faltantes.append(r)

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Registros completos")

# =========================
# 🚨 ALERTAS
# =========================
st.markdown("---")
st.markdown("## 🚨 Alertas")

alertas = []

for root, dirs, files in os.walk(base_registros):
    for file in files:
        if file.endswith(".pdf"):
            estado = evaluar_vencimiento(os.path.join(root, file), file)
            if estado and ("🔴" in estado or "🟡" in estado):
                alertas.append(f"{estado} - {file}")

if alertas:
    for a in alertas:
        color = "#ff4d4d" if "🔴" in a else "#ffa500"

        st.markdown(f"""
        <div style="background:{color}; padding:10px; border-radius:10px; color:white;">
            {a}
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✔ Sin alertas")

# =========================
# 📊 PANEL
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
    st.sidebar.markdown(f"📁 **{act}**")
