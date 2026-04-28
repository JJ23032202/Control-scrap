import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
from supabase import create_client
import streamlit as st

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =====================================================
# CONFIGURACIÓN
# =====================================================
MODO_CLOUD = True
st.set_page_config(page_title="Control de Scrap", layout="wide")

st.markdown("""
<style>

/* ===== COLORES BASE ===== */
:root {
    --azul-principal: #0F2A44;
    --azul-claro: #1F4E79;
    --naranja: #E36B2C;
    --verde-ok: #2ECC71;
    --rojo-error: #E74C3C;
    --gris-fondo: #F2F2F2;
    --azul-oscuro: #061A2C;
}

/* ===== FONDO APP ===== */
.stApp {
    background-color: var(--azul-oscuro);
}

/* ===== TÍTULOS ===== */
h1, h2, h3 {
    color: var(--azul-principal);
    font-weight: 700;
}

/* ===== BOTONES ===== */
div.stButton > button {
    background-color: var(--naranja);
    color: white;
    border-radius: 10px;
    border: none;
    height: 3.5em;
    font-size: 1.1em;
    font-weight: bold;
}

div.stButton > button:hover {
    background-color: var(--azul-claro);
}

/* ===== BOTÓN TECLADO ===== */
button[kind="secondary"] {
    background-color: var(--naranja) !important;
    color: white !important;
}

/* ===== INPUTS ===== */
input, select, textarea {
    border-radius: 8px !important;
    border: 2px solid var(--naranja) !important;
    font-size: 1.05em !important;
}

/* ===== SELECTBOX ===== */
div[data-baseweb="select"] {
    border-radius: 8px;
}

/* ===== MENSAJES ===== */
div.stAlert-success {
    background-color: var(--verde-ok);
    color: white;
    font-weight: bold;
}

div.stAlert-error {
    background-color: var(--rojo-error);
    color: white;
    font-weight: bold;
}

/* ===== IMÁGENES ===== */
img {
    border: 4px solid var(--azul-principal);
    border-radius: 10px;
    padding: 4px;
    background-color: white;
}

/* ===== MODAL TECLADO ===== */
section[data-testid="stDialog"] {
    border-radius: 15px;
    border: 4px solid var(--naranja);
}

</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = r"C:\Users\24tjo8\OneDrive - Aptiv\SCRAP\datos_scrap.xlsx"
IMAGES_PATH = os.path.join(BASE_DIR, "imagenes_scrap")

# =====================================================
# INICIALIZAR SESSION STATE
# =====================================================


def init_state():
    defaults = {
        "pantalla": "menu",
        "parte": "",
        "maquina": "",
        "libras": "",
        "ultimo_scan": "",
        "abrir_teclado": False,
        "mostrar_guardado": False,
        "form_uid": 0,
        "fecha": datetime.now().date(),
        "nuevo_uid": 0,
        "nuevo_guardado": False,
        "nuevo_seccion":None,
        "filtro_uid": 0,
        "causa_qr":"",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    
if "mostrar_guardado" not in st.session_state:
    st.session_state.mostrar_guardado = False


init_state()

# =====================================================
# UTILIDADES
# =====================================================

def leer_excel(hoja, columnas=None):
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=hoja)
    except:
        df = pd.DataFrame()

    if columnas:
        for c in columnas:
            if c not in df.columns:
                df[c] = None
        df = df[columnas]

    return df

def guardar_excel(df, hoja):
    with pd.ExcelWriter(
        EXCEL_PATH,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as writer:
        df.to_excel(writer, sheet_name=hoja, index=False)

def buscar_parte(codigo):
    df = leer_excel("NumerosParte", ["numero_parte", "maquina"])
    fila = df[df["numero_parte"] == codigo]
    if fila.empty:
        return None, None
    return fila.iloc[0]["numero_parte"], fila.iloc[0]["maquina"]


def obtener_imagen(parte):
    for ext in (".jpg", ".png", ".jpeg"):
        ruta = os.path.join(IMAGES_PATH, f"{parte}{ext}")
        if os.path.exists(ruta):
            return ruta
    return None

def reset_escaneo():
    st.session_state.parte = ""
    st.session_state.maquina = ""
    st.session_state.libras = ""
    st.session_state.ultimo_scan = ""
    st.session_state.abrir_teclado = False
    st.session_state.fecha = datetime.now().date()
    st.session_state.form_uid += 1

def reset_nuevo():
    st.session_state.nuevo_uid += 1
    
def render_header(titulo, mostrar_regresar=True):
    col1, col2, col3 = st.columns([1, 6, 2])

    with col1:
        if mostrar_regresar:
            if st.button("⬅️", key=f"back_{titulo}"):
                st.session_state.pantalla = "menu"
                st.rerun()

    with col2:
        st.markdown(
            f"<h2 style='text-align:center; color:#E36B2C;'>{titulo}</h2>",
            unsafe_allow_html=True
        )

    with col3:
        logo_path = os.path.join(BASE_DIR, "logo_versigent.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=140)


def render_footer():
    st.markdown(
        """
        <hr>
        <div style="text-align:center; font-size:13px; color:#CFCFCF;">
           IT OpEx NL II Ing. Jennifer Valdes - Versigent
        </div>
        """,
        unsafe_allow_html=True
    )


def guardar_scrap_supabase(data: dict):
    supabase.table("scrap_registrado").insert(data).execute()


def leer_scrap_supabase():
    response = (
        supabase
        .table("scrap_registrado")
        .select("*")
        .order("fecha", desc=True)
        .execute()
    )

    if response.data:
        return pd.DataFrame(response.data)
    return pd.DataFrame()


def buscar_causa_por_qr(codigo):
    df = leer_excel("CausasQR", ["qr", "causa"])
    fila = df[df["qr"] == codigo]

    if fila.empty:
        return None
    return fila.iloc[0]["causa"]

# =====================================================
# MENÚ PRINCIPAL
# =====================================================
def menu():
    render_header("Control de Scrap", mostrar_regresar=False)

    st.markdown("---")

    # ✅ ESTO ES OBLIGATORIO
    col1, col2 = st.columns(2)

    with col1:
        if st.button("📷 Escaneo", use_container_width=True):
            st.session_state.pantalla = "escaneo"
            st.rerun()

        if st.button("➕ Nuevo", use_container_width=True):
            st.session_state.pantalla = "nuevo"
            st.rerun()

    with col2:
        if st.button("📊 Historial", use_container_width=True):
            st.session_state.pantalla = "historial"
            st.rerun()

        if st.button("📈 Gráficos", use_container_width=True):
            st.session_state.pantalla = "graficos"
            st.rerun()

    render_footer()


# =====================================================
# PANTALLA DE ESCANEO
# =====================================================
def escaneo():
    render_header("Escaneo de Scrap")

    # ---------- REGRESAR ----------

    # ---------- SCANNER ----------
   
    codigo = st.text_input(
        "📷 Escanee el código de barras",
        key=f"scan_{st.session_state.form_uid}",
        placeholder="Apunte el escáner al código…"
    )



    if codigo and codigo != st.session_state.ultimo_scan:
        st.session_state.ultimo_scan = codigo
        causa_qr = buscar_causa_por_qr(codigo)

        if not causa_qr:
            st.error("❌ QR no reconocido")
        else:
            st.session_state.causa_qr = causa_qr


    # ---------- IMAGEN ----------
    if st.session_state.parte:
        ruta = obtener_imagen(st.session_state.parte)
        if ruta:
            st.image(ruta, width=250)
        else:
            st.info("Imagen no disponible")
    else:
        st.info("Sin imagen")

    # ---------- FORMULARIO ----------
    col1, col2 = st.columns(2)

    with col1:
        maquinas = leer_excel(
            "Maquinas",
            ["nombre_maquina"]
        )["nombre_maquina"].dropna().astype(str).tolist()

        maquina_sel = st.selectbox(
            "Máquina",
            maquinas,
            index=maquinas.index(st.session_state.maquina)
            if st.session_state.maquina in maquinas else 0,
            key=f"maquina_{st.session_state.form_uid}"
        )

        st.session_state.maquina = maquina_sel



        st.text_input(
            "Causa",
            value=st.session_state.causa_qr,
            disabled=True
        )
        causa = st.session_state.causa_qr


        planes = leer_excel("PlanesAccion", ["plan"])["plan"].dropna().tolist()
        plan = st.selectbox(
            "Plan de acción",
            planes,
            key=f"plan_{st.session_state.form_uid}"
        )

    with col2:
        partes_df = leer_excel("NumerosParte", ["numero_parte", "maquina"])
        partes_filtradas = partes_df[
            partes_df["maquina"] == st.session_state.maquina
        ]["numero_parte"].dropna().tolist()

        parte = st.selectbox(
            "Parte",
            partes_filtradas,
            key=f"parte_{st.session_state.form_uid}"
        )
        st.session_state.parte = parte


        col_l1, col_l2,  = st.columns([3, 1])
        with col_l1:
            st.text_input("Libras", value=st.session_state.libras, disabled=True)
        with col_l2:
            if st.button("⌨️", key="btn_teclado"):
                st.session_state.abrir_teclado = True
        st.date_input(
            "📅 Fecha",
            value=st.session_state.fecha,
            disabled=False
        )

    # ---------- TECLADO NUMÉRICO ----------
    if st.session_state.abrir_teclado:

        @st.dialog("🔢 Ingresar Libras")
        def teclado():

            st.markdown(
                f"""
                <div style="
                text-align:center;
                font-size:32px;
                font-weight:bold;
                background:#0F2A44;
                padding:20px;
                border-radius:10px;">
                {st.session_state.libras or "0"}
                </div>
                """,
                unsafe_allow_html=True
            )

            keypad = [
                ["7","8","9"],
                ["4","5","6"],
                ["1","2","3"],
                [".","0","⌫"]
            ]

            for r, fila in enumerate(keypad):
                cols = st.columns(3)
                for c, k in enumerate(fila):
                    if cols[c].button(
                        k,
                        use_container_width=True,
                        key=f"key_{r}_{c}"
                    ):
                        if k == "⌫":
                            st.session_state.libras = st.session_state.libras[:-1]
                        else:
                            st.session_state.libras += k
                        st.rerun()

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("✅ Aceptar", key="key_ok"):
                    st.session_state.abrir_teclado = False
                    st.rerun()

            with col_b:
                if st.button("❌ Cancelar", key="key_cancel"):
                    st.session_state.libras = ""
                    st.session_state.abrir_teclado = False
                    st.rerun()

        teclado()

    # ---------- FIRMA ----------
    firmas = []
    if st.session_state.maquina:
        df_m = leer_excel("Maquinistas", ["nombre", "maquina"])
        firmas = df_m[
            df_m["maquina"] == st.session_state.maquina
        ]["nombre"].dropna().tolist()

    firma = st.selectbox(
        "Firma",
        firmas,
        key=f"firma_{st.session_state.form_uid}"
    )

    # ---------- GUARDAR ----------

    if st.button("💾 Guardar Scrap", key="btn_guardar", use_container_width=True):

        # --- Validaciones ---
        if not st.session_state.parte:
            st.error("❌ Falta escanear la parte")
            return

        if not st.session_state.libras:
            st.error("❌ Falta ingresar libras")
            return

        if not causa:
            st.error("❌ Falta seleccionar causa")
            return



        if not plan:
            st.error("❌ Falta seleccionar plan de acción")
            return

        if not firma:
            st.error("❌ Falta seleccionar firma")
            return

        # --- Guardado ---
        data = {
            "Fecha": st.session_state.fecha.strftime("%d/%m/%Y"),
            "Maquina": st.session_state.maquina,
            "Parte": st.session_state.parte,
            "Causa": causa,

            "Plan Accion": plan,
            "Libras": st.session_state.libras,
            "Firma": firma
        }


        guardar_scrap_supabase(data)
        if st.session_state.mostrar_guardado:
            aviso = st.empty()
            aviso.success("✅ Scrap guardado correctamente")

            import time
            time.sleep(2.5)   # visible ~2.5 segundos

            aviso.empty()

        # ✅ Solo si TODO fue correcto


        st.session_state.mostrar_guardado = True
        reset_escaneo()
        st.rerun()
    render_footer()

# ================= NUEVO =================

def nuevo():
    render_header("Nuevo")

    # ===== MENSAJE POST-GUARDADO =====
    if st.session_state.nuevo_guardado:
        st.success("✅ Guardado correctamente")
        st.session_state.nuevo_guardado = False

    # ===== REGRESAR =====

    # ================= MÁQUINA =================
    with st.expander("➕ Agregar Máquina"):
        with st.form(f"form_maquina_{st.session_state.nuevo_uid}", clear_on_submit=False):

            nombre_maquina = st.text_input(
                "Nombre de la máquina",
                key=f"new_maquina_{st.session_state.nuevo_uid}"
            )

            guardar = st.form_submit_button("Guardar Máquina")

            if guardar:
                if not nombre_maquina.strip():
                    st.error("Nombre vacío")
                else:
                    df = leer_excel("Maquinas", ["maquina_id", "nombre_maquina"])

                    if nombre_maquina in df["nombre_maquina"].values:
                        st.error("La máquina ya existe")
                    else:
                        df.loc[len(df)] = [len(df) + 1, nombre_maquina]
                        guardar_excel(df, "Maquinas")

                        st.session_state.nuevo_guardado = True
                        reset_nuevo()
                        st.rerun()

    # ================= CAUSA =================
    with st.expander("➕ Agregar Causa"):
        with st.form(f"form_causa_{st.session_state.nuevo_uid}", clear_on_submit=False):

            causa = st.text_input(
                "Causa",
                key=f"new_causa_{st.session_state.nuevo_uid}"
            )

            guardar = st.form_submit_button("Guardar Causa")

            if guardar:
                if not causa.strip():
                    st.error("Causa vacía")
                else:
                    df = leer_excel("Causas", ["causa_id", "causa"])

                    if causa in df["causa"].values:
                        st.error("La causa ya existe")
                    else:
                        df.loc[len(df)] = [len(df) + 1, causa]
                        guardar_excel(df, "Causas")

                        st.session_state.nuevo_guardado = True
                        reset_nuevo()
                        st.rerun()

    # ================= PLAN =================
    with st.expander("➕ Agregar Plan de Acción"):
        with st.form(f"form_plan_{st.session_state.nuevo_uid}", clear_on_submit=False):

            plan = st.text_input(
                "Plan de acción",
                key=f"new_plan_{st.session_state.nuevo_uid}"
            )

            guardar = st.form_submit_button("Guardar Plan")

            if guardar:
                if not plan.strip():
                    st.error("Plan vacío")
                else:
                    df = leer_excel("PlanesAccion", ["plan_id", "plan"])
                    df.loc[len(df)] = [len(df) + 1, plan]
                    guardar_excel(df, "PlanesAccion")

                    st.session_state.nuevo_guardado = True
                    reset_nuevo()
                    st.rerun()

    # ================= NÚMERO DE PARTE =================
    with st.expander("➕ Agregar Número de Parte"):
        with st.form(f"form_parte_{st.session_state.nuevo_uid}", clear_on_submit=False):

            maquinas = leer_excel(
                "Maquinas", ["nombre_maquina"]
            )["nombre_maquina"].dropna().astype(str).tolist()

            maquina_sel = st.selectbox(
                "Máquina",
                maquinas,
                key=f"new_parte_maquina_{st.session_state.nuevo_uid}"
            )
            st.session_state.maquina = maquina
            numero_parte = st.text_input(
                "Número de parte",
                key=f"new_numero_parte_{st.session_state.nuevo_uid}"
            )

            imagen = st.file_uploader(
                "Imagen (.jpg / .png)",
                type=["jpg", "png", "jpeg"],
                key=f"new_img_{st.session_state.nuevo_uid}"
            )

            guardar = st.form_submit_button("Guardar Número de Parte")

            if guardar:
                if not numero_parte or not maquina_sel:
                    st.error("Campos incompletos")
                else:
                    df = leer_excel(
                        "NumerosParte", ["parte_id", "numero_parte", "maquina"]
                    )

                    if numero_parte in df["numero_parte"].values:
                        st.error("El número de parte ya existe")
                    else:
                        df.loc[len(df)] = [len(df) + 1, numero_parte, maquina_sel]
                        guardar_excel(df, "NumerosParte")

                        if imagen:
                            ruta = os.path.join(IMAGES_PATH, f"{numero_parte}.jpg")
                            with open(ruta, "wb") as f:
                                f.write(imagen.read())

                        st.session_state.nuevo_guardado = True
                        reset_nuevo()
                        st.rerun()

    # ================= MAQUINISTA =================
    with st.expander("➕ Agregar Maquinista"):
        with st.form(f"form_maquinista_{st.session_state.nuevo_uid}", clear_on_submit=False):

            maquinas = leer_excel(
                "Maquinas", ["nombre_maquina"]
            )["nombre_maquina"].dropna().astype(str).tolist()

            maquina = st.selectbox(
                "Máquina",
                maquinas,
                key=f"new_maquinista_maquina_{st.session_state.nuevo_uid}"
            )

            nombre = st.text_input(
                "Nombre del maquinista",
                key=f"new_maquinista_nombre_{st.session_state.nuevo_uid}"
            )

            guardar = st.form_submit_button("Guardar Maquinista")

            if guardar:
                maquina = str(maquina).strip()
                nombre = str(nombre).strip()

                df = leer_excel(
                    "Maquinistas", ["maquinista_id", "nombre", "maquina"]
                )

                df["maquina"] = df["maquina"].astype(str).str.strip()
                df["nombre"] = df["nombre"].astype(str).str.strip()

                if len(df[df["maquina"] == maquina]) >= 4:
                    st.error(f"La máquina {maquina} ya tiene 4 maquinistas")
                elif not nombre:
                    st.error("Nombre vacío")
                elif not df[
                    (df["maquina"].str.lower() == maquina.lower()) &
                    (df["nombre"].str.lower() == nombre.lower())
                ].empty:
                    st.error("Ese maquinista ya existe en esta máquina")
                else:
                    nuevo_id = 1 if df.empty else int(df["maquinista_id"].max()) + 1
                    df.loc[len(df)] = [nuevo_id, nombre, maquina]
                    guardar_excel(df, "Maquinistas")

                    st.session_state.nuevo_guardado = True
                    reset_nuevo()
                    st.rerun()
    st.divider()
    render_footer()
# ================= HISTORIAL =================


def historial():
    AZUL = "#0F2A44"
    NARANJA = "#E36B2C"
    render_header("Historial de Scrap")

    # ---------- REGRESAR ----------


    # ---------- CARGAR DATA ----------

    df = leer_scrap_supabase()

    if df.empty:
        st.info("Aún no hay registros.")
        return


    # ---------- NORMALIZAR ----------
    df["Fecha"] = pd.to_datetime(df["fecha"]).dt.date
    df["Maquina"] = df["maquina"]
    df["Parte"] = df["parte"]
    df["Causa"] = df["causa"]
    df["Plan Acción"] = df["plan_accion"]
    df["Libras"] = pd.to_numeric(df["libras"], errors="coerce").fillna(0)

   
    fecha_min = min(df["Fecha"])
    fecha_max = max(df["Fecha"])


    uid = st.session_state.filtro_uid

# ---------- ACCIONES SUPERIORES ----------
    col_a, col_b = st.columns([1, 6])

    with col_a:
        output = io.BytesIO()
        df.to_excel(output, index=False)  # o df_f si quieres filtrado
        output.seek(0)

        st.download_button(
            label="📥 Descargar Excel",
            data=output,
            file_name="scrap_historial.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_b:
        with st.expander("🔍 Filtros", expanded=True):
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                f_fecha_ini = st.date_input(
                    "Desde",
                    value=fecha_min,
                    key=f"f_fecha_ini_{uid}"
                )

            with c2:
                f_fecha_fin = st.date_input(
                    "Hasta",
                    value=fecha_max,
                    key=f"f_fecha_fin_{uid}"
                )

            with c3:
                opciones_maquina = ["Todas"] + sorted(df["Maquina"].unique().tolist())
                f_maquina = st.selectbox(
                    "Máquina",
                    opciones_maquina,
                    key=f"f_maquina_{uid}"
                )

            with c4:
                opciones_parte = ["Todas"] + sorted(df["Parte"].unique().tolist())
                f_parte = st.selectbox(
                    "Parte",
                    opciones_parte,
                    key=f"f_parte_{uid}"
                )

            if st.button("🧹 Limpiar filtros"):
                st.session_state.filtro_uid += 1
                st.rerun()

    # ---------- APLICAR FILTROS ----------
    df_f = df.copy()

    df_f = df_f[
        (df_f["Fecha"]>= f_fecha_ini) &
        (df_f["Fecha"] <= f_fecha_fin)
    ]

    if f_maquina != "Todas":
        df_f = df_f[df_f["Maquina"] == f_maquina]

    if f_parte != "Todas":
        df_f = df_f[df_f["Parte"] == f_parte]

    df_f = df_f.sort_values("Fecha", ascending=False)

    st.divider()
    st.markdown(f"### 📋 Registros ({len(df_f)})")

    # ---------- REGISTROS (LAYOUT DENTRO DEL MISMO CUADRO) ----------
    for idx, (_, row) in enumerate(df_f.iterrows()):
        color = AZUL if idx % 2 == 0 else NARANJA

        lb = row["Libras"]
        lb = "-" if pd.isna(lb) or str(lb).strip() == "" else str(lb)

        st.markdown(
            f"""
<div style="
background:{color};
color:white;
padding:10px;
border-radius:8px;
margin-bottom:6px;
">

<div style="
display:grid;
grid-template-columns: 2fr 2fr 3fr 1.5fr;
column-gap:10px;
font-weight:bold;
">
    <div>Maquina: {row['Maquina']}</div>
    <div># Parte: {row['Parte']}</div>
    <div>Causa: {row['Causa']}</div>
    <div>Fecha: {row['Fecha'].strftime('%d/%m/%Y')}</div>
</div>

<div style="
display:grid;
grid-template-columns: 2fr 2fr 3fr 1.5fr;
column-gap:10px;
margin-top:4px;
font-size:16px;
font-weight:bold;
">
    <div>Plan: {row['Plan Acción']}</div>
    <div>$</div>
    <div>Lb: {lb}</div>
    <div></div>
</div>

</div>
""",
            unsafe_allow_html=True
        )
        


    render_footer()
# ================= GRAFICOS =================

def graficos():
    render_header("Gráficos")

    # ---------- REGRESAR ----------


    # ---------- CARGAR DATA ----------
    df = leer_scrap_supabase()

    if df.empty:
        st.info("No hay registros.")
        return

    # ---------- NORMALIZAR ----------
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce").dt.date
    df["Libras"] = pd.to_numeric(df["Libras"], errors="coerce").fillna(0)
    df["Maquina"] = df["Maquina"].astype(str).str.strip()
    df["Parte"] = df["Parte"].astype(str).str.strip()
    df["Causa"] = df["Causa"].astype(str).str.strip()

    fecha_min = df["Fecha"].min()
    fecha_max = df["Fecha"].max()

    # ---------- FILTRO FECHA ----------
    colf1, colf2 = st.columns([1, 2])

    with colf1:
        fecha_sel = st.date_input(
            "Filtrar por fecha",
            value=None,
            min_value=fecha_min,
            max_value=fecha_max
        )

    with colf2:
        if st.button("Ver todo"):
            fecha_sel = None

    if fecha_sel:
        df = df[df["Fecha"] == fecha_sel]

    st.divider()

    # ---------- DATOS PARA GRÁFICAS ----------
    top_partes = (
        df.groupby("Parte")
        .size()
        .sort_values(ascending=False)
        .head(5)
    )

    top_maquinas = (
        df.groupby("Maquina")
        .size()
        .sort_values(ascending=False)
        .head(5)
    )

    tipo_scrap = (
        df.groupby("Causa")
        .size()
        .sort_values(ascending=False)
        .head(5)
    )

    lb_por_parte = (
        df.groupby("Parte")["Libras"]
        .sum()
        .sort_values(ascending=False)
        .head(5)
    )

    # ---------- GRID 2x2 ----------
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # ===== # PARTE =====
    with col1:
        st.subheader("# Parte")
        fig, ax = plt.subplots()
        ax.bar(top_partes.index, top_partes.values, color="#5DAE3C")
        ax.set_ylabel("Cantidad")
        ax.set_xlabel("Parte")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

    # ===== MAQUINA =====
    with col2:
        st.subheader("Máquina")
        fig, ax = plt.subplots()
        ax.barh(top_maquinas.index, top_maquinas.values, color="#1E6F1E")
        ax.set_xlabel("Cantidad")
        ax.set_ylabel("Máquina")
        st.pyplot(fig)

    # ===== TIPO DE SCRAP =====
    with col3:
        st.subheader("Tipo de scrap")
        fig, ax = plt.subplots()
        wedges, _ = ax.pie(
            tipo_scrap.values,
            labels=None,
            startangle=90,
            wedgeprops=dict(width=0.4)
        )

        for i, wedge in enumerate(wedges):
            ang = (wedge.theta2 + wedge.theta1) / 2
            x = 0.7 * np.cos(np.deg2rad(ang))
            y = 0.7 * np.sin(np.deg2rad(ang))
            ax.text(
                x, y,
                str(tipo_scrap.values[i]),
                ha="center",
                va="center",
                color="white",
                fontweight="bold"
            )

        ax.legend(wedges, tipo_scrap.index, loc="center left", bbox_to_anchor=(1, 0.5))
        st.pyplot(fig)

    # ===== LB POR PARTE =====
    with col4:
        st.subheader("Lb por parte")
        fig, ax = plt.subplots()
        ax.bar(lb_por_parte.index, lb_por_parte.values, color="#A83232")
        ax.set_ylabel("Libras")
        ax.set_xlabel("Parte")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
    render_footer()


# ================= ROUTER =================
if st.session_state.pantalla == "menu":
    menu()
elif st.session_state.pantalla == "escaneo":
    escaneo()
elif st.session_state.pantalla == "nuevo":
    nuevo()
elif st.session_state.pantalla == "historial":
    historial()
elif st.session_state.pantalla == "graficos":
    graficos()



