import streamlit as st
from openai import OpenAI
import json
import pandas as pd

# Configuración inicial de la interfaz en Streamlit
st.set_page_config(
    page_title="HR Interview Copilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Título y encabezado principal
st.title("🎯 HR Interview Copilot")
st.caption("Generador inteligente de guías de entrevista estructuradas por competencias y metodología STAR.")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.header("⚙️ Configuración Global")

# Selección de origen de API Key
api_key_input = st.sidebar.text_input(
    "OpenAI API Key",
    type="password",
    help="Introduce tu API Key de OpenAI para habilitar la generación."
)

# Intentar obtener la API key desde st.secrets si existe, o usar el input del usuario
openai_api_key = api_key_input or st.secrets.get("OPENAI_API_KEY", "")

if not openai_api_key:
    st.sidebar.warning("⚠️ Es necesaria una API Key de OpenAI para usar la aplicación.")

# Parámetros del perfil en la barra lateral
st.sidebar.subheader("📌 Detalles del Puesto")
nivel_puesto = st.sidebar.selectbox(
    "Nivel de Responsabilidad",
    ["Júnior", "Mid-Level", "Senior", "Lead / Manager", "Executive / C-Level"]
)

valores_corporativos = st.sidebar.text_area(
    "Valores Corporativos (Opcional)",
    placeholder="Ej: Innovación, Empatía, Orientación al Cliente...",
    help="Valores transversales a incluir en la evaluación."
)

# Inicializar st.session_state para mantener la guía generada sin perder datos
if "guia_generada" not in st.session_state:
    st.session_state["guia_generada"] = None
if "datos_puesto" not in st.session_state:
    st.session_state["datos_puesto"] = {}

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs([
    "⚙️ Configuración del Puesto",
    "📋 Guía de Entrevista & Rúbrica",
    "📥 Exportar Guía"
])

# --- PESTAÑA 1: CONFIGURACIÓN ---
with tab1:
    st.subheader("1. Definición de la Vacante")
    
    col1, col2 = st.columns(2)
    with col1:
        nombre_puesto = st.text_input(
            "Denominación del Puesto",
            placeholder="Ej. Senior Frontend Developer, Recruiting Specialist..."
        )
    
    competencias_predefinidas = [
        "Liderazgo y Gestión de Equipos",
        "Comunicación Asertiva",
        "Trabajo en Equipo y Colaboración",
        "Resiliencia y Gestión del Estrés",
        "Orientación a Resultados",
        "Resolución de Problemas Complejos",
        "Adaptabilidad y Gestión del Cambio",
        "Pensamiento Analítico",
        "Toma de Decisiones",
        "Innovación y Creatividad"
    ]
    
    with col2:
        competencias_seleccionadas = st.multiselect(
            "Selecciona entre 3 y 5 Competencias Clave",
            options=competencias_predefinidas,
            default=["Comunicación Asertiva", "Resolución de Problemas Complejos", "Adaptabilidad y Gestión del Cambio"]
        )

    competencias_custom = st.text_input(
        "Competencias Adicionales (Opcional)",
        placeholder="Ej: Negociación internacional, Pensamiento sistémico..."
    )

    descripcion_puesto = st.text_area(
        "Contexto o Descripción de la Vacante (Opcional)",
        placeholder="Copia aquí el borrador de la oferta o detalles específicos del contexto del equipo...",
        height=120
    )

    # Combinar competencias seleccionadas y personalizadas
    todas_competencias = competencias_seleccionadas.copy()
    if competencias_custom:
        todas_competencias.extend([c.strip() for c in competencias_custom.split(",") if c.strip()])

    st.markdown("---")
    
    # Botón de ejecución
    if st.button("🚀 Generar Guía de Entrevista", type="primary", use_container_width=True):
        if not openai_api_key:
            st.error("Por favor, introduce tu OpenAI API Key en la barra lateral para continuar.")
        elif not nombre_puesto:
            st.error("Por favor, indica la denominación del puesto.")
        elif len(todas_competencias) == 0:
            st.error("Por favor, selecciona al menos una competencia a evaluar.")
        else:
            with st.spinner("Analizando requerimientos y redactando guía STAR personalizada..."):
                try:
                    client = OpenAI(api_key=openai_api_key)
                    
                    # Prompt del sistema para forzar formato JSON estructurado
                    system_prompt = (
                        "Eres un experto consultor en Selección por Competencias y People Analytics. "
                        "Tu tarea es diseñar una guía de entrevista estructurada en formato JSON estricto. "
                        "Responde ÚNICAMENTE con el objeto JSON estructurado, sin rodeos ni Markdown adicional."
                    )

                    user_prompt = f"""
                    Genera una guía de entrevista en español para el puesto: '{nombre_puesto}' (Nivel: {nivel_puesto}).
                    
                    Competencias a evaluar: {', '.join(todas_competencias)}
                    Valores corporativos a considerar: {valores_corporativos if valores_corporativos else 'No especificados'}
                    Contexto adicional del puesto: {descripcion_puesto if descripcion_puesto else 'No especificado'}

                    Estructura del JSON requerido:
                    {{
                        "puesto": "{nombre_puesto}",
                        "nivel": "{nivel_puesto}",
                        "competencias": [
                            {{
                                "competencia": "Nombre de la competencia",
                                "pregunta_star": "Pregunta situacional/conductual en formato STAR",
                                "preguntas_repregunta": [
                                    "Pregunta de repregunta 1 para profundizar",
                                    "Pregunta de repregunta 2 para profundizar"
                                ],
                                "rubrica": {{
                                    "nivel_1": "Descripción de respuesta Insuficiente / Deficiente",
                                    "nivel_3": "Descripción de respuesta Aceptable / Adecuada",
                                    "nivel_5": "Descripción de respuesta Excelente / Sobresaliente"
                                }},
                                "green_flags": ["Conducta positiva 1", "Conducta positiva 2"],
                                "red_flags": ["Señal de alerta 1", "Señal de alerta 2"]
                            }}
                        ]
                    }}
                    """

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )

                    contenido = json.loads(response.choices[0].message.content)
                    st.session_state["guia_generada"] = contenido
                    st.session_state["datos_puesto"] = {
                        "puesto": nombre_puesto,
                        "nivel": nivel_puesto
                    }
                    st.success("¡Guía generada con éxito! Dirígete a la pestaña '📋 Guía de Entrevista & Rúbrica' para revisarla.")

                except Exception as e:
                    st.error(f"Ocurrió un error durante la generación: {str(e)}")

