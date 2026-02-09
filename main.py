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
if "mensagens_concierge" not in st.session_state:
    st.session_state.mensagens_concierge = [{"role": "assistant", "content": "Olá! Sou o Concierge AuditIA. Posso te ajudar a auditar links, verificar documentos ou realizar e-discovery. O que precisa?"}]

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Forense Elite", page_icon="👁️", layout="wide")

# 2. SEMÁFORO DE CORES BLINDADO (PONTOS 1 E 2)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white"
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px;">{texto}</div>'

st.markdown("""<style>.stApp { background-color: #ffffff; color: #333333; } div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }</style>""", unsafe_allow_html=True)

# 3. CONEXÃO RESILIENTE (FIX 404/NOTFOUND)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Tentativa de seleção automática de modelo estável
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0] if modelos else 'gemini-1.5-flash')
except:
    st.error("Instabilidade nos servidores de análise. Aguarde um momento."); st.stop()

# 4. CONCIERGE "SPECIALIST" (PONTO 5)
with st.sidebar:
    st.header("🤖 Concierge AuditIA")
    for msg in st.session_state.mensagens_concierge:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt := st.chat_input("Dúvida técnica?"):
        st.session_state.mensagens_concierge.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.write(prompt)
        
        with st.chat_message("assistant"):
            knowledge = """
            Você é o Concierge AuditIA, um assistente humanizado e expert em perícia digital.
            CAPACIDADES DO SISTEMA:
            - Auditamos links suspeitos (phishing) e domínios maliciosos.
            - Verificamos veracidade de documentos, contratos e metadados.
            - e-Discovery em e-mails (.eml/.pst) e PDFs (até 1000 pág).
            - Detectamos IA em fotos (Anatomia Crítica, Luz, Textura).
            - Vídeo: Ainda não auditamos vídeo diretamente.
            - Suporte Humano: Apenas para casos insolúveis, use auditaiajuda@gmail.com.
            Sempre explique como fazer o procedimento antes de sugerir contato externo.
            """
            try:
                res = model.generate_content(knowledge + prompt)
                st.write(res.text)
                st.session_state.mensagens_concierge.append({"role": "assistant", "content": res.text})
            except: st.write("Tive um problema técnico. Envie sua dúvida para: auditaiajuda@gmail.com")

# 5. CABEÇALHO E INGESTÃO CUMULATIVA (PONTO 4)
try: st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")
new_files = st.file_uploader("📂 Arraste seus documentos, imagens ou e-mails aqui ou clique para fazer o upload:", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Provas Acumuladas na Investigação:**")
    cols = st.columns(min(len(st.session_state.arquivos_acumulados), 6))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 6]: st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Estes documentos são legítimos? Analise os cabeçalhos do e-mail em busca de fraude.'...", height=120)

# FUNÇÃO LAUDO PDF
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=11); pdf.ln(10)
    pdf.multi_cell(0, 8, txt=conteudo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR PERICIAL (BLINDAGEM TOTAL)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Forneça material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando varredura pericial avançada..."):
                try:
                    instrucao = f"""Aja como AuditIA, perito forense sênior. Hoje: {agora}.
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO]** em negrito e maiúsculas.
                    2. Logo abaixo: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'.
                    3. Analise todos os arquivos acumulados buscando fraudes, phishing em links e sinais de IA.
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
                except: st.error("Instabilidade na análise. Verifique sua conexão.")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. GUIA MESTRE (PONTO 3 - PRESERVADO)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia"):
    st.markdown("""### 🛡️ Inteligência Forense Profissional
    * 🕵️‍♀️ **Forense de Imagem**: Anatomia crítica e detecção de artefatos de IA.
    * ✉️ **e-Discovery & PST**: Auditoria de massa de e-mails corporativos.
    * 🚦 **Semáforo de Risco**: Vermelho, Laranja, Amarelo, Verde e Azul.
    * 🧠 **Memória Iterativa**: Histórico para follow-up sem perda de contexto.""")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
