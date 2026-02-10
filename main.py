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

# --- 1. CONFIGURAÇÃO E ESTILO VISUAL (HARMONIA) ---
st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #2c3e50; }
    
    /* Botão EXECUTAR (Azul Profissional - Confiança) */
    div.stButton > button:first-child { 
        background-color: #2980b9; 
        color: white; 
        border-radius: 8px; 
        font-weight: bold; 
        height: 3.5em; 
        width: 100%; 
        border: none;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover { 
        background-color: #3498db; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Botão LIMPAR (Cinza Suave - Discrição) */
    button[kind="secondary"] {
        background-color: #ecf0f1;
        color: #7f8c8d;
        border: 1px solid #bdc3c7;
        border-radius: 8px;
        height: 3.5em;
        width: 100%;
    }
    button[kind="secondary"]:hover {
        background-color: #bdc3c7;
        color: #2c3e50;
    }
    
    /* Ajuste de Texto */
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #ced4da; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GESTÃO DE SESSÃO ---
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

# --- 3. TERMÔMETRO DE CORES (HIERARQUIA ABSOLUTA) ---
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    
    # REGRA 1: SOBERANIA DO VERDE (Se for seguro, ignora o resto)
    if "CLASSIFICAÇÃO: SEGURO" in texto_upper or "VEREDITO: SEGURO" in texto_upper or "LEGÍTIMO" in texto_upper:
        cor, font, icon = "#27ae60", "white", "🟢" # Verde Esmeralda (Sucesso)
        
    # REGRA 2: FRAUDE CONFIRMADA
    elif any(t in texto_upper for t in ["FRAUDE CONFIRMADA", "GOLPE", "SCAM", "CRIME"]):
        cor, font, icon = "#c0392b", "white", "🔴" # Vermelho Sangue (Perigo)
        
    # REGRA 3: ALTA ATENÇÃO (Laranja)
    elif any(t in texto_upper for t in ["ALTA ATENÇÃO", "PHISHING", "SUSPEITO", "MANIPULAÇÃO"]):
        cor, font, icon = "#d35400", "white", "🟠" # Laranja Escuro
        
    # REGRA 4: ATENÇÃO / FOTOS (Amarelo)
    elif any(t in texto_upper for t in ["ATENÇÃO", "IMAGEM", "FOTO", "IA", "SINTÉTICO"]):
        cor, font, icon = "#f39c12", "black", "🟡" # Amarelo Ouro
        
    # REGRA 5: NEUTRO (Azul)
    else:
        cor, font, icon = "#2980b9", "white", "🔵" # Azul Profissional
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border-left: 10px solid rgba(0,0,0,0.2); margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <span style="font-size: 1.2em;">{icon} ANÁLISE FORENSE:</span><br><br>
        {texto}
    </div>
    '''

# --- 4. CONEXÃO BLINDADA (AUTO-FALLBACK) ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Tenta conectar no modelo padrão, se falhar, o código avisa elegantemente
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("⚠️ Servidor em sincronização. Aguarde 30 segundos.")

# --- 5. CABEÇALHO E CONSENTIMENTO ---
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.info("🔒 **Protocolo de Segurança:** Ferramenta de IA Forense para auxílio à decisão. Resultados probabilísticos.")

st.markdown("---")

# --- 6. MESA DE PERÍCIA (ARQUIVOS + MINIATURAS) ---
new_files = st.file_uploader("📂 Mesa de Perícia (Arraste e-mails, PDFs ou Imagens):", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Evidências Coletadas:**")
    cols = st.columns(4)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 4]:
            if f['type'].startswith('image'):
                st.image(Image.open(io.BytesIO(f['content'])), width=100) # Miniatura controlada
            st.caption(f"📎 {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Analise a veracidade desta evidência.'", height=100)

# --- 7. BOTÕES EM HARMONIA (LADO A LADO) ---
c1, c2 = st.columns([1, 1])
with c1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        if not user_query and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("⏳ AuditIA realizando varredura multilinear..."):
                try:
                    instrucao = f"""Aja como AuditIA, perito forense sênior. Hoje: {agora}.
                    MANDAMENTO VISUAL:
                    1. Se o documento/imagem for autêntico, INICIE OBRIGATORIAMENTE COM: '**CLASSIFICAÇÃO: SEGURO**'.
                    2. Se for golpe, use: '**CLASSIFICAÇÃO: FRAUDE CONFIRMADA**'.
                    3. Se for suspeito, use: '**CLASSIFICAÇÃO: ALTA ATENÇÃO**'.
                    
                    ANÁLISE TÉCNICA:
                    - Analise cabeçalhos, metadados e marcadores anatômicos (se houver imagem).
                    - Seja direto e técnico."""
                    
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
                    response = model.generate_content(contexto, request_options={"timeout": 600}) # Timeout estendido para estabilidade
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e: st.error("Instabilidade momentânea. Tente novamente em instantes.")

with c2:
    # Botão secundário (Clear) com estilo sutil
    if st.button("🗑️ LIMPAR CASO", type="secondary"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.rerun()

# --- 8. CENTRAL DE AJUDA COMPLETA (SOLICITAÇÃO ATENDIDA) ---
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
        ### 🛠️ Manual de Per