# --- PESTAÑA 2: VISUALIZACIÓN DE GUÍA ---
with tab2:
    if st.session_state["guia_generada"] is None:
        st.info("👋 Aún no has generado ninguna guía. Ve a la pestaña '⚙️ Configuración del Puesto' para empezar.")
    else:
        datos = st.session_state["guia_generada"]
        st.subheader(f"📋 Guía de Entrevista: {datos.get('puesto')} ({datos.get('nivel')})")
        
        for item in datos.get("competencias", []):
            with st.expander(f"🔹 Competencia: {item.get('competencia')}", expanded=True):
                st.markdown(f"**❓ Pregunta STAR Principal:**")
                st.info(f"\"{item.get('pregunta_star')}\"")
                
                st.markdown("**🔍 Preguntas de Repregunta (Follow-up):**")
                for subq in item.get("preguntas_repregunta", []):
                    st.markdown(f"- {subq}")
                
                st.markdown("---")
                st.markdown("**📊 Rúbrica de Puntuación:**")
                
                rubrica = item.get("rubrica", {})
                col_r1, col_r3, col_r5 = st.columns(3)
                with col_r1:
                    st.error(f"**1 - Insuficiente**\n\n{rubrica.get('nivel_1')}")
                with col_r3:
                    st.warning(f"**3 - Adecuado**\n\n{rubrica.get('nivel_3')}")
                with col_r5:
                    st.success(f"**5 - Excelente**\n\n{rubrica.get('nivel_5')}")

                st.markdown("---")
                col_gf, col_rf = st.columns(2)
                with col_gf:
                    st.markdown("**✅ Green Flags (Señales Positivas):**")
                    for gf in item.get("green_flags", []):
                        st.markdown(f"- {gf}")
                with col_rf:
                    st.markdown("**🚩 Red Flags (Alertas):**")
                    for rf in item.get("red_flags", []):
                        st.markdown(f"- {rf}")

# --- PESTAÑA 3: EXPORTAR GUÍA ---
with tab3:
    if st.session_state["guia_generada"] is None:
        st.info("👋 Genera una guía primero para poder exportarla.")
    else:
        datos = st.session_state["guia_generada"]
        st.subheader("📥 Exportar Guía de Entrevista")
        st.write("Copia el texto a continuación o descárgalo para usarlo durante la sesión de selección.")

        # Construcción del texto plano formateado
        texto_exportable = f"====================================================\n"
        texto_exportable += f"GUÍA DE ENTREVISTA ESTRUCTURADA STAR\n"
        texto_exportable += f"Puesto: {datos.get('puesto')} | Nivel: {datos.get('nivel')}\n"
        texto_exportable += f"====================================================\n\n"

        for idx, comp in enumerate(datos.get("competencias", []), start=1):
            texto_exportable += f"--- {idx}. COMPETENCIA: {comp.get('competencia').upper()} ---\n\n"
            texto_exportable += f"PREGUNTA STAR:\n{comp.get('pregunta_star')}\n\n"
            texto_exportable += f"REPREGUNTAS SUGERIDAS:\n"
            for q in comp.get("preguntas_repregunta", []):
                texto_exportable += f"- {q}\n"
            texto_exportable += f"\nRÚBRICA DE EVALUACIÓN:\n"
            texto_exportable += f"  [1 - Insuficiente]: {comp.get('rubrica', {}).get('nivel_1')}\n"
            texto_exportable += f"  [3 - Adecuado]    : {comp.get('rubrica', {}).get('nivel_3')}\n"
            texto_exportable += f"  [5 - Excelente]   : {comp.get('rubrica', {}).get('nivel_5')}\n\n"
            texto_exportable += f"SEÑALES POSITIVAS (GREEN FLAGS):\n"
            for gf in comp.get("green_flags", []):
                texto_exportable += f"- {gf}\n"
            texto_exportable += f"\nSEÑALES DE ALERTA (RED FLAGS):\n"
            for rf in comp.get("red_flags", []):
                texto_exportable += f"- {rf}\n"
            texto_exportable += f"\n" + "="*50 + "\n\n"

        st.text_area("Vista previa del texto exportable:", texto_exportable, height=350)

        st.download_button(
            label="📄 Descargar Guía en Formato TXT",
            data=texto_exportable,
            file_name=f"Guia_Entrevista_{datos.get('puesto').replace(' ', '_')}.txt",
            mime="text/plain",
            use_container_width=True
        )