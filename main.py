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
    st.session_state.chat_suporte = [{"role": "assistant", "content": "Olá! Sou o Concierge AuditIA. Conheço todos os protocolos de auditoria (Phishing, Documentos, IA). Como posso guiar sua investigação?"}]

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Supreme Forensic Intelligence", page_icon="👁️", layout="wide")

# 2. TERMÔMETRO DE CORES COM HIERARQUIA DE PRIORIDADE VERDE (PONTO 1)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    # PRIORIDADE 1: VERDE (Segurança confirmada ignora gatilhos de alerta explicativos)
    if "SEGURO" in texto_upper or "TUDO OK" in texto_upper or "INTEGRIDADE CONFIRMADA" in texto_upper:
        cor, font = "#2ecc71", "white" # VERDE
    elif any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "GOLPE", "FAKE", "SCAM"]):
        cor, font = "#ff4b4b", "white" # VERMELHO
    elif any(term in texto_upper for term in ["ALTA ATENÇÃO", "MUITA ATENÇÃO", "PHISHING", "ALTAMENTE SUSPEITO"]):
        cor, font = "#ffa500", "white" # LARANJA
    elif "ATENÇÃO" in texto_upper:
        cor, font = "#f1c40f", "black" # AMARELO
    else:
        cor, font = "#3498db", "white" # AZUL (NEUTRO)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        {texto}
    </div>
    '''

st.markdown("""<style>.stApp { background-color: #ffffff; color: #333333; } div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }</style>""", unsafe_allow_html=True)

# 3. ESCUDO DE CONEXÃO (FIX DEFINITIVO 404 E CAIXA ROSA)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Chamada resiliente para evitar erro de versão instável
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("AuditIA em sincronização com o servidor forense. Aguarde 60 segundos."); st.stop()

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

# FUNÇÃO LAUDO PDF
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=11); pdf.ln(10)
    pdf.multi_cell(0, 8, txt=conteudo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR DE AUDITORIA (CONSOLIDADO E RIGOROSO - PONTOS 1 E 2)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ AuditIA realizando varredura forense..."):
                try:
                    instrucao = f"""Aja como AuditIA, inteligência forense sênior. Hoje: {agora}.
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO EM MAIÚSCULAS]** em negrito.
                    2. Use o termômetro: FRAUDE CONFIRMADA, ALTA ATENÇÃO, ATENÇÃO, SEGURO ou INFORMATIVO.
                    3. Se o material for autêntico e seguro, use obrigatoriamente 'CLASSIFICAÇÃO: SEGURO'.
                    4. Analise cabeçalhos SPF/DKIM para e-mails e metadados para documentos.
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
                    response = model.generate_content(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except: st.error("Instabilidade momentânea no servidor. Por favor, tente novamente em 60 segundos.")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CONCIERGE "HUMANIZED EXPERT" (PONTO 5)
st.markdown("---")
with st.container():
    st.subheader("💬 Atendimento Especializado AuditIA")
    for msg in st.session_state.chat_suporte:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt_suporte := st.chat_input("Dúvida técnica sobre limites, precisão ou como funciona?"):
        st.session_state.chat_suporte.append({"role": "user", "content": prompt_suporte})
        with st.chat_message("user"): st.write(prompt_suporte)
        with st.chat_message("assistant"):
            knowledge = """
            Você é o Concierge AuditIA. Seja um assistente humanizado, técnico e consultivo.
            - Precisão: Explique que nossa precisão é maximizada por auditoria multilinear (SPF, DKIM, Anatomia, Metadados).
            - Limites: Podemos processar até 5 arquivos simultâneos de 200MB cada (total 1GB).
            - Procedimento: Se a dúvida for vaga, pergunte ao usuário o que ele deseja auditar especificamente.
            - Nunca responda de forma curta ou seca. Ofereça conhecimento técnico primeiro.
            - Responda na primeira linha. Use auditaiajuda@gmail.com apenas para erros de sistema ou casos comerciais.
            """
            try:
                res_sup = model.generate_content(knowledge + prompt_suporte)
                st.write(res_sup.text)
                st.session_state.chat_suporte.append({"role": "assistant", "content": res_sup.text})
            except: st.write("Tive uma pequena oscilação técnica. Detalhe sua dúvida ou envie para auditaiajuda@gmail.com")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
