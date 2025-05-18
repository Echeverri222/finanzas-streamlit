import streamlit as st
st.set_page_config(page_title="Dashboard Financiero", layout="wide")

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import json

# === CONFIGURACIÓN DE ACCESO A GOOGLE SHEETS ===

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_CREDS"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

SHEET_ID = "1W0gOUZFFJHvsP5f6aozHDWt519WEy1u2q8h0nImVCt8"
workbook = client.open_by_key(SHEET_ID)
sheet = workbook.sheet1
sheet_ahorros = workbook.get_worksheet(1)  # Hoja 2 para ahorros
sheet_metas = workbook.get_worksheet(2)    # Hoja 3 para metas

# === FUNCIONES ===

def cargar_datos():
    """Carga los datos desde Google Sheets sin caché"""
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df["fecha"] = df["fecha"].astype(str).str.replace("'", "")
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["mes"] = df["fecha"].dt.to_period("M").astype(str)
    return df

def cargar_ahorros():
    """Carga los datos de ahorros"""
    try:
        data = sheet_ahorros.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df["fecha"] = pd.to_datetime(df["fecha"])
        return df
    except Exception as e:
        st.error(f"Error al cargar ahorros: {str(e)}")
        return pd.DataFrame()

def cargar_metas():
    """Carga las metas de ahorro"""
    try:
        data = sheet_metas.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df["fecha_meta"] = pd.to_datetime(df["fecha_meta"])
        return df
    except Exception as e:
        st.error(f"Error al cargar metas: {str(e)}")
        return pd.DataFrame()

