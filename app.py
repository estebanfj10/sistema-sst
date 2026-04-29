import streamlit as st
import os
from datetime import datetime, timedelta

# =========================
# 🧱 CONFIG GENERAL
# =========================
st.set_page_config(
    page_title="Sistema SST",
    page_icon="🦺",
    layout="wide"
)

# 🖼️ BANNER
st.image("banner.png", use_container_width=True)

st.title("🦺 Sistema de Seguridad e Higiene")

# =========================
# 🎨 ESTILOS PRO
# =========================
st.markdown("""
<style>
body {background-color: #eef2f7;}

h1 {color: #1f4e79; font-weight: 700;}
h2, h3 {color: #1f4e79;}

.card {
    background: white;
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    margin-bottom: 12px;
    transition: 0.2s;
}
.card:hover {
    transform: scale(1.01);
}

.small-text {
    color: gray;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 🚨 FUNCION VENCIMIENTOS
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
        estado = "🔴 VENCIDO"
    elif (fecha_vencimiento - hoy).days <= 30:
        estado = "🟡 POR VENCER"
    else:
        estado = "🟢 VIGENTE"

    return estado, fecha_vencimiento.strftime('%d/%m/%Y')

# =========================
# BASE DE DATOS
# =========================
base_dir = "documentos"
base_registros = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(base_registros, exist_ok=True)

actividades_disponibles = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d)) and d != "registros"
]

# =========================
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar documento (REGISTRO)")

archivo_subido = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo_subido:

    nombre = archivo_subido.name.lower()

    actividad_auto = None
    for act in actividades_disponibles:
        if act in nombre:
            actividad_auto = act
            break

    tipos = ["procedimiento", "checklist", "permiso", "ats", "capacitacion"]
    tipo_auto = None

    for t in tipos:
        if t in nombre:
            tipo_auto = t
            break

    actividad_final = st.selectbox(
        "Actividad",
        actividades_disponibles,
        index=actividades_disponibles.index(actividad_auto) if actividad_auto in actividades_disponibles else 0
    )

    tipo_final = st.text_input("Tipo de documento", value=tipo_auto if tipo_auto else "")

    if st.button("Guardar archivo"):

        ruta_guardado = os.path.join(base_registros, actividad_final, tipo_final)
        os.makedirs(ruta_guardado, exist_ok=True)

        ruta_completa = os.path.join(ruta_guardado, archivo_subido.name)

        with open(ruta_completa, "wb") as f:
            f.write(archivo_subido.getbuffer())

        st.success(f"✔ Guardado en REGISTROS/{actividad_final}/{tipo_final}")

# =========================
# 🔎 BUSCADOR
# =========================
st.markdown("### 🔎 Búsqueda de documentación")

consulta = st.text_input("", placeholder="Ej: altura, excavación...")

actividad_detectada = None

if consulta:
    consulta_lower = consulta.lower()

    for act in actividades_disponibles:
        if act in consulta_lower:
            actividad_detectada = act
            break

    if not actividad_detectada and actividades_disponibles:
        actividad_detectada = st.selectbox("Seleccione actividad:", actividades_disponibles)

# =========================
# 📁 CONTENIDO
# =========================
if actividad_detectada:

    st.markdown(f"## 📁 {actividad_detectada.upper()}")

    col1, col2 = st.columns(2)

    # =========================
    # 📄 BASE
    # =========================
    with col1:
        st.markdown("### 📄 Documentación base")

        carpeta = os.path.join(base_dir, actividad_detectada)
        archivos = []

        for root, dirs, files in os.walk(carpeta):
            for file in files:
                if file.endswith(".pdf"):
                    archivos.append((file, os.path.join(root, file), root))

        if len(archivos) == 0:
            st.info("📭 No hay documentación base")
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

    # =========================
    # 📊 REGISTROS
    # =========================
    with col2:
        st.markdown("### 📊 Estado real (REGISTROS)")

        requisitos = ["permiso", "ats", "checklist"]
        faltantes = []

        carpeta_reg = os.path.join(base_registros, actividad_detectada)

        for r in requisitos:
            encontrado = False

            if os.path.exists(carpeta_reg):
                for root, dirs, files in os.walk(carpeta_reg):
                    for file in files:
                        if r in file.lower():
                            encontrado = True
                            break

            if not encontrado:
                faltantes.append(r)

        if faltantes:
            st.error(f"❌ Faltan: {', '.join(faltantes)}")
        else:
            st.success("✔ Registros completos")

# =========================
# 🚨 ALERTAS PRO
# =========================
st.markdown("---")
st.markdown("## 🚨 Alertas de Vencimientos")

alertas = []

for root, dirs, files in os.walk(base_registros):
    for file in files:
        if file.endswith(".pdf"):
            ruta = os.path.join(root, file)
            resultado = evaluar_vencimiento(ruta, file)

            if resultado:
                estado, _ = resultado
                if "🔴" in estado or "🟡" in estado:
                    alertas.append(f"{estado} - {file}")

if alertas:
    for a in alertas:
        color = "#ff4d4d" if "🔴" in a else "#ffa500"

        st.markdown(f"""
        <div style="background:{color}; padding:10px; border-radius:10px; color:white; margin-bottom:5px;">
            {a}
        </div>
        """, unsafe_allow_html=True)
else:
    st.success("✔ Sin vencimientos críticos")

# =========================
# 📊 PANEL PRO
# =========================
st.markdown("---")
st.markdown("## 📊 Panel de Control")

total = len(actividades_disponibles)
docs = 0

for root, dirs, files in os.walk(base_registros):
    docs += len([f for f in files if f.endswith(".pdf")])

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="card">
        👷 <b>Actividades</b>
        <h2>{total}</h2>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card">
        📄 <b>Registros</b>
        <h2>{docs}</h2>
    </div>
    """, unsafe_allow_html=True)

# =========================
# SIDEBAR PRO
# =========================
st.sidebar.markdown("## 🦺 Sistema SST")

for act in actividades_disponibles:
    st.sidebar.markdown(f"📁 **{act}**")
