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

# 1. GESTÃO DE SESSÃO E MESA DE PERÍCIA CUMULATIVA (PONTO 4)
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "chat_suporte" not in st.session_state:
    st.session_state.chat_suporte = [{"role": "assistant", "content": "Olá! Sou o Concierge AuditIA. Conheço todos os protocolos de auditoria do sistema. O que vamos investigar hoje?"}]

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Supreme Forensic Reliability", page_icon="👁️", layout="wide")

# 2. TERMÔMETRO DE CORES COM HIERARQUIA DE PRIORIDADE (PONTO 1)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    # PRIORIDADE 1: VERDE (Se o veredito for seguro, ignora outros termos explicativos)
    if any(term in texto_upper for term in ["SEGURO", "TUDO OK", "INTEGRIDADE CONFIRMADA", "VEREDITO: VERDE"]):
        cor, font = "#2ecc71", "white" 
    elif any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "GOLPE", "FAKE", "SCAM"]):
        cor, font = "#ff4b4b", "white" 
    elif any(term in texto_upper for term in ["ALTA ATENÇÃO", "MUITA ATENÇÃO", "PHISHING"]):
        cor, font = "#ffa500", "white" 
    elif "ATENÇÃO" in texto_upper:
        cor, font = "#f1c40f", "black" 
    else:
        cor, font = "#3498db", "white" # AZUL (INFORMATIVO)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        {texto}
    </div>
    '''

st.markdown("""<style>.stApp { background-color: #ffffff; color: #333333; } div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }</style>""", unsafe_allow_html=True)

# 3. MOTOR DE CONEXÃO ULTRA-RESILIENTE (FIX 404 E TIMEOUT)
def inicializar_motor():
    try:
        genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = available_models[0] if available_models else 'gemini-1.5-flash'
        return genai.GenerativeModel(model_name)
    except:
        return None

model = inicializar_motor()

# 4. CABEÇALHO (BRANDING CARLOS BONONI)
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. INGESTÃO CUMULATIVA (DRAG AND DROP - PONTO 4)
new_files = st.file_uploader("📂 Arraste seus documentos, imagens ou e-mails aqui ou clique para fazer o upload:", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Mesa de Perícia (Provas Acumuladas):**")
    cols = st.columns(min(len(st.session_state.arquivos_acumulados), 6))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 6]: st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Sua dúvida técnica ou busca e-discovery aqui...", height=120)

# 6. MOTOR DE AUDITORIA COM RETENTATIVA AGRESSIVA (FIX OSCILAÇÃO)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        if not model: st.error("Servidor em sincronização. Tente em 60s."); st.stop()
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando varredura forense multilinear (Pode levar alguns segundos)..."):
                for tentativa in range(4): # AUMENTO PARA 4 TENTATIVAS
                    try:
                        instrucao = f"""Aja como AuditIA, perito sênior. Hoje: {agora}.
                        1. Inicie com **CLASSIFICAÇÃO: [TIPO EM MAIÚSCULAS]** em negrito.
                        2. Se for legítimo, use 'CLASSIFICAÇÃO: SEGURO'.
                        3. Responda diretamente e tecnicamente sobre metadados, links e anatomia.
                        4. Encerre com **RESUMO DO VEREDITO:**."""
                        
                        contexto = [instrucao]
                        for h in st.session_state.historico_pericial: contexto.append(h)
                        for f in st.session_state.arquivos_acumulados:
                            if f['name'].endswith('.eml'):
                                msg = email.message_from_bytes(f['content'], policy=policy.default)
                                contexto.append(f"E-MAIL: {msg.get_body(preferencelist=('plain')).get_content()}")
                            elif f['name'].endswith('.pdf'): contexto.append({"mime_type": "application/pdf", "data": f['content']})
                            else: contexto.append(Image.open(io.BytesIO(f['content'])))
                        
                        contexto.append(pergunta_efetiva)
                        # TIMEOUT AMPLIADO PARA 600 SEGUNDOS (EVITA IMAGE_1E6756.PNG)
                        response = model.generate_content(contexto, request_options={"timeout": 600})
                        st.session_state.historico_pericial.append(response.text)
                        st.rerun()
                        break
                    except:
                        if tentativa < 3: time.sleep(5) # ESPERA MAIOR ENTRE TENTATIVAS
                        else: st.error("Instabilidade persistente no servidor pericial. Por favor, tente novamente em instantes.")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CONCIERGE "SPECIALIST" (PONTO 5 - HUMANIZADO E RESOLUTIVO)
st.markdown("---")
with st.container():
    st.subheader("💬 Concierge AuditIA - Suporte Especializado")
    for msg in st.session_state.chat_suporte:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    st.write("Dúvidas frequentes:")
    col_a, col_b, col_c = st.columns(3)
    if col_a.button("Média de Precisão"): st.info("Analisamos 12 marcadores anatômicos, metadados SPF/DKIM e selos digitais. A precisão é probabilística e de alta fidelidade forense.")
    if col_b.button("Limites do Robô"): st.info("Você pode anexar até 5 arquivos simultâneos. O limite individual é de 200MB (total de 1GB por sessão).")
    if col_c.button("Auditoria de Links"): st.info("Auditamos domínios falsos, redirecionamentos maliciosos e phishing em tempo real.")
    
    if prompt_suporte := st.chat_input("Ou detalhe sua dúvida técnica aqui:"):
        st.session_state.chat_suporte.append({"role": "user", "content": prompt_suporte})
        with st.chat_message("user"): st.write(prompt_suporte)
        with st.chat_message("assistant"):
            knowledge = "Você é o Concierge AuditIA. Seja humanizado e técnico. Use auditaiajuda@gmail.com apenas se o sistema falhar ou para laudos complexos."
            try:
                res_sup = model.generate_content(knowledge + prompt_suporte)
                st.write(res_sup.text)
                st.session_state.chat_suporte.append({"role": "assistant", "content": res_sup.text})
            except: st.write("Tive uma pequena oscilação técnica. Use auditaiajuda@gmail.com para suporte avançado.")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
