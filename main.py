import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO E ACÚMULO DE PROVAS (PONTO 4)
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "chat_suporte" not in st.session_state:
    st.session_state.chat_suporte = [{"role": "assistant", "content": "Olá! Sou o Concierge AuditIA. Posso te ajudar a auditar links, verificar documentos ou realizar e-discovery. O que precisa?"}]

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Forense Profissional", page_icon="👁️", layout="wide")

# 2. SEMÁFORO DE CORES BLINDADO
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white"
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px;">{texto}</div>'

# CSS PARA O CHAT FLUTUANTE E LAYOUT (PONTO 5)
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }
    .floating-chat { position: fixed; bottom: 20px; right: 20px; width: 350px; background: white; border: 1px solid #ddd; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); z-index: 1000; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO ESTÁVEL (FIX DEFINITIVO ERRO 404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erro de conexão com o servidor pericial. Tente novamente em instantes."); st.stop()

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

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Analise a veracidade destes documentos e busque links suspeitos'...", height=120)

# 6. MOTOR DE AUDITORIA (BLINDAGEM V25)
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
                    instrucao = f"""Aja como AuditIA, perito sênior. Hoje: {agora}.
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO]** em negrito e maiúsculas.
                    2. Logo abaixo: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'.
                    3. Analise links, documentos e imagens acumulados buscando fraudes.
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
                except Exception as e: st.error(f"Erro na análise: Verifique sua conexão ou volume de dados.")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CONCIERGE FLUTUANTE (PONTO 5)
st.markdown("---")
with st.expander("💬 Conversar com Concierge AuditIA", expanded=False):
    st.write("Estou aqui para tirar suas dúvidas sobre o sistema de forma humanizada.")
    for msg in st.session_state.chat_suporte:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Como posso ajudar?"):
        st.session_state.chat_suporte.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            knowledge = """
            Você é o Concierge AuditIA. Você sabe:
            - Auditamos links suspeitos e phishing.
            - Verificamos veracidade de documentos e contratos.
            - Analisamos e-mails (.eml/.pst) e PDFs (até 1000 pág).
            - Identificamos IA em imagens (Anatomia Crítica).
            - Atualmente NÃO analisamos vídeo diretamente.
            Responda de forma humanizada. Só peça para enviar e-mail para auditaiajuda@gmail.com se for algo que você realmente não resolve.
            """
            response = model.generate_content(knowledge + prompt)
            st.write(response.text)
            st.session_state.chat_suporte.append({"role": "assistant", "content": response.text})

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
