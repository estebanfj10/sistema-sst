import streamlit as st
import os
import requests
import base64

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

# =========================
# HEADER
# =========================
st.markdown("""
<style>
.header {
    background: linear-gradient(90deg, #0f172a, #1e3a8a);
    padding: 20px;
    border-radius: 10px;
    color: white;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>🦺 Sistema SST</h1>
    <p>Gestión de Seguridad e Higiene</p>
</div>
""", unsafe_allow_html=True)

st.image("banner.png", use_container_width=True)

# =========================
# FUNCIONES
# =========================
def normalizar(txt):
    return txt.lower().replace("_"," ").replace("-"," ").strip()

def subir_a_github(ruta, nombre, contenido):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    response = requests.put(
        url,
        json={
            "message": f"Subida {nombre}",
            "content": contenido_base64
        },
        headers={"Authorization": f"token {token}"}
    )

    if response.status_code in [200, 201]:
        return True
    else:
        st.error(f"❌ Error GitHub: {response.status_code}")
        try:
            st.json(response.json())
        except:
            pass
        return False


def obtener_base_github(ruta_relativa):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    resultados = []

    def recorrer(ruta):
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        r = requests.get(url, headers={"Authorization": f"token {token}"})

        if r.status_code == 200:
            for item in r.json():
                if item["type"] == "dir":
                    recorrer(item["path"])
                elif item["name"].lower().endswith(".pdf"):
                    resultados.append({
                        "nombre": item["name"],
                        "url": item["download_url"]
                    })

    recorrer(f"ventana/{ruta_relativa}")
    return resultados


def obtener_registros_github(ruta_relativa):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    resultados = []

    def recorrer(ruta):
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        r = requests.get(url, headers={"Authorization": f"token {token}"})

        if r.status_code != 200:
            return

        for item in r.json():
            if item["type"] == "dir":
                recorrer(item["path"])
            elif item["name"].lower().endswith(".pdf"):
                partes = item["path"].split("/")
                subtipo = partes[-2] if len(partes) > 2 else "general"

                resultados.append({
                    "nombre": item["name"],
                    "url": item["download_url"],
                    "subtipo": subtipo
                })

    recorrer(f"ventana/{ruta_relativa}")
    return resultados


def obtener_subcarpetas_github(ruta_relativa):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    carpetas = []

    url = f"https://api.github.com/repos/{repo}/contents/ventana/{ruta_relativa}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})

    if r.status_code == 200:
        for item in r.json():
            if item["type"] == "dir":
                carpetas.append(item["name"])

    return sorted(carpetas)

# =========================
# BASE
# =========================
base_dir = "ventana"

empresas = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
empresa_sel = st.selectbox("Empresa", empresas, key="empresa")

ruta_empresa = os.path.join(base_dir, empresa_sel)

obras = [d for d in os.listdir(ruta_empresa) if d.startswith("registro_obra")]
obra_sel = st.selectbox("Obra", obras, key="obra")

ruta_tipos = os.path.join(ruta_empresa, obra_sel)
tipos = os.listdir(ruta_tipos)

# =========================
# CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos, key="tipo_carga")

    subcarpetas = obtener_subcarpetas_github(f"{empresa_sel}/{obra_sel}/{tipo}")

    if subcarpetas:
        subtipo = st.selectbox("Subtipo", subcarpetas, key="subtipo_carga")
        ruta_github = f"ventana/{empresa_sel}/{obra_sel}/{tipo}/{subtipo}"
        ruta_local = os.path.join(base_dir, empresa_sel, obra_sel, tipo, subtipo)
    else:
        st.info("📂 Este tipo no tiene subcarpetas")
        ruta_github = f"ventana/{empresa_sel}/{obra_sel}/{tipo}"
        ruta_local = os.path.join(base_dir, empresa_sel, obra_sel, tipo)

    if st.button("Guardar"):

        os.makedirs(ruta_local, exist_ok=True)

        with open(os.path.join(ruta_local, archivo.name), "wb") as f:
            f.write(archivo.getbuffer())

        ok = subir_a_github(
            ruta_github,
            archivo.name,
            archivo.getbuffer()
        )

        if ok:
            st.success("✔ Subido correctamente")
        else:
            st.warning("⚠️ No se pudo subir")

# =========================
# CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Tipo", tipos, key="tipo_consulta")

# ===== BASE =====
st.markdown("### 📄 Documentación base")

base = obtener_base_github(f"{empresa_sel}/datos_bases/{tipo_sel}")

if base:
    for item in base:
        st.write(f"📄 {item['nombre']}")
        r = requests.get(item["url"])
        if r.status_code == 200:
            st.download_button("📥 Descargar", r.content, item["nombre"], key=f"base_{item['nombre']}")
else:
    st.warning("⚠️ Sin base")

# ===== REGISTROS =====
st.markdown("### 📊 Registros")

subcarpetas = obtener_subcarpetas_github(f"{empresa_sel}/{obra_sel}/{tipo_sel}")
reg = obtener_registros_github(f"{empresa_sel}/{obra_sel}/{tipo_sel}")

archivos_por_sub = {}
for item in reg:
    archivos_por_sub.setdefault(item["subtipo"], []).append(item)

# 🔹 CASO SIN SUBCARPETAS
if not subcarpetas:
    if reg:
        for item in reg:
            st.write(f"📄 {item['nombre']}")
            r = requests.get(item["url"])
            if r.status_code == 200:
                st.download_button(
                    "📥 Descargar",
                    r.content,
                    item["nombre"],
                    key=f"reg_{item['nombre']}"
                )
    else:
        st.warning("⚠️ Sin registros")

# 🔹 CASO CON SUBCARPETAS
else:
    for sub in subcarpetas:

        st.markdown(f"#### 📂 {sub}")

        archivos = archivos_por_sub.get(sub, [])

        if archivos:
            for item in archivos:
                st.write(f"📄 {item['nombre']}")
                r = requests.get(item["url"])
                if r.status_code == 200:
                    st.download_button(
                        "📥 Descargar",
                        r.content,
                        item["nombre"],
                        key=f"reg_{sub}_{item['nombre']}"
                    )
        else:
            st.caption("Sin archivos")