def guardar_movimiento(fecha, nombre, importe, tipo):
    """Guarda un nuevo movimiento y retorna True si fue exitoso"""
    try:
        fecha_str = fecha.strftime("%Y-%m-%d")
        nueva_fila = [fecha_str, nombre, int(importe), tipo]
        next_row = len(sheet.get_all_values()) + 1
        sheet.append_row(nueva_fila)
        sheet.format(f"A{next_row}", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
        return True
    except Exception as e:
        st.error(f"Error al guardar el movimiento: {str(e)}")
        return False

def guardar_ahorro(fecha, monto, descripcion):
    """Guarda un nuevo movimiento de ahorro"""
    try:
        fecha_str = fecha.strftime("%Y-%m-%d")
        nueva_fila = [fecha_str, int(monto), descripcion]
        next_row = len(sheet_ahorros.get_all_values()) + 1
        sheet_ahorros.append_row(nueva_fila)
        sheet_ahorros.format(f"A{next_row}", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
        return True
    except Exception as e:
        st.error(f"Error al guardar el ahorro: {str(e)}")
        return False

def guardar_meta(nombre, meta_total, fecha_meta, descripcion):
    """Guarda una nueva meta de ahorro"""
    try:
        fecha_str = fecha_meta.strftime("%Y-%m-%d")
        nueva_fila = [nombre, int(meta_total), fecha_str, descripcion]
        next_row = len(sheet_metas.get_all_values()) + 1
        sheet_metas.append_row(nueva_fila)
        sheet_metas.format(f"C{next_row}", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
        return True
    except Exception as e:
        st.error(f"Error al guardar la meta: {str(e)}")
        return False

def eliminar_movimiento(indice_sheet):
    try:
        sheet.delete_rows(indice_sheet + 2)  # +2 porque sheets empieza en 1 y tiene header
        st.cache_data.clear()
        st.success("✅ Movimiento eliminado correctamente.")
        st.rerun()
    except Exception as e:
        st.error(f"Error al eliminar el movimiento: {str(e)}")

def eliminar_ahorro(indice_sheet):
    try:
        sheet_ahorros.delete_rows(indice_sheet + 2)
        st.cache_data.clear()
        st.success("✅ Ahorro eliminado correctamente.")
        st.rerun()
    except Exception as e:
        st.error(f"Error al eliminar el ahorro: {str(e)}")

def eliminar_meta(indice_sheet):
    try:
        sheet_metas.delete_rows(indice_sheet + 2)
        st.cache_data.clear()
        st.success("✅ Meta eliminada correctamente.")
        st.rerun()
    except Exception as e:
        st.error(f"Error al eliminar la meta: {str(e)}")

def actualizar_ahorro(indice_sheet, fecha, monto, descripcion):
    """Actualiza un registro de ahorro existente"""
    try:
        fecha_str = fecha.strftime("%Y-%m-%d")
        sheet_ahorros.update(f'A{indice_sheet + 2}', fecha_str)
        sheet_ahorros.update(f'B{indice_sheet + 2}', int(monto))
        sheet_ahorros.update(f'C{indice_sheet + 2}', descripcion)
        sheet_ahorros.format(f"A{indice_sheet + 2}", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
        return True
    except Exception as e:
        st.error(f"Error al actualizar el ahorro: {str(e)}")
        return False

def actualizar_meta(indice_sheet, nombre, meta_total, fecha_meta, descripcion):
    """Actualiza una meta existente"""
    try:
        fecha_str = fecha_meta.strftime("%Y-%m-%d")
        sheet_metas.update(f'A{indice_sheet + 2}', nombre)
        sheet_metas.update(f'B{indice_sheet + 2}', int(meta_total))
        sheet_metas.update(f'C{indice_sheet + 2}', fecha_str)
        sheet_metas.update(f'D{indice_sheet + 2}', descripcion)
        sheet_metas.format(f"C{indice_sheet + 2}", {"numberFormat": {"type": "DATE", "pattern": "yyyy-mm-dd"}})
        return True
    except Exception as e:
        st.error(f"Error al actualizar la meta: {str(e)}")
        return False

# Cargar datos al inicio
df = cargar_datos()
df_ahorros = cargar_ahorros()
df_metas = cargar_metas()

fmt = lambda x: f"${x:,.0f}".replace(",", ".")

# === INTERFAZ PRINCIPAL ===

st.title("Finanzas Personales")

# === FILTROS PRINCIPALES ===
col1, col2, col3 = st.columns([1, 1, 2])
with col1:
    año = st.selectbox("Selecciona un año", sorted(df["fecha"].dt.year.unique()), index=0)
    df_filtrado = df[df["fecha"].dt.year == año]

with col2:    
    meses = ["Todos"] + sorted(df_filtrado["mes"].unique().tolist())
    mes_seleccionado = st.selectbox("Selecciona un mes", meses, index=0)
    
    if mes_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["mes"] == mes_seleccionado]

# Inicializar estados de sesión
if "mostrar_formulario" not in st.session_state:
    st.session_state["mostrar_formulario"] = False
if "mostrar_eliminar" not in st.session_state:
    st.session_state["mostrar_eliminar"] = False
if "confirmar_eliminar" not in st.session_state:
    st.session_state["confirmar_eliminar"] = False
if "indice_eliminar" not in st.session_state:
    st.session_state["indice_eliminar"] = None
if "mostrar_form_ahorro" not in st.session_state:
    st.session_state["mostrar_form_ahorro"] = False
if "mostrar_form_meta" not in st.session_state:
    st.session_state["mostrar_form_meta"] = False
if "editar_ahorro" not in st.session_state:
    st.session_state["editar_ahorro"] = None
if "editar_meta" not in st.session_state:
    st.session_state["editar_meta"] = None
if "confirmar_eliminar_ahorro" not in st.session_state:
    st.session_state["confirmar_eliminar_ahorro"] = None
if "confirmar_eliminar_meta" not in st.session_state:
    st.session_state["confirmar_eliminar_meta"] = None

# Crear pestañas
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Resumen Gráfico",
    "📝 Gestión de Movimientos",
    "📋 Detalle Mensual",
    "📜 Lista de Movimientos",
    "💰 Ahorros y Metas"
])

with tab1:
    # === RESUMEN GRÁFICO ===
    st.subheader("Resumen General")
    gastos_filtrados = df_filtrado[df_filtrado["tipo_movimiento"] != "Ingresos"]
    ingresos_filtrados = df_filtrado[df_filtrado["tipo_movimiento"] == "Ingresos"]

    total_gastos = gastos_filtrados["importe"].sum()
    total_ingresos = ingresos_filtrados["importe"].sum()
    balance = total_ingresos - total_gastos

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Ingresos", fmt(total_ingresos))
    col2.metric("Total Gastos", fmt(total_gastos))
    col3.metric("Balance Neto", fmt(balance))

    # Gráficos de categorías
    st.subheader("Distribución de gastos por categoría")
    cat_summary = gastos_filtrados.groupby("tipo_movimiento")["importe"].sum().reset_index()
    cat_summary["porcentaje"] = 100 * cat_summary["importe"] / cat_summary["importe"].sum()
    cat_summary["importe_fmt"] = cat_summary["importe"].apply(fmt)

    # Definir colores específicos para cada categoría
    COLOR_MAP = {
        "Alimentacion": "#63B3ED",     # Azul claro
        "Transporte": "#38B2AC",       # Verde turquesa
        "Compras": "#F56565",          # Rojo
        "Gastos fijos": "#FBD38D",     # Rosa salmón
        "Ahorro": "#2B6CB0",           # Azul oscuro
        "Salidas": "#48BB78",          # Verde
        "Otros": "#D6BCFA"             # Morado claro
    }

    col1, col2 = st.columns(2)
    # Gráfico de torta
    fig1 = px.pie(cat_summary, names="tipo_movimiento", values="porcentaje", 
                title="Distribución por categoría",
                color="tipo_movimiento",
                color_discrete_map=COLOR_MAP)
    fig1.update_traces(textinfo="percent")

    # Gráfico de barras horizontales
    cat_summary_sorted = cat_summary.sort_values("importe", ascending=False)
    fig2 = px.bar(cat_summary_sorted, y="tipo_movimiento", x="importe", text="importe_fmt",
                title="Gastos absolutos", orientation='h',
                color="tipo_movimiento",
                color_discrete_map=COLOR_MAP)
    fig2.update_layout(showlegend=False)

    col1.plotly_chart(fig1, use_container_width=True)
    col2.plotly_chart(fig2, use_container_width=True)

    # Evolución mensual
    st.subheader("Evolución mensual de gastos")
    evol = df[df["tipo_movimiento"] != "Ingresos"].groupby(["mes", "tipo_movimiento"])["importe"].sum().reset_index()
    fig_line = px.line(evol, x="mes", y="importe", color="tipo_movimiento", markers=True,
                      color_discrete_map=COLOR_MAP)
    fig_line.update_layout(yaxis_tickformat=",", yaxis_tickprefix="$ ")
    st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    # === GESTIÓN DE MOVIMIENTOS ===
    st.subheader("Gestión de Movimientos")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Añadir Nuevo Movimiento"):
            st.session_state["mostrar_formulario"] = True
            st.session_state["mostrar_eliminar"] = False
    with col2:
        if st.button("➖ Eliminar Movimiento"):
            st.session_state["mostrar_eliminar"] = True
            st.session_state["mostrar_formulario"] = False

    # Formulario para añadir
    if st.session_state["mostrar_formulario"]:
        with st.form("formulario"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", datetime.today())
                importe = st.number_input("Importe", step=1000)
            with col2:
                nombre = st.text_input("Nombre del movimiento")
                tipo = st.selectbox("Tipo de movimiento", sorted(df["tipo_movimiento"].unique()) + ["Otro"])
            
            submit = st.form_submit_button("Agregar")
            if submit:
                if guardar_movimiento(fecha, nombre, importe, tipo):
                    st.success("Movimiento agregado correctamente.")
                    st.session_state["mostrar_formulario"] = False
                    df = cargar_datos()
                    st.rerun()

    # Interfaz para eliminar
    if st.session_state["mostrar_eliminar"]:
        st.markdown("### 🗑️ Eliminar Movimiento")
        busqueda = st.text_input("🔍 Buscar movimiento por nombre", "")
        
        df_eliminar = df.copy()
        df_eliminar["fecha"] = df_eliminar["fecha"].dt.strftime("%Y-%m-%d")
        df_eliminar["importe"] = df_eliminar["importe"].apply(fmt)
        
        if busqueda:
            df_eliminar = df_eliminar[df_eliminar["nombre"].str.contains(busqueda, case=False)]
        
        for idx, row in df_eliminar.iterrows():
            if st.session_state["confirmar_eliminar"] and st.session_state["indice_eliminar"] == idx:
                st.warning(f"⚠️ ¿Eliminar el movimiento '{row['nombre']}'?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✓ Sí", key=f"confirm_{idx}"):
                        eliminar_movimiento(idx)
                        st.session_state["mostrar_eliminar"] = False
                        st.session_state["confirmar_eliminar"] = False
                        st.session_state["indice_eliminar"] = None
                with col2:
                    if st.button("✗ No", key=f"cancel_{idx}"):
                        st.session_state["confirmar_eliminar"] = False
                        st.session_state["indice_eliminar"] = None
                        st.rerun()
            else:
                cols = st.columns([2, 3, 2, 2, 1])
                cols[0].write(row["fecha"])
                cols[1].write(row["nombre"])
                cols[2].write(row["importe"])
                cols[3].write(row["tipo_movimiento"])
                if cols[4].button("🗑️", key=f"del_{idx}"):
                    st.session_state["confirmar_eliminar"] = True
                    st.session_state["indice_eliminar"] = idx
                    st.rerun()
            st.markdown("---")
        
        if st.button("Cerrar"):
            st.session_state["mostrar_eliminar"] = False
            st.rerun()

with tab3:
    # === DETALLE MENSUAL ===
    st.subheader("Detalle por mes y categoría")
    
    # Crear pivot table incluyendo ingresos
    pivot = df_filtrado.groupby(["mes", "tipo_movimiento"])["importe"].sum().unstack(fill_value=0)
    # Reordenar columnas para que Ingresos sea la primera
    columnas = ["Ingresos"] + [col for col in pivot.columns if col != "Ingresos"]
    pivot = pivot[columnas]
    # Añadir columna de Total (Ingresos - Gastos)
    gastos_totales = pivot.drop("Ingresos", axis=1).sum(axis=1)
    pivot["Total"] = pivot["Ingresos"] - gastos_totales
    st.dataframe(pivot.style.format(fmt))

with tab4:
    # === LISTA DE MOVIMIENTOS ===
    st.subheader("Lista de Movimientos")
    
    col1, col2 = st.columns(2)
    with col1:
        categoria_filtro = st.multiselect(
            "Filtrar por categoría",
            options=sorted(df["tipo_movimiento"].unique().tolist())
        )
    with col2:
        mes_filtro = st.multiselect(
            "Filtrar por mes",
            options=sorted(df_filtrado["mes"].unique().tolist())
        )

    df_detalle = df_filtrado.copy()
    if categoria_filtro:
        df_detalle = df_detalle[df_detalle["tipo_movimiento"].isin(categoria_filtro)]
    if mes_filtro:
        df_detalle = df_detalle[df_detalle["mes"].isin(mes_filtro)]

    df_detalle = df_detalle.sort_values("fecha", ascending=False)
    df_detalle["fecha"] = df_detalle["fecha"].dt.strftime("%Y-%m-%d")
    df_detalle["importe"] = df_detalle["importe"].apply(fmt)

    st.dataframe(
        df_detalle[["fecha", "nombre", "importe", "tipo_movimiento"]],
        column_config={
            "fecha": "Fecha",
            "nombre": "Descripción",
            "importe": "Importe",
            "tipo_movimiento": "Categoría"
        },
        hide_index=True
    )

with tab5:
    # === AHORROS Y METAS ===
    st.subheader("💰 Gestión de Ahorros y Metas")
    
    # Sección de Ahorros
    st.markdown("### 📈 Ahorros")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Registrar Ahorro"):
            st.session_state["mostrar_form_ahorro"] = True
            st.session_state["editar_ahorro"] = None
    
    # Formulario para añadir/editar ahorro
    if st.session_state["mostrar_form_ahorro"] or st.session_state["editar_ahorro"] is not None:
        with st.form("formulario_ahorro"):
            editar_modo = st.session_state["editar_ahorro"] is not None
            if editar_modo:
                ahorro = df_ahorros.iloc[st.session_state["editar_ahorro"]]
                st.markdown("#### ✏️ Editar Ahorro")
            else:
                st.markdown("#### ➕ Nuevo Ahorro")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha_ahorro = st.date_input(
                    "Fecha",
                    value=ahorro["fecha"].date() if editar_modo else datetime.today()
                )
                monto_ahorro = st.number_input(
                    "Monto",
                    value=int(ahorro["monto"]) if editar_modo else 0,
                    step=1000,
                    min_value=0
                )
            with col2:
                descripcion_ahorro = st.text_input(
                    "Descripción",
                    value=ahorro["descripcion"] if editar_modo else ""
                )
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Guardar")
            with col2:
                cancel = st.form_submit_button("❌ Cancelar")
            
            if submit:
                if editar_modo:
                    if actualizar_ahorro(st.session_state["editar_ahorro"], fecha_ahorro, monto_ahorro, descripcion_ahorro):
                        st.success("✅ Ahorro actualizado correctamente")
                        st.session_state["editar_ahorro"] = None
                        df_ahorros = cargar_ahorros()
                        st.rerun()
                else:
                    if guardar_ahorro(fecha_ahorro, monto_ahorro, descripcion_ahorro):
                        st.success("✅ Ahorro registrado correctamente")
                        st.session_state["mostrar_form_ahorro"] = False
                        df_ahorros = cargar_ahorros()
                        st.rerun()
            
            if cancel:
                st.session_state["mostrar_form_ahorro"] = False
                st.session_state["editar_ahorro"] = None
                st.rerun()
    
    # Mostrar resumen de ahorros
    if not df_ahorros.empty:
        total_ahorrado = df_ahorros["monto"].sum()
        st.metric("Total Ahorrado", fmt(total_ahorrado))
        
        # Gráfico de evolución de ahorros
        df_ahorros_evol = df_ahorros.sort_values("fecha").copy()
        df_ahorros_evol["monto_acumulado"] = df_ahorros_evol["monto"].cumsum()
        
        fig_ahorros = px.line(
            df_ahorros_evol,
            x="fecha",
            y="monto_acumulado",
            title="Evolución de Ahorros (Acumulado)",
            markers=True
        )
        fig_ahorros.update_layout(
            yaxis_tickformat=",",
            yaxis_tickprefix="$ ",
            xaxis_title="Fecha",
            yaxis_title="Total Ahorrado"
        )
        
        # Añadir etiquetas con los montos en cada punto
        fig_ahorros.update_traces(
            texttemplate="%{y:$,.0f}",
            textposition="top center"
        )
        
        st.plotly_chart(fig_ahorros, use_container_width=True)
        
        # Lista de movimientos de ahorro
        st.markdown("#### Movimientos de Ahorro")
        for idx, ahorro in df_ahorros.sort_values("fecha", ascending=False).iterrows():
            with st.container():
                cols = st.columns([2, 2, 2, 1, 1])
                cols[0].write(ahorro["fecha"].strftime("%Y-%m-%d"))
                cols[1].write(fmt(ahorro["monto"]))
                cols[2].write(ahorro["descripcion"])
                
                # Botones de editar y eliminar
                if cols[3].button("✏️", key=f"edit_ahorro_{idx}"):
                    st.session_state["editar_ahorro"] = idx
                    st.session_state["mostrar_form_ahorro"] = False
                    st.rerun()
                
                if cols[4].button("🗑️", key=f"del_ahorro_{idx}"):
                    st.session_state["confirmar_eliminar_ahorro"] = idx
                    st.rerun()
                
                # Confirmación de eliminación
                if st.session_state["confirmar_eliminar_ahorro"] == idx:
                    st.warning("⚠️ ¿Estás seguro de eliminar este ahorro?")
                    col1, col2 = st.columns(2)
                    if col1.button("✓ Sí", key=f"confirm_del_ahorro_{idx}"):
                        eliminar_ahorro(idx)
                        st.session_state["confirmar_eliminar_ahorro"] = None
                        df_ahorros = cargar_ahorros()
                        st.rerun()
                    if col2.button("✗ No", key=f"cancel_del_ahorro_{idx}"):
                        st.session_state["confirmar_eliminar_ahorro"] = None
                        st.rerun()
                st.markdown("---")
    
    # Sección de Metas
    st.markdown("### 🎯 Metas de Ahorro")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Nueva Meta"):
            st.session_state["mostrar_form_meta"] = True
            st.session_state["editar_meta"] = None
    
    # Formulario para añadir/editar meta
    if st.session_state["mostrar_form_meta"] or st.session_state["editar_meta"] is not None:
        with st.form("formulario_meta"):
            editar_modo = st.session_state["editar_meta"] is not None
            if editar_modo:
                meta = df_metas.iloc[st.session_state["editar_meta"]]
                st.markdown("#### ✏️ Editar Meta")
            else:
                st.markdown("#### ➕ Nueva Meta")
            
            col1, col2 = st.columns(2)
            with col1:
                nombre_meta = st.text_input(
                    "Nombre de la Meta",
                    value=meta["nombre_objetivo"] if editar_modo else ""
                )
                meta_total = st.number_input(
                    "Monto Objetivo",
                    value=int(meta["meta_total"]) if editar_modo else 0,
                    step=1000,
                    min_value=0
                )
            with col2:
                fecha_meta = st.date_input(
                    "Fecha Objetivo",
                    value=meta["fecha_meta"].date() if editar_modo else datetime.today()
                )
                descripcion_meta = st.text_input(
                    "Descripción de la Meta",
                    value=meta["descripcion"] if editar_modo else ""
                )
            
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("💾 Guardar")
            with col2:
                cancel = st.form_submit_button("❌ Cancelar")
            
            if submit:
                if editar_modo:
                    if actualizar_meta(st.session_state["editar_meta"], nombre_meta, meta_total, fecha_meta, descripcion_meta):
                        st.success("✅ Meta actualizada correctamente")
                        st.session_state["editar_meta"] = None
                        df_metas = cargar_metas()
                        st.rerun()
                else:
                    if guardar_meta(nombre_meta, meta_total, fecha_meta, descripcion_meta):
                        st.success("✅ Meta guardada correctamente")
                        st.session_state["mostrar_form_meta"] = False
                        df_metas = cargar_metas()
                        st.rerun()
            
            if cancel:
                st.session_state["mostrar_form_meta"] = False
                st.session_state["editar_meta"] = None
                st.rerun()
    
    # Mostrar metas existentes
    if not df_metas.empty:
        st.markdown("#### Metas Actuales")
        for idx, meta in df_metas.iterrows():
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                with col1:
                    st.markdown(f"**{meta['nombre_objetivo']}**")
                    st.write(meta['descripcion'])
                with col2:
                    st.metric("Objetivo", fmt(meta['meta_total']))
                    st.write(f"Fecha: {meta['fecha_meta'].strftime('%Y-%m-%d')}")
                with col3:
                    # Calcular progreso basado en ahorros totales
                    progreso = min(100, (total_ahorrado / meta['meta_total']) * 100)
                    st.progress(progreso / 100)
                    st.write(f"Progreso: {progreso:.1f}%")
                
                # Botones de editar y eliminar
                with col4:
                    if st.button("✏️", key=f"edit_meta_{idx}"):
                        st.session_state["editar_meta"] = idx
                        st.session_state["mostrar_form_meta"] = False
                        st.rerun()
                
                with col5:
                    if st.button("🗑️", key=f"del_meta_{idx}"):
                        st.session_state["confirmar_eliminar_meta"] = idx
                        st.rerun()
                
                # Confirmación de eliminación
                if st.session_state["confirmar_eliminar_meta"] == idx:
                    st.warning("⚠️ ¿Estás seguro de eliminar esta meta?")
                    col1, col2 = st.columns(2)
                    if col1.button("✓ Sí", key=f"confirm_del_meta_{idx}"):
                        eliminar_meta(idx)
                        st.session_state["confirmar_eliminar_meta"] = None
                        df_metas = cargar_metas()
                        st.rerun()
                    if col2.button("✗ No", key=f"cancel_del_meta_{idx}"):
                        st.session_state["confirmar_eliminar_meta"] = None
                        st.rerun()
                st.markdown("---")
