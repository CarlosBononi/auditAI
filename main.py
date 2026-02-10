import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import email
from email import policy
from datetime import datetime
import pytz

# ==============================
# 1. GESTÃO DE SESSÃO
# ==============================
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""
if "aceitou_termo" not in st.session_state:
    st.session_state.aceitou_termo = False

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

# ==============================
# 2. CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="AuditIA - Inteligência Pericial Sênior",
    page_icon="👁️",
    layout="centered"
)

# ==============================
# 3. TERMÔMETRO DE CLASSIFICAÇÃO
# ==============================
def aplicar_estilo_pericial(texto: str) -> str:
    texto_upper = texto.upper()
    if "SEGURO" in texto_upper or "EXIF" in texto_upper or "AUTENTICIDADE" in texto_upper:
        cor, font = "#2ecc71", "white"  # 🟢 Verde
    elif "INFORMATIVO" in texto_upper or "NEUTRO" in texto_upper:
        cor, font = "#3498db", "white"  # 🔵 Azul
    elif "ATENÇÃO" in texto_upper or "SEM RASTRO" in texto_upper or "SENSOR" in texto_upper:
        cor, font = "#f1c40f", "black"  # 🟡 Amarelo
    elif "INCONSISTÊNCIA" in texto_upper or "TÉCNICA" in texto_upper:
        cor, font = "#e67e22", "white"  # 🟠 Laranja
    elif "FRAUDE" in texto_upper or "MANIPULAÇÃO" in texto_upper or "GOLPE" in texto_upper:
        cor, font = "#c0392b", "white"  # 🔴 Vermelho
    else:
        cor, font = "#95a5a6", "white"  # fallback cinza

    return f"""
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font};
    font-weight: bold; margin-bottom: 20px; 
    box-shadow: 0 3px 10px rgba(0,0,0,0.15); text-align:center;">
        {texto}
    </div>
    """

# ==============================
# 4. ESTILO GLOBAL
# ==============================
st.markdown("""
    <style>
    .stApp { background-color: #fdfdfd; }
    div.stButton > button {
        border-radius: 10px;
        font-weight: bold;
        height: 3em;
        width: 100%;
        border: none;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        transition: 0.3s;
    }
    </style>
    """, unsafe_allow_html=True)

# ==============================
# 5. CONEXÃO COM GEMINI
# ==============================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    available_models = [m for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
    if available_models:
        model_name = available_models[0].name
        model = genai.GenerativeModel(model_name)
    else:
        st.error("Nenhum modelo disponível para generateContent.")
        st.stop()
except Exception as e:
    st.error(f"Erro na conexão com servidor Gemini: {e}")
    st.stop()

# ==============================
# 6. CABEÇALHO
# ==============================
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except FileNotFoundError:
    st.title("👁️ AuditIA")

st.markdown("---")

# ==============================
# 7. TERMO DE CONSENTIMENTO
# ==============================
st.subheader("⚠️ Termo de Consentimento")
st.write("""
Este sistema é uma ferramenta de **auditoria digital baseada em inteligência artificial**.  
Os resultados apresentados são **probabilísticos** e devem ser validados por **perícia humana oficial**.  
O AuditIA não substitui profissionais credenciados e pode apresentar erros devido à natureza da tecnologia.  
Ao prosseguir, você declara estar ciente dos riscos e limitações.
""")

aceite = st.radio("Estou ciente dos termos e desejo continuar:", ["Não", "Sim"])
st.session_state.aceitou_termo = (aceite == "Sim")

st.markdown("---")

