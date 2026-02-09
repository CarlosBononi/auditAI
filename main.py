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
if "chat_suporte" not in st.session_state:
    st.session_state.chat_suporte = [{"role": "assistant", "content": "Olá! Sou o Concierge AuditIA. O que você precisa saber agora? Seja direto."}]

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Forense Elite", page_icon="👁️", layout="wide")

# 2. SEMÁFORO DE CORES COM SENSIBILIDADE MÁXIMA
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "PHISHING", "SCAM", "GOLPE", "FAKE"]):
        cor, font = "#ff4b4b", "white" # VERMELHO
    elif any(term in texto_upper for term in ["POSSÍVEL FRAUDE", "SUSPEITA", "INCONSISTENTE"]):
        cor, font = "#ffa500", "white" # LARANJA
    elif "ATENÇÃO" in texto_upper:
        cor, font = "#f1c40f", "black" # AMARELO
    elif "SEGURO" in texto_upper:
        cor, font = "#2ecc71", "white" # VERDE
    else:
        cor, font = "#3498db", "white" # AZUL (Informativo)
    
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">{texto}</div>'

st.markdown("""<style>.stApp { background-color: #ffffff; color: #333333; } div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }</style>""", unsafe_allow_html=True)

# 3. CONEXÃO ESTÁVEL
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos_disp[0] if modelos_disp else 'gemini-1.5-flash')
except:
    st.error("Erro de conexão. Tente novamente."); st.stop()

# 4. CABEÇALHO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. INGESTÃO CUMULATIVA (DRAG AND DROP)
new_files = st.file_uploader("📂 Arraste seus documentos, imagens ou e-mails aqui ou clique para fazer o upload:", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Provas Acumuladas:**")
    cols = st.columns(min(len(st.session_state.arquivos_acumulados), 6))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 6]: st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Analise os e-mails e a foto em conjunto buscando por fraude'...", height=120)

# FUNÇÃO LAUDO PDF
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=11); pdf.ln(10)
    pdf.multi_cell(0, 8, txt=conteudo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR DE AUDITORIA (BLINDAGEM V29)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ AuditIA realizando auditoria forense..."):
                try:
                    instrucao = f"""Aja como AuditIA. Hoje: {agora}.
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO]** em negrito e maiúsculas.
                    2. Responda diretamente e tecnicamente.
                    3. Termine com **RESUMO DO VEREDITO:**."""
                    
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
                except: st.error("Erro na análise. Tente novamente.")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CONCIERGE "DIRECT" (HUMANIZADO E OBJETIVO)
st.markdown("---")
with st.container():
    st.subheader("💬 Concierge AuditIA")
    for msg in st.session_state.chat_suporte:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt_suporte := st.chat_input("Como posso ajudar de forma direta?"):
        st.session_state.chat_suporte.append({"role": "user", "content": prompt_suporte})
        with st.chat_message("user"): st.write(prompt_suporte)
        with st.chat_message("assistant"):
            # NOVA DIRETRIZ: Resposta direta na primeira linha.
            knowledge = "Aja como o Concierge AuditIA. RESPONDA O QUE FOI PERGUNTADO NA PRIMEIRA LINHA DE FORMA OBJETIVA. Não repita o manual inteiro. Limite-se a responder a dúvida. Se não souber, indique auditaiajuda@gmail.com."
            try:
                res_sup = model.generate_content(knowledge + prompt_suporte)
                st.write(res_sup.text)
                st.session_state.chat_suporte.append({"role": "assistant", "content": res_sup.text})
            except: st.write("Tive uma falha. Envie sua dúvida para auditaiajuda@gmail.com")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
