import sqlite3
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "proyectos.db"

ETAPAS = [
    "Nuevo", "Acción requerida", "Pendiente", "Evaluación",
    "Inspección", "Validación", "2da Validación", "Finalizado", "Archivado"
]
ESTADOS = [
    "Pendiente de evaluación", "En proceso", "En espera",
    "Acción requerida", "Atrasado", "Detenido", "Completado"
]
RESULTADOS = [
    "Sin determinar", "Cumple", "No cumple", "Condicionada",
    "Posponer", "Definitiva"
]
PRIORIDADES = ["Baja", "Media", "Alta", "Urgente"]

st.set_page_config(page_title="Control de proyectos DPP", page_icon="📋", layout="wide")

def conectar():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            fecha_recepcion TEXT,
            municipio TEXT,
            etapa TEXT NOT NULL,
            estado TEXT NOT NULL,
            resultado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            responsable TEXT,
            ultima_actualizacion TEXT,
            proximo_paso TEXT,
            fecha_limite TEXT,
            enlace_planner TEXT,
            enlace_onenote TEXT,
            enlace_documentos TEXT,
            observaciones TEXT,
            creado_en TEXT NOT NULL
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS historial (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proyecto_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            detalle TEXT NOT NULL,
            estado_nuevo TEXT,
            FOREIGN KEY(proyecto_id) REFERENCES proyectos(id)
        )
    """)
    con.commit()
    return con

con = conectar()

def obtener_proyectos():
    return pd.read_sql_query("SELECT * FROM proyectos ORDER BY COALESCE(fecha_recepcion,'') DESC, id DESC", con)

def registrar_historial(proyecto_id, tipo, detalle, estado_nuevo=None):
    con.execute(
        "INSERT INTO historial (proyecto_id, fecha, tipo, detalle, estado_nuevo) VALUES (?, ?, ?, ?, ?)",
        (proyecto_id, datetime.now().strftime("%Y-%m-%d %H:%M"), tipo, detalle, estado_nuevo)
    )
    con.commit()

st.title("📋 Control y seguimiento de proyectos")
st.caption("Registro maestro para visualizar la cartera y abrir los registros de Planner, OneNote y documentos.")
st.info("Esta versión inicial no sincroniza automáticamente con Planner ni OneNote: guarda un registro central y permite enlazar los recursos existentes.")

df = obtener_proyectos()

# Indicadores
total = len(df)
activos = int((~df["estado"].isin(["Completado"])).sum()) if total else 0
atrasados = int((df["estado"] == "Atrasado").sum()) if total else 0
accion = int((df["estado"] == "Acción requerida").sum()) if total else 0
completados = int((df["estado"] == "Completado").sum()) if total else 0

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Total de proyectos", total)
m2.metric("Activos", activos)
m3.metric("Acción requerida", accion)
m4.metric("Atrasados", atrasados)
m5.metric("Completados", completados)

tablero, nuevo, detalle, exportar = st.tabs(
    ["📊 Cartera general", "➕ Registrar proyecto", "📝 Ficha e historial", "📤 Exportar datos"]
)

with tablero:
    st.subheader("Cartera general")
    if df.empty:
        st.write("Todavía no hay proyectos registrados. Entra en **Registrar proyecto** para crear el primero.")
    else:
        f1, f2, f3, f4 = st.columns(4)
        filtro_etapa = f1.multiselect("Filtrar por etapa", ETAPAS, default=[])
        filtro_estado = f2.multiselect("Filtrar por estado", ESTADOS, default=[])
        filtro_resultado = f3.multiselect("Resultado de evaluación", RESULTADOS, default=[])
        buscar = f4.text_input("Buscar por código o nombre")

        vista = df.copy()
        if filtro_etapa:
            vista = vista[vista["etapa"].isin(filtro_etapa)]
        if filtro_estado:
            vista = vista[vista["estado"].isin(filtro_estado)]
        if filtro_resultado:
            vista = vista[vista["resultado"].isin(filtro_resultado)]
        if buscar:
            mask = vista["codigo"].fillna("").str.contains(buscar, case=False) | vista["nombre"].fillna("").str.contains(buscar, case=False)
            vista = vista[mask]

        columnas = [
            "codigo", "nombre", "fecha_recepcion", "etapa", "estado",
            "resultado", "prioridad", "ultima_actualizacion", "proximo_paso", "fecha_limite"
        ]
        nombres = {
            "codigo": "Código DPP", "nombre": "Proyecto", "fecha_recepcion": "Recepción",
            "etapa": "Etapa", "estado": "Estado", "resultado": "Evaluación",
            "prioridad": "Prioridad", "ultima_actualizacion": "Última actualización",
            "proximo_paso": "Próximo paso", "fecha_limite": "Fecha límite"
        }
        st.dataframe(
            vista[columnas].rename(columns=nombres),
            use_container_width=True, hide_index=True,
            column_config={
                "Código DPP": st.column_config.TextColumn("Código DPP", width="small"),
                "Proyecto": st.column_config.TextColumn("Proyecto", width="large"),
                "Próximo paso": st.column_config.TextColumn("Próximo paso", width="large"),
            }
        )
        st.caption(f"Mostrando {len(vista)} de {len(df)} proyectos.")
        st.download_button(
            "Descargar cartera filtrada (CSV)",
            data=vista[columnas].rename(columns=nombres).to_csv(index=False).encode("utf-8-sig"),
            file_name=f"cartera_proyectos_{date.today().isoformat()}.csv",
            mime="text/csv"
        )

with nuevo:
    st.subheader("Registrar un proyecto")
    with st.form("form_nuevo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        codigo = c1.text_input("Código DPP / expediente *", placeholder="Ej. 04_DPP01-03931")
        nombre = c2.text_input("Nombre del proyecto *", placeholder="Ej. Vivienda unifamiliar")
        c3, c4, c5 = st.columns(3)
        fecha_recepcion = c3.date_input("Fecha de recepción", value=None)
        municipio = c4.text_input("Municipio")
        responsable = c5.text_input("Responsable")
        c6, c7, c8 = st.columns(3)
        etapa = c6.selectbox("Etapa actual", ETAPAS)
        estado = c7.selectbox("Estado de seguimiento", ESTADOS)
        resultado = c8.selectbox("Resultado de evaluación", RESULTADOS)
        c9, c10 = st.columns(2)
        prioridad = c9.selectbox("Prioridad", PRIORIDADES, index=1)
        fecha_limite = c10.date_input("Próxima fecha límite", value=None)
        proximo_paso = st.text_input("Próximo paso / acción requerida")
        enlace_planner = st.text_input("Enlace a Planner")
        enlace_onenote = st.text_input("Enlace a OneNote")
        enlace_documentos = st.text_input("Enlace a carpeta o documentos")
        observaciones = st.text_area("Observaciones iniciales")
        guardar = st.form_submit_button("Guardar proyecto", type="primary")

    if guardar:
        if not codigo.strip() or not nombre.strip():
            st.error("Completa el código DPP y el nombre del proyecto.")
        else:
            hoy = date.today().isoformat()
            try:
                cur = con.execute("""
                    INSERT INTO proyectos (
                        codigo,nombre,fecha_recepcion,municipio,etapa,estado,resultado,
                        prioridad,responsable,ultima_actualizacion,proximo_paso,fecha_limite,
                        enlace_planner,enlace_onenote,enlace_documentos,observaciones,creado_en
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    codigo.strip(), nombre.strip(),
                    fecha_recepcion.isoformat() if fecha_recepcion else "",
                    municipio.strip(), etapa, estado, resultado, prioridad,
                    responsable.strip(), hoy, proximo_paso.strip(),
                    fecha_limite.isoformat() if fecha_limite else "",
                    enlace_planner.strip(), enlace_onenote.strip(), enlace_documentos.strip(),
                    observaciones.strip(), datetime.now().isoformat(timespec="seconds")
                ))
                con.commit()
                registrar_historial(cur.lastrowid, "Registro creado", "Proyecto registrado en la cartera.", estado)
                st.success("Proyecto registrado correctamente.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Ese código ya existe. Utiliza un código único para cada expediente.")

