import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO E ACÚMULO (PONTO 4)
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "chat_suporte" not in st.session_state:
    st.session_state.chat_suporte = [{"role": "assistant", "content": "Olá! Sou o Concierge AuditIA. Posso te ajudar a auditar links, verificar a autenticidade de documentos ou realizar e-discovery. O que precisa?"}]

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

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO ESTÁVEL (FIX DEFINITIVO 404/NOTFOUND)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Busca dinâmica para garantir o nome correto do modelo na sua conta
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model_name = available_models[0] if available_models else 'gemini-1.5-flash'
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error("Erro de conexão com o servidor. A API está instável, aguarde um momento."); st.stop()

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
    st.write("📦 **Provas Acumuladas na Sessão:**")
    cols = st.columns(min(len(st.session_state.arquivos_acumulados), 6))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 6]: st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Estes documentos são autênticos? Busque por links suspeitos e cabeçalhos forjados.'...", height=120)

# 6. MOTOR DE AUDITORIA (BLINDAGEM V26)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando varredura pericial avançada..."):
                try:
                    instrucao = f"""Aja como AuditIA, perito forense sênior. Hoje: {agora}.
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO]** em negrito e maiúsculas.
                    2. Logo abaixo: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'.
                    3. Analise links, documentos e e-mails acumulados buscando fraudes técnicas.
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
                except: st.error("Instabilidade na análise. Verifique sua conexão ou volume de dados.")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CONCIERGE "WIDGET" (PONTO 5 - HUMANIZADO)
st.markdown("---")
with st.container():
    st.subheader("💬 Concierge AuditIA - Suporte Humanizado")
    for msg in st.session_state.chat_suporte:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Dúvida técnica ou operacional?"):
        st.session_state.chat_suporte.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            knowledge = """
            Você é o Concierge AuditIA. Seja humanizado e técnico.
            CONHECIMENTOS:
            - Auditamos links suspeitos (phishing) e domínios.
            - Verificamos veracidade de documentos, contratos e metadados.
            - Realizamos e-discovery em .eml e .pst.
            - Identificamos geração por IA em fotos (Anatomia Crítica).
            - Vídeo: Ainda não analisamos vídeo diretamente.
            - Dificuldades técnicas ou jurídicas? auditaiajuda@gmail.com.
            Sempre tente explicar o procedimento antes de sugerir o e-mail.
            """
            try:
                response = model.generate_content(knowledge + prompt)
                st.write(response.text)
                st.session_state.chat_suporte.append({"role": "assistant", "content": response.text})
            except: st.write("Tive uma falha momentânea. Por favor, envie sua dúvida para auditaiajuda@gmail.com")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
