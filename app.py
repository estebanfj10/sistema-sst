import io
import streamlit as st
import requests
from datetime import datetime
from collections import defaultdict

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

# =========================
# PAGE CONFIG — PRIMERO
# =========================
st.set_page_config(
    page_title="Sistema SST",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CSS DARK THEME
# =========================
st.markdown("""
<style>
.stApp { background-color: #0f172a; color: #e2e8f0; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #94a3b8 !important; }

h1, h2, h3, h4 { color: #f1f5f9 !important; }

.stSelectbox > div > div,
.stTextInput > div > div > input {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #60a5fa);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(59,130,246,0.4);
}
[data-testid="stFileUploader"] {
    background: #1e293b !important;
    border: 2px dashed #334155 !important;
    border-radius: 10px !important;
}
hr { border-color: #334155 !important; }

.card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
}
.card-title {
    font-size: 0.75rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;
}
.card-value { font-size: 1.5rem; font-weight: 700; color: #f1f5f9; }

.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.04em;
}
.badge-ok      { background:#14532d; color:#86efac; border:1px solid #166534; }
.badge-warn    { background:#451a03; color:#fcd34d; border:1px solid #78350f; }
.badge-danger  { background:#450a0a; color:#fca5a5; border:1px solid #7f1d1d; }
.badge-partial { background:#1e3a5f; color:#93c5fd; border:1px solid #1d4ed8; }

.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1e40af 100%);
    padding: 24px 28px; border-radius: 14px; margin-bottom: 24px;
    border: 1px solid #1e40af; box-shadow: 0 4px 24px rgba(30,64,175,0.3);
}
.main-header h1 { margin: 0 0 4px 0; font-size: 1.8rem; }
.main-header p  { margin: 0; color: #93c5fd !important; font-size: 0.9rem; }

label, .stMarkdown p { color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
# Cada usuario tiene una contraseña y un rol:
#   "admin"    → ve todo, incluida la gestión de carpetas
#   "operario" → solo Dashboard, Consulta y Cargar documento
USUARIOS = {
    "esteban": {"password": "seguridad2026", "rol": "admin"},
    # Agregá acá más usuarios operarios, por ejemplo:
    # "juan":  {"password": "obra2026", "rol": "operario"},
}

def login():
    st.markdown("""
    <div style="max-width:380px; margin:80px auto 0 auto;">
      <div style="background:linear-gradient(135deg,#0f172a,#1e3a8a);
                  border:1px solid #1e40af; border-radius:16px;
                  padding:36px 32px; box-shadow:0 8px 32px rgba(30,64,175,0.3);">
        <div style="text-align:center; margin-bottom:28px;">
          <span style="font-size:3rem;">🦺</span>
          <h2 style="color:#f1f5f9; margin:8px 0 4px;">Sistema SST</h2>
          <p style="color:#64748b; font-size:0.85rem; margin:0;">Seguridad y Salud en el Trabajo</p>
        </div>
    """, unsafe_allow_html=True)
    user = st.text_input("👤 Usuario", placeholder="Ingresá tu usuario")
    pwd  = st.text_input("🔑 Contraseña", type="password", placeholder="••••••••")
    if st.button("Ingresar →", use_container_width=True):
        datos_usuario = USUARIOS.get(user.lower())
        if datos_usuario and datos_usuario["password"] == pwd:
            st.session_state["login"]   = True
            st.session_state["usuario"] = user.lower()
            st.session_state["rol"]     = datos_usuario["rol"]
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    st.markdown("</div></div>", unsafe_allow_html=True)

if "login" not in st.session_state:
    st.session_state["login"] = False
if not st.session_state["login"]:
    login()
    st.stop()
if "rol" not in st.session_state:
    st.session_state["rol"] = "operario"

# =========================
# UTILIDADES
# =========================
def normalizar(txt):
    return txt.lower().replace("_", " ").replace("-", " ").strip()

def obtener_fecha(nombre):
    try:
        partes = nombre.replace(".pdf", "").split("_")
        for p in partes:
            if "-" in p:
                return datetime.strptime(p, "%d-%m-%Y")
    except:
        return None

def estado_fecha(fecha):
    if not fecha:
        return "sin_fecha"
    hoy = datetime.now()
    if fecha < hoy:
        return "vencido"
    if fecha.month == hoy.month and fecha.year == hoy.year:
        return "proximo"
    return "vigente"

def limpiar_nombre(nombre):
    """Normaliza un nombre para usarlo como carpeta (sin espacios ni tildes)."""
    reemplazos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n",
        "Á": "a", "É": "e", "Í": "i", "Ó": "o", "Ú": "u", "Ñ": "n",
    }
    n = nombre.strip().lower()
    for a, b in reemplazos.items():
        n = n.replace(a, b)
    n = n.replace(" ", "_")
    return "".join(c for c in n if c.isalnum() or c == "_")

# =========================
# GOOGLE DRIVE
# =========================
# Estructura en Drive (todo dentro de GDRIVE_ROOT_FOLDER_ID):
#
# 📁 raíz (compartida con el service account)
#   📁 empresa_n1/
#     📁 datos_bases/          ← base documental (fija)
#       📁 altura/ 📁 excavacion/ ...
#     📁 obra1/                ← registros por obra
#       📁 altura/ 📁 excavacion/ ...
#     📁 obra2/
# =========================

CARPETA_BASES = "datos_bases"
SCOPES = ["https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_drive_service():
    info = dict(st.secrets["gdrive_service_account"])
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

DRIVE = get_drive_service()
ROOT_FOLDER_ID = st.secrets["GDRIVE_ROOT_FOLDER_ID"]

@st.cache_data(ttl=300)
def _listar_hijos(parent_id, solo_carpetas=False, solo_pdfs=False):
    """Lista los archivos/carpetas directamente dentro de parent_id."""
    condiciones = [f"'{parent_id}' in parents", "trashed=false"]
    if solo_carpetas:
        condiciones.append("mimeType='application/vnd.google-apps.folder'")
    if solo_pdfs:
        condiciones.append("mimeType='application/pdf'")
    query = " and ".join(condiciones)
    items, page_token = [], None
    try:
        while True:
            resp = DRIVE.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                pageToken=page_token,
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
            ).execute()
            items.extend(resp.get("files", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    except HttpError:
        return []
    return items

def crear_carpeta_drive(nombre, parent_id):
    metadata = {"name": nombre, "mimeType": "application/vnd.google-apps.folder", "parents": [parent_id]}
    carpeta = DRIVE.files().create(body=metadata, fields="id", supportsAllDrives=True).execute()
    return carpeta["id"]

def resolver_id(*nombres, crear_si_no_existe=False):
    """
    Recorre la cadena de nombres de carpetas desde la raíz y devuelve el id
    de la última. Si crear_si_no_existe=True, crea las que falten.
    """
    actual = ROOT_FOLDER_ID
    for nombre in nombres:
        hijos = _listar_hijos(actual, solo_carpetas=True)
        encontrado = next((h for h in hijos if h["name"] == nombre), None)
        if encontrado:
            actual = encontrado["id"]
        elif crear_si_no_existe:
            actual = crear_carpeta_drive(nombre, actual)
        else:
            return None
    return actual

def url_descarga(file_id):
    return f"https://drive.google.com/uc?export=download&id={file_id}"

def hacer_publico(file_id):
    """Permite que cualquiera con el link pueda ver/descargar el archivo."""
    try:
        DRIVE.permissions().create(
            fileId=file_id, body={"role": "reader", "type": "anyone"}, supportsAllDrives=True
        ).execute()
    except HttpError:
        pass

def obtener_empresas():
    return [h["name"] for h in _listar_hijos(ROOT_FOLDER_ID, solo_carpetas=True)]

def obtener_obras(empresa):
    empresa_id = resolver_id(empresa)
    if not empresa_id:
        return []
    return [h["name"] for h in _listar_hijos(empresa_id, solo_carpetas=True) if h["name"] != CARPETA_BASES]

def obtener_tipos(*ruta_nombres):
    """Subcarpetas dentro de la ruta indicada (empresa, obra) o (empresa, datos_bases)."""
    parent_id = resolver_id(*ruta_nombres)
    if not parent_id:
        return []
    return [h["name"] for h in _listar_hijos(parent_id, solo_carpetas=True)]

def obtener_pdfs_carpeta(*ruta_nombres):
    """
    Devuelve lista de PDFs (y PDFs en subcarpetas) de una ruta.
    ruta_nombres, ej: (empresa, "datos_bases", "altura")
    """
    res = []
    parent_id = resolver_id(*ruta_nombres)
    if not parent_id:
        return res
    hijos = _listar_hijos(parent_id)
    for h in hijos:
        if h["mimeType"] == "application/pdf":
            res.append({"nombre": h["name"], "url": url_descarga(h["id"]), "id": h["id"], "subtipo": "general"})
        elif h["mimeType"] == "application/vnd.google-apps.folder":
            sub_hijos = _listar_hijos(h["id"], solo_pdfs=True)
            for j in sub_hijos:
                res.append({"nombre": j["name"], "url": url_descarga(j["id"]), "id": j["id"], "subtipo": h["name"]})
    return res

def subir_a_drive(ruta_nombres, nombre_archivo, contenido_bytes):
    """Sube un PDF a la ruta indicada, creando las carpetas que falten."""
    try:
        parent_id = resolver_id(*ruta_nombres, crear_si_no_existe=True)
        media = MediaIoBaseUpload(io.BytesIO(contenido_bytes), mimetype="application/pdf", resumable=True)
        metadata = {"name": nombre_archivo, "parents": [parent_id]}
        archivo = DRIVE.files().create(
            body=metadata, media_body=media, fields="id", supportsAllDrives=True
        ).execute()
        hacer_publico(archivo["id"])
        return True
    except HttpError:
        return False

def renombrar_carpeta(ruta_nombres, nuevo_nombre):
    folder_id = resolver_id(*ruta_nombres)
    if not folder_id:
        return False, "No se encontró la carpeta."
    try:
        DRIVE.files().update(fileId=folder_id, body={"name": nuevo_nombre}, supportsAllDrives=True).execute()
        return True, "Carpeta renombrada correctamente."
    except HttpError as e:
        return False, str(e)

def eliminar_carpeta(ruta_nombres):
    """Mueve la carpeta a la papelera de Drive (se puede restaurar desde ahí)."""
    folder_id = resolver_id(*ruta_nombres)
    if not folder_id:
        return False, "No se encontró la carpeta."
    try:
        DRIVE.files().update(fileId=folder_id, body={"trashed": True}, supportsAllDrives=True).execute()
        return True, "Carpeta movida a la papelera de Drive."
    except HttpError as e:
        return False, str(e)

# =========================
# CONTROL DE CUMPLIMIENTO
# =========================
REGLAS = {
    "altura":            {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "excavacion":        {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "caliente":          {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "espacio_confinado": {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "izaje":             {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "electricidad":      {"base": ["procedimiento"], "registros": ["permiso"]},
    "herramientas":      {"base": [],                "registros": ["checklist"]},
    "epp":               {"base": [],                "registros": []},
    "accidentes":        {"base": [],                "registros": []},
    "capacitacion":      {"base": [],                "registros": []},
    "default":           {"base": ["procedimiento"], "registros": ["checklist"]},
}

def cumple(archivos, palabra):
    return any(palabra in normalizar(a["nombre"]) for a in archivos)

def cumple_subtipo(archivos, palabra):
    return any(a["subtipo"] == palabra for a in archivos)

def evaluar_control(tipo, base_docs, reg_docs):
    reglas    = REGLAS.get(tipo, REGLAS["default"])
    faltantes = []
    for r in reglas["base"]:
        if not cumple(base_docs, r):
            faltantes.append(f"Base: {r}")
    for r in reglas["registros"]:
        if not (cumple(reg_docs, r) or cumple_subtipo(reg_docs, r)):
            faltantes.append(f"Registro: {r}")
    total = len(reglas["base"]) + len(reglas["registros"])
    if not faltantes:
        return "completo", faltantes
    if total > 0 and len(faltantes) == total:
        return "critico", faltantes
    return "parcial", faltantes

# =========================
# ALERTAS
# =========================
def obtener_alertas(empresa, obra, tipos):
    alertas = []
    for t in tipos:
        docs = obtener_pdfs_carpeta(empresa, obra, t)
        for d in docs:
            f   = obtener_fecha(d["nombre"])
            est = estado_fecha(f)
            if est in ["vencido", "proximo"]:
                alertas.append({"archivo": d["nombre"], "tipo": t, "estado": est})
    return alertas

def resumen_general(empresa, obra, tipos):
    data = []
    for t in tipos:
        base_docs = obtener_pdfs_carpeta(empresa, CARPETA_BASES, t)
        reg_docs  = obtener_pdfs_carpeta(empresa, obra, t)
        estado, faltantes = evaluar_control(t, base_docs, reg_docs)
        data.append({"tipo": t, "estado": estado, "faltantes": faltantes})
    return data

# =========================
# WHATSAPP (CallMeBot)
# =========================
CALLMEBOT_PHONE  = st.secrets.get("CALLMEBOT_PHONE", "")
CALLMEBOT_APIKEY = st.secrets.get("CALLMEBOT_APIKEY", "")

def whatsapp_configurado():
    return bool(CALLMEBOT_PHONE and CALLMEBOT_APIKEY)

def enviar_whatsapp(mensaje):
    """
    Envía un mensaje de WhatsApp usando CallMeBot (gratis).
    Requiere CALLMEBOT_PHONE y CALLMEBOT_APIKEY en secrets.
    """
    if not whatsapp_configurado():
        return False, "Faltan configurar CALLMEBOT_PHONE y CALLMEBOT_APIKEY en secrets."
    import urllib.parse
    texto = urllib.parse.quote(mensaje)
    url = (
        f"https://api.callmebot.com/whatsapp.php"
        f"?phone={CALLMEBOT_PHONE}&text={texto}&apikey={CALLMEBOT_APIKEY}"
    )
    try:
        r = requests.get(url, timeout=15)
        return (r.status_code == 200), r.text
    except Exception as e:
        return False, str(e)

def armar_mensaje_alertas(empresa, obra, alertas):
    if not alertas:
        return f"✅ SST | {empresa} - {obra}: sin vencimientos pendientes."
    vencidos = [a for a in alertas if a["estado"] == "vencido"]
    proximos = [a for a in alertas if a["estado"] == "proximo"]
    lineas = [f"🦺 SST | {empresa} - {obra}"]
    if vencidos:
        lineas.append(f"\n🚨 VENCIDOS ({len(vencidos)}):")
        for a in vencidos:
            lineas.append(f"- {a['archivo']} ({a['tipo']})")
    if proximos:
        lineas.append(f"\n⚠️ PRÓXIMOS A VENCER ({len(proximos)}):")
        for a in proximos:
            lineas.append(f"- {a['archivo']} ({a['tipo']})")
    return "\n".join(lineas)

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 8px 0; text-align:center;">
        <span style="font-size:2.2rem;">🦺</span>
        <p style="color:#93c5fd; font-weight:700; font-size:1rem; margin:4px 0 0 0;">SST</p>
        <p style="color:#475569; font-size:0.75rem; margin:0;">Sistema de Seguridad</p>
    </div>
    <hr style="border-color:#334155; margin:12px 0;">
    """, unsafe_allow_html=True)

    empresas = obtener_empresas()
    if not empresas:
        st.error("⚠️ No se pudo leer la carpeta de Drive. Verificá GDRIVE_ROOT_FOLDER_ID y que esté compartida con el service account.")
        st.stop()

    empresa = st.selectbox("🏢 Empresa", empresas, key="empresa")

    obras = obtener_obras(empresa)
    if not obras:
        st.warning("Sin obras cargadas para esta empresa.")
        st.stop()

    obra = st.selectbox("🏗️ Obra", obras, key="obra")

    st.markdown("<hr style='border-color:#334155; margin:12px 0;'>", unsafe_allow_html=True)

    opciones_nav = ["📊 Dashboard", "🔎 Consulta", "📤 Cargar documento"]
    if st.session_state["rol"] == "admin":
        opciones_nav.append("⚙️ Gestionar carpetas")

    seccion = st.radio(
        "Navegación",
        opciones_nav,
        key="seccion"
    )

    st.markdown("<hr style='border-color:#334155; margin:12px 0;'>", unsafe_allow_html=True)

    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔒 Cerrar sesión", use_container_width=True):
        st.session_state["login"] = False
        st.rerun()

    st.markdown(f"""
    <div style="margin-top:20px; text-align:center;">
        <p style="color:#334155; font-size:0.7rem; margin:0;">
            Usuario: <span style="color:#64748b">{st.session_state['usuario']}</span>
            ({st.session_state['rol']})
        </p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# HEADER
# =========================
tipos = obtener_tipos(empresa, obra)

st.markdown(f"""
<div class="main-header">
    <h1>🦺 Sistema SST</h1>
    <p>📍 {empresa} &nbsp;›&nbsp; {obra}</p>
</div>
""", unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if seccion == "📊 Dashboard":
    alertas = obtener_alertas(empresa, obra, tipos)
    resumen = resumen_general(empresa, obra, tipos)

    vencidos  = sum(1 for a in alertas if a["estado"] == "vencido")
    proximos  = sum(1 for a in alertas if a["estado"] == "proximo")
    completos = sum(1 for r in resumen if r["estado"] == "completo")
    criticos  = sum(1 for r in resumen if r["estado"] == "critico")

    col_titulo, col_wp = st.columns([4, 1])
    with col_wp:
        if st.button("📲 Enviar por WhatsApp", use_container_width=True):
            if not whatsapp_configurado():
                st.warning("⚠️ Configurá CALLMEBOT_PHONE y CALLMEBOT_APIKEY en secrets para usar esta función.")
            else:
                with st.spinner("Enviando..."):
                    msg = armar_mensaje_alertas(empresa, obra, alertas)
                    ok, resp = enviar_whatsapp(msg)
                if ok:
                    st.success("✅ Mensaje enviado por WhatsApp")
                else:
                    st.error(f"❌ No se pudo enviar: {resp}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="card">
            <div class="card-title">Tipos activos</div>
            <div class="card-value">{len(tipos)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="card">
            <div class="card-title">Completos</div>
            <div class="card-value" style="color:#86efac">{completos}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="card">
            <div class="card-title">Próx. a vencer</div>
            <div class="card-value" style="color:#fcd34d">{proximos}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="card">
            <div class="card-title">Vencidos</div>
            <div class="card-value" style="color:#fca5a5">{vencidos}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 📅 Vencimientos")
        if alertas:
            for a in alertas:
                badge = '<span class="badge badge-danger">VENCIDO</span>' \
                        if a["estado"] == "vencido" \
                        else '<span class="badge badge-warn">PRÓXIMO</span>'
                st.markdown(f"""<div class="card" style="padding:12px 16px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.85rem;color:#cbd5e1">{a['archivo']}</span>
                        {badge}
                    </div>
                    <div style="color:#475569;font-size:0.75rem;margin-top:4px;">📁 {a['tipo']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="card" style="text-align:center;padding:24px;">
                <span style="font-size:2rem;">✅</span>
                <p style="color:#86efac;margin:8px 0 0 0;font-weight:600;">Sin vencimientos</p>
            </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown("### 📊 Cumplimiento por tipo")
        badge_map = {
            "completo": ("badge-ok",      "COMPLETO"),
            "parcial":  ("badge-partial", "PARCIAL"),
            "critico":  ("badge-danger",  "CRÍTICO"),
        }
        for r in resumen:
            cls, lbl = badge_map.get(r["estado"], ("badge-partial", r["estado"].upper()))
            falt_html = ""
            if r["faltantes"]:
                items = "".join(f'<li style="color:#94a3b8;font-size:0.78rem">{f}</li>'
                                for f in r["faltantes"])
                falt_html = f'<ul style="margin:6px 0 0 16px;padding:0">{items}</ul>'
            st.markdown(f"""<div class="card" style="padding:12px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.9rem;color:#e2e8f0;font-weight:500;">{r['tipo']}</span>
                    <span class="badge {cls}">{lbl}</span>
                </div>
                {falt_html}
            </div>""", unsafe_allow_html=True)

# =========================
# CONSULTA
# =========================
elif seccion == "🔎 Consulta":
    st.markdown("### 🔎 Consulta de documentos")

    if not tipos:
        st.warning("Esta obra no tiene tipos de registro cargados.")
        st.stop()

    tipo_sel = st.selectbox("Seleccioná el tipo", tipos, key="tipo_consulta")

    base_docs = obtener_pdfs_carpeta(empresa, CARPETA_BASES, tipo_sel)
    reg_docs  = obtener_pdfs_carpeta(empresa, obra, tipo_sel)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Documentos Base")
        if base_docs:
            for i, b in enumerate(base_docs):
                st.markdown(f"""<div class="card" style="padding:12px 16px;margin-bottom:6px;">
                    <div style="color:#e2e8f0;font-size:0.85rem;margin-bottom:8px;">📄 {b['nombre']}</div>
                </div>""", unsafe_allow_html=True)
                st.link_button("📥 Descargar", b["url"], key=f"base_{i}", use_container_width=True)
        else:
            st.markdown("""<div class="card" style="text-align:center;color:#475569;padding:20px;">
                Sin documentos base para este tipo
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📋 Registros de la obra")
        if reg_docs:
            grupos = defaultdict(list)
            for r in reg_docs:
                grupos[r["subtipo"]].append(r)

            for subtipo, archivos in grupos.items():
                if subtipo != "general":
                    st.markdown(f"""<p style="color:#64748b;font-size:0.8rem;
                        text-transform:uppercase;letter-spacing:0.08em;
                        margin:12px 0 6px 0;">📁 {subtipo}</p>""",
                        unsafe_allow_html=True)
                for i, a in enumerate(archivos):
                    f         = obtener_fecha(a["nombre"])
                    est       = estado_fecha(f)
                    badge_cls = {"vencido":"badge-danger","proximo":"badge-warn","vigente":"badge-ok"}.get(est,"")
                    badge_lbl = {"vencido":"VENCIDO","proximo":"PRÓXIMO","vigente":"VIGENTE"}.get(est,"")
                    badge_html = f'<span class="badge {badge_cls}">{badge_lbl}</span>' if badge_cls else ""
                    st.markdown(f"""<div class="card" style="padding:10px 14px;margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:#cbd5e1;font-size:0.82rem;">📄 {a['nombre']}</span>
                            {badge_html}
                        </div>
                    </div>""", unsafe_allow_html=True)
                    st.link_button("📥 Descargar", a["url"],
                                   key=f"reg_{subtipo}_{i}", use_container_width=True)
        else:
            st.markdown("""<div class="card" style="text-align:center;color:#475569;padding:20px;">
                Sin registros cargados para este tipo
            </div>""", unsafe_allow_html=True)

    estado, faltantes = evaluar_control(tipo_sel, base_docs, reg_docs)
    badge_map = {
        "completo": ("badge-ok",      "✅ COMPLETO"),
        "parcial":  ("badge-partial", "⚠️ PARCIAL"),
        "critico":  ("badge-danger",  "🚨 CRÍTICO"),
    }
    cls, lbl = badge_map.get(estado, ("badge-partial", estado.upper()))
    falt_html = ""
    if faltantes:
        items = "".join(f'<li style="color:#fca5a5;font-size:0.85rem;margin:4px 0">{f}</li>'
                        for f in faltantes)
        falt_html = f'<ul style="margin:10px 0 0 18px;padding:0">{items}</ul>'

    st.markdown(f"""<div class="card" style="margin-top:24px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
            <span style="color:#94a3b8;font-weight:600;font-size:0.9rem;">🚨 Estado de control</span>
            <span class="badge {cls}">{lbl}</span>
        </div>
        {falt_html}
    </div>""", unsafe_allow_html=True)

# =========================
# CARGAR DOCUMENTO
# =========================
elif seccion == "📤 Cargar documento":
    st.markdown("### 📤 Cargar documento")

    st.markdown("""<div class="card" style="margin-bottom:20px;border-color:#1e40af;">
        <p style="color:#93c5fd;margin:0;font-size:0.85rem;">
            📌 Solo se aceptan <strong>PDF</strong>.
            Incluí la fecha de vencimiento en el nombre como <code>nombre_DD-MM-YYYY.pdf</code> si aplica.
        </p>
    </div>""", unsafe_allow_html=True)

    archivo = st.file_uploader("Seleccioná el PDF", type=["pdf"])

    if archivo:
        col1, col2 = st.columns(2)
        with col1:
            tipo_carga = st.selectbox("Tipo de documento", tipos, key="tipo_carga")
        with col2:
            subs = obtener_tipos(empresa, obra, tipo_carga)
            subtipo_sel = st.selectbox("Subtipo", ["— sin subtipo —"] + subs, key="subtipo_carga")

        ruta = (empresa, obra, tipo_carga)
        if subtipo_sel != "— sin subtipo —":
            ruta += (subtipo_sel,)

        st.markdown(f"""<div class="card" style="margin:12px 0;">
            <div class="card-title">Destino en Drive</div>
            <div style="color:#93c5fd;font-size:0.85rem;font-family:monospace;">
                {" / ".join(ruta)} / {archivo.name}
            </div>
        </div>""", unsafe_allow_html=True)

        notificar_wp = st.checkbox(
            "📲 Notificarme por WhatsApp cuando se suba este documento",
            value=False,
            disabled=not whatsapp_configurado(),
            help=None if whatsapp_configurado() else "Configurá CALLMEBOT_PHONE y CALLMEBOT_APIKEY en secrets"
        )

        if st.button("⬆️ Subir documento", use_container_width=True):
            with st.spinner("Subiendo..."):
                ok = subir_a_drive(ruta, archivo.name, archivo.getbuffer())
            if ok:
                st.success("✅ Documento subido correctamente")
                if notificar_wp:
                    msg = (
                        f"📤 SST | Nuevo documento cargado\n"
                        f"Empresa: {empresa}\nObra: {obra}\n"
                        f"Tipo: {tipo_carga}"
                        + (f" / {subtipo_sel}" if subtipo_sel != "— sin subtipo —" else "")
                        + f"\nArchivo: {archivo.name}"
                    )
                    wp_ok, wp_resp = enviar_whatsapp(msg)
                    if wp_ok:
                        st.success("✅ Notificación de WhatsApp enviada")
                    else:
                        st.warning(f"⚠️ Documento subido, pero falló el WhatsApp: {wp_resp}")
                st.cache_data.clear()
            else:
                st.error("❌ Error al subir. Verificá los permisos del service account en Drive.")

# =========================
# GESTIONAR CARPETAS
# =========================
elif seccion == "⚙️ Gestionar carpetas":
    if st.session_state["rol"] != "admin":
        st.error("🚫 No tenés permisos para acceder a esta sección.")
        st.stop()
    st.markdown("### ⚙️ Gestión de carpetas")
    st.markdown("""<div class="card" style="margin-bottom:20px;border-color:#1e40af;">
        <p style="color:#93c5fd;margin:0;font-size:0.85rem;">
            📌 Acá podés crear, renombrar y eliminar empresas, obras, tipos y subtipos directamente en Drive.
            Los nombres se normalizan automáticamente (sin espacios ni tildes).
        </p>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🏢 Empresa", "🏗️ Obra", "📁 Tipo", "📂 Subtipo", "✏️ Modificar / Eliminar"]
    )

    # --- Nueva empresa ---
    with tab1:
        st.markdown("#### Crear nueva empresa")
        nombre_empresa = st.text_input("Nombre de la empresa", key="in_empresa")
        if st.button("➕ Crear empresa", key="btn_empresa"):
            if not nombre_empresa:
                st.warning("Ingresá un nombre.")
            else:
                slug = limpiar_nombre(nombre_empresa)
                with st.spinner("Creando..."):
                    resolver_id(slug, crear_si_no_existe=True)
                    resolver_id(slug, CARPETA_BASES, crear_si_no_existe=True)
                st.success(f"✅ Empresa '{slug}' creada")
                st.cache_data.clear()

    # --- Nueva obra ---
    with tab2:
        st.markdown("#### Crear nueva obra")
        st.caption("Elegí a qué empresa (ya existente) se le agrega la obra.")
        empresa_obra = st.selectbox("Empresa", empresas, key="empresa_destino_obra")
        nombre_obra = st.text_input("Nombre de la obra", key="in_obra")
        if st.button("➕ Crear obra", key="btn_obra"):
            if not nombre_obra:
                st.warning("Ingresá un nombre.")
            else:
                slug = limpiar_nombre(nombre_obra)
                with st.spinner("Creando..."):
                    resolver_id(empresa_obra, slug, crear_si_no_existe=True)
                st.success(f"✅ Obra '{slug}' creada en {empresa_obra}")
                st.cache_data.clear()

    # --- Nuevo tipo ---
    with tab3:
        st.markdown("#### Crear nuevo tipo de registro")
        st.caption("Elegí en qué empresa y en qué carpeta (base documental u obra, ambas ya existentes) va el tipo.")
        empresa_tipo = st.selectbox("Empresa", empresas, key="empresa_destino_tipo")
        obras_tipo = obtener_obras(empresa_tipo)
        destino_tipo = st.selectbox(
            "¿Dónde va este tipo?",
            [f"📚 Base documental ({CARPETA_BASES})"] + [f"🏗️ Obra: {o}" for o in obras_tipo],
            key="destino_tipo"
        )
        nombre_tipo = st.text_input("Nombre del tipo (ej: altura, excavacion)", key="in_tipo")
        if st.button("➕ Crear tipo", key="btn_tipo"):
            if not nombre_tipo:
                st.warning("Ingresá un nombre.")
            else:
                slug = limpiar_nombre(nombre_tipo)
                if destino_tipo.startswith("📚"):
                    ruta_padre = (empresa_tipo, CARPETA_BASES)
                else:
                    obra_destino = destino_tipo.replace("🏗️ Obra: ", "")
                    ruta_padre = (empresa_tipo, obra_destino)
                with st.spinner("Creando..."):
                    resolver_id(*ruta_padre, slug, crear_si_no_existe=True)
                st.success(f"✅ Tipo '{slug}' creado en {' / '.join(ruta_padre)}")
                st.cache_data.clear()
        st.caption("💡 Tip: si el tipo es de un permiso de trabajo (altura, excavación, caliente, izaje, espacio confinado), "
                   "creálo también dentro de la base documental y dentro de cada obra que lo necesite.")

    # --- Nuevo subtipo ---
    with tab4:
        st.markdown("#### Crear nuevo subtipo")
        st.caption("Un subtipo es una subcarpeta dentro de un tipo ya existente (ej: dentro de 'altura' → 'permiso', 'ats').")
        empresa_subtipo = st.selectbox("Empresa", empresas, key="empresa_destino_subtipo")
        obras_subtipo = obtener_obras(empresa_subtipo)
        origen_subtipo = st.selectbox(
            "¿Dentro de qué carpeta va?",
            [f"📚 Base documental ({CARPETA_BASES})"] + [f"🏗️ Obra: {o}" for o in obras_subtipo],
            key="origen_subtipo"
        )
        if origen_subtipo.startswith("📚"):
            ruta_base_subtipo = (empresa_subtipo, CARPETA_BASES)
        else:
            obra_sel_subtipo = origen_subtipo.replace("🏗️ Obra: ", "")
            ruta_base_subtipo = (empresa_subtipo, obra_sel_subtipo)

        tipos_disponibles = obtener_tipos(*ruta_base_subtipo)
        if not tipos_disponibles:
            st.warning("Esa carpeta todavía no tiene tipos creados. Creá un tipo primero en la pestaña anterior.")
        else:
            tipo_padre = st.selectbox("Tipo", tipos_disponibles, key="in_tipo_padre_subtipo")
            nombre_subtipo = st.text_input("Nombre del subtipo (ej: permiso, ats, checklist)", key="in_subtipo")
            if st.button("➕ Crear subtipo", key="btn_subtipo"):
                if not nombre_subtipo:
                    st.warning("Ingresá un nombre.")
                else:
                    slug = limpiar_nombre(nombre_subtipo)
                    with st.spinner("Creando..."):
                        resolver_id(*ruta_base_subtipo, tipo_padre, slug, crear_si_no_existe=True)
                    st.success(f"✅ Subtipo '{slug}' creado en {' / '.join(ruta_base_subtipo)} / {tipo_padre}")
                    st.cache_data.clear()

    # --- Modificar / Eliminar ---
    with tab5:
        st.markdown("#### ✏️ Renombrar o eliminar una carpeta")
        st.markdown("""<div class="card" style="border-color:#1e40af;margin-bottom:16px;">
            <p style="color:#93c5fd;margin:0;font-size:0.8rem;">
                ℹ️ Al eliminar, la carpeta se mueve a la <strong>papelera de Drive</strong> (se puede restaurar
                desde ahí si fue un error). No se borra de forma permanente al instante.
            </p>
        </div>""", unsafe_allow_html=True)

        nivel = st.selectbox(
            "¿Qué querés modificar?",
            ["Empresa", "Obra", "Tipo", "Subtipo"],
            key="nivel_modificar"
        )

        ruta_objetivo = None
        nombre_actual = None

        if nivel == "Empresa":
            empresa_m = st.selectbox("Empresa", empresas, key="m_empresa")
            ruta_objetivo = (empresa_m,)
            nombre_actual = empresa_m

        elif nivel == "Obra":
            empresa_m = st.selectbox("Empresa", empresas, key="m_obra_empresa")
            obras_m = obtener_obras(empresa_m)
            if obras_m:
                obra_m = st.selectbox("Obra", obras_m, key="m_obra")
                ruta_objetivo = (empresa_m, obra_m)
                nombre_actual = obra_m
            else:
                st.info("Esta empresa no tiene obras.")

        elif nivel == "Tipo":
            empresa_m = st.selectbox("Empresa", empresas, key="m_tipo_empresa")
            obras_m = obtener_obras(empresa_m)
            origen_m = st.selectbox(
                "¿Dónde está el tipo?",
                [f"📚 Base documental ({CARPETA_BASES})"] + [f"🏗️ Obra: {o}" for o in obras_m],
                key="m_tipo_origen"
            )
            ruta_padre_m = (empresa_m, CARPETA_BASES) if origen_m.startswith("📚") \
                else (empresa_m, origen_m.replace("🏗️ Obra: ", ""))
            tipos_m = obtener_tipos(*ruta_padre_m)
            if tipos_m:
                tipo_m = st.selectbox("Tipo", tipos_m, key="m_tipo")
                ruta_objetivo = ruta_padre_m + (tipo_m,)
                nombre_actual = tipo_m
            else:
                st.info("Esa carpeta no tiene tipos cargados.")

        elif nivel == "Subtipo":
            empresa_m = st.selectbox("Empresa", empresas, key="m_sub_empresa")
            obras_m = obtener_obras(empresa_m)
            origen_m = st.selectbox(
                "¿Dónde está el tipo?",
                [f"📚 Base documental ({CARPETA_BASES})"] + [f"🏗️ Obra: {o}" for o in obras_m],
                key="m_sub_origen"
            )
            ruta_padre_m = (empresa_m, CARPETA_BASES) if origen_m.startswith("📚") \
                else (empresa_m, origen_m.replace("🏗️ Obra: ", ""))
            tipos_m = obtener_tipos(*ruta_padre_m)
            if tipos_m:
                tipo_m = st.selectbox("Tipo", tipos_m, key="m_sub_tipo")
                subtipos_m = obtener_tipos(*ruta_padre_m, tipo_m)
                if subtipos_m:
                    subtipo_m = st.selectbox("Subtipo", subtipos_m, key="m_subtipo")
                    ruta_objetivo = ruta_padre_m + (tipo_m, subtipo_m)
                    nombre_actual = subtipo_m
                else:
                    st.info("Ese tipo no tiene subtipos cargados.")
            else:
                st.info("Esa carpeta no tiene tipos cargados.")

        if ruta_objetivo:
            st.markdown(f"""<div class="card" style="padding:10px 14px;margin:12px 0;">
                <div style="color:#93c5fd;font-size:0.8rem;font-family:monospace;">📁 {" / ".join(ruta_objetivo)}</div>
            </div>""", unsafe_allow_html=True)

            col_ren, col_del = st.columns(2)

            with col_ren:
                st.markdown("**Renombrar**")
                nuevo_nombre = st.text_input("Nuevo nombre", value=nombre_actual, key="m_nuevo_nombre")
                if st.button("✏️ Renombrar", key="m_btn_renombrar", use_container_width=True):
                    nuevo_slug = limpiar_nombre(nuevo_nombre)
                    if not nuevo_slug or nuevo_slug == nombre_actual:
                        st.warning("Ingresá un nombre distinto al actual.")
                    else:
                        with st.spinner("Renombrando..."):
                            ok, msg = renombrar_carpeta(ruta_objetivo, nuevo_slug)
                        if ok:
                            st.success(f"✅ {msg}")
                            st.cache_data.clear()
                        else:
                            st.error(f"❌ {msg}")

            with col_del:
                st.markdown("**Eliminar**")
                confirmar = st.checkbox(f"Confirmo que quiero eliminar '{nombre_actual}' y todo su contenido",
                                         key="m_confirmar_borrado")
                if st.button("🗑️ Eliminar carpeta", key="m_btn_eliminar", use_container_width=True,
                             disabled=not confirmar):
                    with st.spinner("Eliminando..."):
                        ok, msg = eliminar_carpeta(ruta_objetivo)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.cache_data.clear()
                    else:
                        st.error(f"❌ {msg}")

    st.markdown("<hr style='border-color:#334155; margin:24px 0 16px 0;'>", unsafe_allow_html=True)
    st.markdown("#### 📲 Probar WhatsApp")
    if whatsapp_configurado():
        if st.button("Enviar mensaje de prueba"):
            with st.spinner("Enviando..."):
                ok, resp = enviar_whatsapp("🦺 Prueba del Sistema SST: la conexión con WhatsApp funciona correctamente.")
            if ok:
                st.success("✅ Mensaje de prueba enviado")
            else:
                st.error(f"❌ {resp}")
    else:
        st.info("Para activar WhatsApp agregá `CALLMEBOT_PHONE` y `CALLMEBOT_APIKEY` en tus secrets de Streamlit.")
