import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO E ACÚMULO DE PROVAS
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Forense Elite", page_icon="👁️", layout="wide")

# 2. SEMÁFORO DE CORES BLINDADO
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white"
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px;">{texto}</div>'

st.markdown("""<style>.stApp { background-color: #ffffff; color: #333333; } div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; } .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }</style>""", unsafe_allow_html=True)

# 3. CONEXÃO ESTÁVEL (FIX DEFINITIVO ERRO 404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Chamada explícita para evitar conflito de versão v1beta
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de Inicialização: {e}"); st.stop()

# SIDEBAR - CONCIERGE AUDITIA (HUMANIZADO E RESPONSIVO)
with st.sidebar:
    st.header("🤖 Concierge AuditIA")
    st.write("Olá! Sou seu assistente de suporte. Estou aqui para guiar sua perícia.")
    
    # OPÇÕES DE ESCOLHA RÁPIDA (PONTO 5)
    st.subheader("Sugestões de Apoio:")
    col_a, col_b = st.columns(2)
    if col_a.button("Auditando E-mails"): st.info("Suba arquivos .eml ou .pst. Analiso cabeçalhos, remetentes e links.")
    if col_b.button("Auditando Imagens"): st.info("Procuro por artefatos de IA, erros anatômicos e inconsistências de luz.")
    
    duvida_extra = st.text_input("Como posso ajudar agora?")
    if duvida_extra:
        # Prompt que ensina o assistente a responder antes de desistir
        prompt_ajuda = f"""
        Aja como um atendente sênior humanizado do AuditIA. 
        Conhecimento: Analisamos imagens (IA), E-mails (.eml/.pst), PDFs (até 1000 pág) e e-discovery. 
        AVISO: Atualmente NÃO auditamos arquivos de vídeo diretamente.
        Responda de forma clara: {duvida_extra}. 
        Se o usuário perguntar de vídeo, explique que estamos trabalhando nisso. 
        Só sugira o e-mail auditaiajuda@gmail.com se for uma falha técnica ou dúvida jurídica complexa.
        """
        try:
            res_ajuda = model.generate_content(prompt_ajuda)
            st.info(res_ajuda.text)
        except: st.write("Para suporte avançado, encaminhe sua dúvida para: auditaiajuda@gmail.com")
    
    st.markdown("---")
    st.caption("AuditIA V24 - Vargem Grande do Sul - SP")

# 4. CABEÇALHO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. INGESTÃO CUMULATIVA (PONTO 4)
new_files = st.file_uploader("📂 Arraste seus documentos, imagens ou e-mails aqui ou clique para fazer o upload:", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Arquivos em análise na sessão:**")
    cols = st.columns(min(len(st.session_state.arquivos_acumulados), 6))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 6]: st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Estes e-mails apresentam algum padrão de fraude financeira?'...", height=120)

# 6. MOTOR DE AUDITORIA (BLINDAGEM V24)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ AuditIA realizando varredura pericial..."):
                try:
                    instrucao = f"""Aja como AuditIA, perito forense sênior. Hoje: {agora}.
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO]** em negrito.
                    2. Logo abaixo: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'.
                    3. Analise todos os arquivos acumulados buscando fraudes, inconsistências ou sinais de IA.
                    4. Encerre com **RESUMO DO VEREDITO:**."""
                    
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    for f in st.session_state.arquivos_acumulados:
                        if f['name'].endswith('.eml'):
                            msg = email.message_from_bytes(f['content'], policy=policy.default)
                            contexto.append(f"E-MAIL ({f['name']}): {msg.get_body(preferencelist=('plain')).get_content()}")
                        elif f['name'].endswith('.pdf'): contexto.append({"mime_type": "application/pdf", "data": f['content']})
                        else: contexto.append(Image.open(io.BytesIO(f['content'])))
                    
                    contexto.append(pergunta_efetiva)
                    response = model.generate_content(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e: st.error(f"Erro técnico na análise: {e}")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. GUIA MESTRE (PONTO 3 - PRESERVADO)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia"):
    st.markdown("""### 🛡️ Inteligência Forense Profissional
    * 🕵️‍♀️ **Forense de Imagem**: Anatomia crítica e artefatos de IA.
    * ✉️ **e-Discovery & PST**: Auditoria de e-mails em massa.
    * 🚦 **Semáforo de Risco**: Vermelho, Laranja, Amarelo, Verde e Azul.
    * 🧠 **Memória Iterativa**: Histórico para follow-up sem perda de contexto.""")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