with detalle:
    st.subheader("Ficha individual e historial")
    df_det = obtener_proyectos()
    if df_det.empty:
        st.info("Registra primero un proyecto.")
    else:
        opciones = {f"{r['codigo']} — {r['nombre']}": int(r["id"]) for _, r in df_det.iterrows()}
        elegido = st.selectbox("Selecciona un proyecto", list(opciones.keys()))
        pid = opciones[elegido]
        registro = con.execute("SELECT * FROM proyectos WHERE id=?", (pid,)).fetchone()
        cols = [d[0] for d in con.execute("SELECT * FROM proyectos LIMIT 0").description]
        p = dict(zip(cols, registro))

        st.markdown(f"### {p['codigo']} — {p['nombre']}")
        links = []
        for label, url in [
            ("Planner", p["enlace_planner"]), ("OneNote", p["enlace_onenote"]),
            ("Documentos", p["enlace_documentos"])
        ]:
            if url and url.startswith(("https://", "http://")):
                links.append(f"[Abrir {label}]({url})")
        st.markdown(" · ".join(links) if links else "No se han añadido enlaces a Planner, OneNote o documentos.")

        with st.expander("Editar información del proyecto", expanded=True):
            with st.form(f"editar_{pid}"):
                a1, a2 = st.columns(2)
                nombre_e = a1.text_input("Nombre", value=p["nombre"])
                municipio_e = a2.text_input("Municipio", value=p["municipio"] or "")
                a3, a4, a5 = st.columns(3)
                etapa_e = a3.selectbox("Etapa", ETAPAS, index=ETAPAS.index(p["etapa"]) if p["etapa"] in ETAPAS else 0)
                estado_e = a4.selectbox("Estado", ESTADOS, index=ESTADOS.index(p["estado"]) if p["estado"] in ESTADOS else 0)
                resultado_e = a5.selectbox("Resultado de evaluación", RESULTADOS, index=RESULTADOS.index(p["resultado"]) if p["resultado"] in RESULTADOS else 0)
                a6, a7 = st.columns(2)
                prioridad_e = a6.selectbox("Prioridad", PRIORIDADES, index=PRIORIDADES.index(p["prioridad"]) if p["prioridad"] in PRIORIDADES else 1)
                responsable_e = a7.text_input("Responsable", value=p["responsable"] or "")
                proximo_e = st.text_input("Próximo paso", value=p["proximo_paso"] or "")
                fecha_limite_e = st.text_input("Fecha límite (AAAA-MM-DD)", value=p["fecha_limite"] or "")
                ultima_e = st.text_input("Fecha última actualización (AAAA-MM-DD)", value=date.today().isoformat())
                planner_e = st.text_input("Enlace a Planner", value=p["enlace_planner"] or "")
                onenote_e = st.text_input("Enlace a OneNote", value=p["enlace_onenote"] or "")
                docs_e = st.text_input("Enlace a documentos", value=p["enlace_documentos"] or "")
                observaciones_e = st.text_area("Observaciones", value=p["observaciones"] or "")
                guardar_e = st.form_submit_button("Guardar cambios", type="primary")
            if guardar_e:
                anterior_estado = p["estado"]
                con.execute("""
                    UPDATE proyectos SET nombre=?, municipio=?, etapa=?, estado=?, resultado=?,
                    prioridad=?, responsable=?, proximo_paso=?, fecha_limite=?, ultima_actualizacion=?,
                    enlace_planner=?, enlace_onenote=?, enlace_documentos=?, observaciones=?
                    WHERE id=?
                """, (
                    nombre_e.strip(), municipio_e.strip(), etapa_e, estado_e, resultado_e,
                    prioridad_e, responsable_e.strip(), proximo_e.strip(), fecha_limite_e.strip(),
                    ultima_e.strip(), planner_e.strip(), onenote_e.strip(), docs_e.strip(),
                    observaciones_e.strip(), pid
                ))
                con.commit()
                cambios = f"Ficha actualizada. Etapa: {etapa_e}. Estado: {estado_e}. Evaluación: {resultado_e}."
                registrar_historial(pid, "Actualización", cambios, estado_e)
                if estado_e != anterior_estado:
                    registrar_historial(pid, "Cambio de estado", f"Estado cambiado de «{anterior_estado}» a «{estado_e}».", estado_e)
                st.success("Cambios guardados.")
                st.rerun()

        st.markdown("#### Añadir un avance al historial")
        with st.form(f"historial_{pid}", clear_on_submit=True):
            tipo_h = st.selectbox("Tipo de registro", [
                "Avance", "Evaluación técnica", "Documento recibido", "Documento pendiente",
                "Reunión", "Inspección", "Decisión", "Incidencia", "Otro"
            ])
            detalle_h = st.text_area("Detalle del avance, decisión u observación *")
            agregar_h = st.form_submit_button("Añadir al historial")
        if agregar_h:
            if detalle_h.strip():
                registrar_historial(pid, tipo_h, detalle_h.strip(), p["estado"])
                con.execute("UPDATE proyectos SET ultima_actualizacion=? WHERE id=?", (date.today().isoformat(), pid))
                con.commit()
                st.success("Registro añadido al historial.")
                st.rerun()
            else:
                st.error("Escribe el detalle antes de guardar.")

        hist = pd.read_sql_query(
            "SELECT fecha AS Fecha, tipo AS Tipo, detalle AS Detalle, estado_nuevo AS Estado FROM historial WHERE proyecto_id=? ORDER BY id DESC",
            con, params=(pid,)
        )
        st.markdown("#### Historial cronológico")
        if hist.empty:
            st.caption("Todavía no hay movimientos registrados.")
        else:
            st.dataframe(hist, use_container_width=True, hide_index=True)

with exportar:
    st.subheader("Exportar y respaldar")
    df_exp = obtener_proyectos()
    st.write("Descarga la cartera en CSV para analizarla en Excel.")
    if not df_exp.empty:
        st.download_button(
            "Descargar todos los proyectos (CSV)",
            data=df_exp.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"proyectos_{date.today().isoformat()}.csv",
            mime="text/csv"
        )
        hist_all = pd.read_sql_query("""
            SELECT p.codigo, p.nombre, h.fecha, h.tipo, h.detalle, h.estado_nuevo
            FROM historial h JOIN proyectos p ON p.id=h.proyecto_id
            ORDER BY h.id DESC
        """, con)
        st.download_button(
            "Descargar historial completo (CSV)",
            data=hist_all.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"historial_proyectos_{date.today().isoformat()}.csv",
            mime="text/csv"
        )
    st.warning(
        "Importante: esta versión guarda los datos en un archivo SQLite local. "
        "Para uso real en Streamlit Community Cloud, el almacenamiento local no garantiza persistencia. "
        "Antes de cargar datos institucionales, hay que configurar una base de datos persistente y revisar permisos/acceso."
    )

st.divider()
st.caption("Versión inicial · El registro maestro no reemplaza la evaluación técnica detallada de OneNote.")
