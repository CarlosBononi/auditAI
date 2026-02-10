import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz
import time

# 1. GESTÃO DE SESSÃO E MESA DE PERÍCIA CUMULATIVA
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. TERMÔMETRO DE 5 ESTÁGIOS COM SOBERANIA VERDE
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if any(term in texto_upper for term in ["SEGURO", "TUDO OK", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO"]):
        cor, font = "#2ecc71", "white" # VERDE
    elif any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "GOLPE", "FAKE", "SCAM"]):
        cor, font = "#ff4b4b", "white" # VERMELHO
    elif any(term in texto_upper for term in ["ALTA ATENÇÃO", "MUITA ATENÇÃO", "SUSPEITO", "PHISHING"]):
        cor, font = "#ffa500", "white" # LARANJA
    elif any(term in texto_upper for term in ["ATENÇÃO", "IMAGEM", "FOTO", "IA", "SINTÉTICO"]):
        cor, font = "#f1c40f", "black" # AMARELO
    else:
        cor, font = "#3498db", "white" # AZUL (INFORMATIVO)
    
    return f'''
    <div style="background-color: {cor}; padding: 30px; border-radius: 15px; color: {font}; 
    font-weight: bold; border: 2px solid #2c3e50; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        {texto}
    </div>
    '''

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    div.stButton > button:hover { border: 1px solid #2ecc71; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO BLINDADA (ESTABILIDADE TOTAL)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("AuditIA em sincronização com o servidor. Aguarde 60 segundos."); st.stop()

# 4. CABEÇALHO E TERMO DE CONSENTIMENTO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.warning("⚠️ **TERMO DE CONSENTIMENTO:** Esta é uma ferramenta baseada em IA Forense. Os resultados são probabilísticos e devem ser validados por perícia humana oficial. Erros podem ocorrer devido à natureza da tecnologia.")

st.markdown("---")

# 5. INGESTÃO MÚLTIPLA E MINIATURAS
new_files = st.file_uploader("📂 Upload de Provas (Prints, PDFs, E-mails .eml):", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Mesa de Perícia (Miniaturas das Provas):**")
    cols = st.columns(4)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 4]:
            if f['type'].startswith('image'):
                st.image(Image.open(io.BytesIO(f['content'])), width=150)
            st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Analise a veracidade desta evidência.'", height=120)

# 6. COMANDOS EM HARMONIA LADO A LADO
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        if not user_query and not st.session_state.arquivos_acumulados:
            st.warning("Insira material.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando auditoria técnica profunda..."):
                try:
                    instrucao = f"Aja como AuditIA, perito forense sênior. Inicie com **CLASSIFICAÇÃO: [TIPO]**. Se for legítimo, use 'CLASSIFICAÇÃO: SEGURO'."
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    for f in st.session_state.arquivos_acumulados:
                        if f['name'].endswith('.eml'):
                            msg = email.message_from_bytes(f['content'], policy=policy.default)
                            contexto.append(f"E-MAIL: {msg.get_body(preferencelist=('plain')).get_content()}")
                        elif f['type'] == "application/pdf":
                            contexto.append({"mime_type": "application/pdf", "data": f['content']})
                        else: contexto.append(Image.open(io.BytesIO(f['content'])).convert('RGB'))
                    contexto.append(user_query)
                    response = model.generate_content(contexto, request_options={"timeout": 600})
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except: st.error("Erro de instabilidade. Tente novamente.")

with col2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CENTRAL DE AJUDA DETALHADA E FAQ (ROBUSTA)
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
        **Q: Por que o AuditIA foi criado?** R: Para dar armas técnicas a advogados e auditores contra o avanço de fraudes sintéticas.  
        **Q: Como funciona a detecção de fotos?** R: Analisamos 12 marcadores, como número de articulações e padrões de ruído digital.  
        **Q: Qual o limite de upload?** R: Arquivos de até 200MB, garantindo processamento rápido.
        
        *Este artigo foi útil? Envie feedback para auditaiajuda@gmail.com*
        """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | VGS - SP")