# ==============================
# 8. UPLOAD DE ARQUIVOS
# ==============================
if st.session_state.aceitou_termo:
    new_files = st.file_uploader(
        "📂 Upload de Provas (Prints, PDFs, E-mails .eml):",
        type=["jpg", "png", "jpeg", "pdf", "eml", "pst"],
        accept_multiple_files=True
    )

    if new_files:
        for f in new_files:
            if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
                st.session_state.arquivos_acumulados.append({
                    'name': f.name,
                    'content': f.read(),
                    'type': f.type
                })

    if st.session_state.arquivos_acumulados:
        st.write("📦 **Mesa de Perícia (Miniaturas das Provas):**")
        cols = st.columns(4)
        for i, f in enumerate(st.session_state.arquivos_acumulados):
            with cols[i % 4]:
                if f['type'].startswith('image'):
                    st.image(Image.open(io.BytesIO(f['content'])), width=150)
                st.caption(f"✅ {f['name']}")

    # ==============================
    # 9. HISTÓRICO DE INVESTIGAÇÃO
    # ==============================
    st.subheader("🕵️ Linha de Investigação")
    for bloco in st.session_state.historico_pericial:
        st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

    # ==============================
    # 10. PERGUNTA AO PERITO
    # ==============================
    user_query = st.text_area(
        "📝 Pergunta ao Perito:",
        key="campo_pergunta",
        placeholder="Ex: 'Analise a veracidade desta evidência.'",
        height=120
    )

    # ==============================
    # 11. BOTÕES DE AÇÃO
    # ==============================
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 EXECUTAR PERÍCIA"):
            if not user_query and not st.session_state.arquivos_acumulados:
                st.warning("Insira material.")
            else:
                tz_br = pytz.timezone('America/Sao_Paulo')
                agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
                with st.spinner("🕵️ Realizando auditoria técnica profunda..."):
                    try:
                        instrucao = (
                            "Aja como AuditIA, perito forense sênior. "
                            "Inicie com **CLASSIFICAÇÃO: [TIPO]**. "
                            "Se for legítimo, use 'CLASSIFICAÇÃO: SEGURO'."
                        )
                        contexto = [instrucao]
                        contexto.extend(st.session_state.historico_pericial)

                        for f in st.session_state.arquivos_acumulados:
                            if f['name'].endswith('.eml'):
                                msg = email.message_from_bytes(f['content'], policy=policy.default)
                                corpo_email = msg.get_body(preferencelist=('plain'))
                                if corpo_email:
                                    contexto.append(f"E-MAIL: {corpo_email.get_content()}")
                            elif f['type'] == "application/pdf":
                                contexto.append({"mime_type": "application/pdf", "data": f['content']})
                            else:
                                contexto.append(Image.open(io.BytesIO(f['content'])).convert('RGB'))

                        if st.session_state.pergunta_ativa:
                            contexto.append(st.session_state.pergunta_ativa)

                                               response = model.generate_content(contexto, request_options={"timeout": 600})
                        if response and hasattr(response, "text"):
                            st.session_state.historico_pericial.append(response.text)
                        else:
                            st.error("Resposta inválida do modelo.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro de instabilidade: {e}")

    with col2:
        if st.button("🗑️ LIMPAR CASO"):
            st.session_state.historico_pericial = []
            st.session_state.arquivos_acumulados = []
            st.session_state.pergunta_ativa = ""
            st.rerun()

# ==============================
# 12. CENTRAL DE AJUDA
# ==============================
st.markdown("---")
with st.expander("📖 Central de Ajuda AuditIA - Conhecimento Técnico e FAQ"):
    tab1, tab2, tab3 = st.tabs(["A Origem do AuditIA", "Manual de Operação", "FAQ Técnico"])

    with tab1:
        st.markdown("""
        ### 🧬 A Missão AuditIA
        Nascido em **Vargem Grande do Sul - SP**, o AuditIA foi concebido para unir a psicologia forense à tecnologia de ponta.  
        O projeto surgiu da necessidade de identificar micro-anomalias em comunicações digitais que fogem ao olho humano.

        **Nossos 7 Pilares de Investigação:**
        1. **Análise Documental**: Verificação de fontes e metadados estruturais.
        2. **Detecção de IA**: Scrutínio de 12 marcadores anatômicos e texturas sintéticas.
        3. **e-Discovery**: Processamento de arquivos .eml e .pst buscando intenções criminosas.
        4. **Engenharia Social**: Identificação de padrões de phishing e spoofing comportamental.
        5. **Física da Luz**: Verificação de reflexos oculares e sombras em provas visuais.
        6. **Ponzi Detection**: Análise técnica de modelos de promessas financeiras inconsistentes.
        7. **Consistência Digital**: Comparação entre o que é dito e o rastro digital deixado.
        """)

    with tab2:
        st.markdown("""
        ### 🛠️ Manual de Perícia Profissional
        - **Mesa de Perícia**: Adicione até 5 arquivos para uma auditoria conjunta.
        - **Pergunta ao Perito**: Seja cirúrgico. "Analise a textura de pele e sombras desta face" gera resultados superiores.
        - **Interpretando o Termômetro**:
           - 🟢 **Verde**: Autenticidade confirmada com rastro EXIF.
           - 🔵 **Azul**: Documento informativo neutro.
           - 🟡 **Amarelo**: Imagem sem rastro de sensor digital (Atenção!).
           - 🟠 **Laranja**: Inconsistências técnicas detectadas.
           - 🔴 **Vermelho**: Fraude ou manipulação confirmada.
        """)

    with tab3:
        st.markdown("""
        ### ❓ FAQ Técnico
        **Q: Por que o AuditIA foi criado?**  
        R: Para dar armas técnicas a advogados e auditores contra o avanço de fraudes sintéticas.  

        **Q: Como funciona a detecção de fotos?**  
        R: Analisamos 12 marcadores, como número de articulações e padrões de ruído digital.  

        **Q: Qual o limite de upload?**  
        R: Arquivos de até 200MB, garantindo processamento rápido.  

        *Este artigo foi útil? Envie feedback para auditaiajuda@gmail.com*
        """)

# ==============================
# 13. RODAPÉ
# ==============================
st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | VGS - SP")
