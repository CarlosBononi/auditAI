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
if "chat_suporte" not in st.session_state:
    st.session_state.chat_suporte = [{"role": "assistant", "content": "Que satisfação tê-lo por aqui! Sou o Concierge AuditIA. Como posso iluminar sua investigação hoje?"}]

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

# Layout original que você prefere
st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. TERMÔMETRO DE CORES COM HIERARQUIA REAL (PONTO 1)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    # PRIORIDADE 1: VERDE (Se o veredito for seguro, ignora outros termos)
    if any(term in texto_upper for term in ["SEGURO", "TUDO OK", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO"]):
        cor, font = "#2ecc71", "white" 
    elif any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "GOLPE", "FAKE", "SCAM"]):
        cor, font = "#ff4b4b", "white" 
    elif any(term in texto_upper for term in ["ALTA ATENÇÃO", "MUITA ATENÇÃO", "PHISHING"]):
        cor, font = "#ffa500", "white" 
    elif "ATENÇÃO" in texto_upper:
        cor, font = "#f1c40f", "black" 
    else:
        cor, font = "#3498db", "white" # AZUL (NEUTRO)
    
    return f'''
    <div style="background-color: {cor}; padding: 30px; border-radius: 15px; color: {font}; 
    font-weight: bold; border: 2px solid #2c3e50; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        {texto}
    </div>
    '''

st.markdown("""<style>.stApp { background-color: #ffffff; color: #333333; } div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 12px; } .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; }</style>""", unsafe_allow_html=True)

# 3. MOTOR DE CONEXÃO RESTAURADO (BASEADO NO SEU MAIN QUE FUNCIONA)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Servidor pericial em sincronização. Aguarde 60 segundos."); st.stop()

# 4. CABEÇALHO ORIGINAL
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. INGESTÃO CUMULATIVA (PONTO 4 - ATUALIZADO)
new_files = st.file_uploader("📂 Arraste seus documentos, imagens ou e-mails aqui ou clique para fazer o upload:", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Provas Acumuladas na Mesa de Perícia:**")
    cols = st.columns(min(len(st.session_state.arquivos_acumulados), 6))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 6]: st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Analise a veracidade destes documentos'...", height=120)

# FUNÇÃO LAUDO PDF (RESTAURADA)
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 8, txt=conteudo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR DE AUDITORIA RIGOROSO (RESTAURADO)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando varredura forense..."):
                try:
                    instrucao = f"""Aja como AuditIA, inteligência forense de elite. Hoje: {agora}.
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO EM MAIÚSCULAS]** em negrito.
                    2. Tipos: SEGURO, FRAUDE CONFIRMADA, ALTA ATENÇÃO, ATENÇÃO ou INFORMATIVO.
                    3. Se for legítimo, use 'CLASSIFICAÇÃO: SEGURO'.
                    4. Responda diretamente e tecnicamente.
                    5. Encerre com **RESUMO DO VEREDITO:**."""
                    
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    for f in st.session_state.arquivos_acumulados:
                        if f['name'].endswith('.eml'):
                            msg = email.message_from_bytes(f['content'], policy=policy.default)
                            contexto.append(f"E-MAIL: {msg.get_body(preferencelist=('plain')).get_content()}")
                        elif f['name'].endswith('.pdf'): contexto.append({"mime_type": "application/pdf", "data": f['content']})
                        else: contexto.append(Image.open(io.BytesIO(f['content'])))
                    
                    contexto.append(pergunta_efetiva)
                    response = model.generate_content(contexto, request_options={"timeout": 600})
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except: st.error("Oscilação no servidor. Tente novamente em 60 segundos.")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CONCIERGE HUMANIZADO COM MÚLTIPLA ESCOLHA (PONTO 5)
st.markdown("---")
with st.container():
    st.subheader("💬 Atendimento Especializado AuditIA")
    for msg in st.session_state.chat_suporte:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    st.write("Como posso facilitar seu trabalho agora?")
    c1, c2, c3 = st.columns(3)
    if c1.button("Precisão do Robô"): st.info("Analisamos 12 marcadores anatômicos e metadados SPF/DKIM para garantir a máxima acurácia técnica.")
    if c2.button("Limites de Arquivo"): st.info("Você pode anexar até 5 arquivos simultâneos de 200MB cada (total 1GB).")
    if c3.button("Auditoria de Links"): st.info("Varremos domínios e redirecionamentos buscando indícios de phishing em tempo real.")

    if prompt_suporte := st.chat_input("Ou detalhe sua dúvida aqui:"):
        st.session_state.chat_suporte.append({"role": "user", "content": prompt_suporte})
        with st.chat_message("user"): st.write(prompt_suporte)
        with st.chat_message("assistant"):
            knowledge = "Você é o Concierge AuditIA. Seja humanizado e técnico. Explique os protocolos de auditoria antes de sugerir auditaiajuda@gmail.com."
            try:
                res = model.generate_content(knowledge + prompt_suporte)
                st.write(res.text); st.session_state.chat_suporte.append({"role": "assistant", "content": res.text})
            except: st.write("Tive uma pequena oscilação. Por favor, detalhe sua dúvida técnica ou use auditaiajuda@gmail.com.")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
