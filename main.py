import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO E RASTREABILIDADE
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Forense Consolidada", page_icon="👁️", layout="wide")

# 2. SEMÁFORO DE CORES COM LÓGICA DE DETECÇÃO (PONTOS 1 E 2)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white" # Azul (Informativo)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        {texto}
    </div>
    '''

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transition: 0.3s; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO E ASSISTENTE DE SIDEBAR (PONTO 5)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Erro de Conexão API."); st.stop()

with st.sidebar:
    st.header("🤖 Assistente AuditIA")
    pergunta_suporte = st.text_input("Dúvida rápida sobre o sistema?")
    if pergunta_suporte:
        response_suporte = model.generate_content(f"Responda como um assistente técnico do AuditIA: {pergunta_suporte}")
        st.write(response_suporte.text)
        st.markdown("Para suporte avançado, [fale com nosso perito especialista](https://wa.me/5511913556631).")
    st.markdown("---")
    st.caption("AuditIA V21 - Vargem Grande do Sul - SP")

# 4. CABEÇALHO
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. INGESTÃO MULTIFUNCIONAL (PONTO 4)
uploaded_files = st.file_uploader("📂 Arraste seus documentos, imagens ou e-mails aqui ou clique para fazer o upload:", 
                                  type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], 
                                  accept_multiple_files=True)

if uploaded_files:
    cols = st.columns(len(uploaded_files))
    for i, f in enumerate(uploaded_files):
        with cols[i]:
            if f.name.lower().endswith(('jpg', 'png', 'jpeg')):
                st.image(f, width=150, caption=f.name)
            else: st.write(f"📄 {f.name}")

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

# 6. MOTOR DE AUDITORIA (CONSOLIDADO)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not uploaded_files:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando auditoria multilinear..."):
                try:
                    instrucao = f"""Aja como AuditIA, perito forense sênior. Data: {agora}.
                    
                    REGRAS OBRIGATÓRIAS DE RESPOSTA:
                    1. Comece com: **CLASSIFICAÇÃO: [TIPO EM MAIÚSCULAS]** em negrito.
                    2. Logo abaixo: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'.
                    3. Se houver e-mails ou PDFs, foque em TEXTO e CABEÇALHOS. Não mencione anatomia de imagem.
                    4. Se houver imagens, use o protocolo de detecção de artefatos de IA.
                    5. Encerre com: **RESUMO DO VEREDITO:** seguido da conclusão final.
                    
                    Busque fraudes agressivamente. Se encontrar inconsistências, classifique como FRAUDE CONFIRMADA."""
                    
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    
                    if uploaded_files:
                        for f in uploaded_files:
                            ext = f.name.split('.')[-1].lower()
                            if ext == 'eml':
                                msg = email.message_from_bytes(f.read(), policy=policy.default)
                                contexto.append(f"E-MAIL ({f.name}): {msg.get_body(preferencelist=('plain')).get_content()}")
                            elif ext == 'pdf': contexto.append({"mime_type": "application/pdf", "data": f.read()})
                            else: contexto.append(Image.open(f).convert('RGB'))
                    
                    contexto.append(pergunta_efetiva)
                    response = model.generate_content(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e:
                    if "429" in str(e): st.error("⚠️ Limite atingido. Aguarde 60s.")
                    else: st.error(f"Erro: {e}")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.rerun()

if st.session_state.historico_pericial:
    pdf_bytes = gerar_pdf_pericial(st.session_state.historico_pericial[-1], datetime.now().strftime("%d/%m/%Y"))
    st.download_button(label="📥 Baixar Laudo PDF", data=pdf_bytes, file_name="Laudo_AuditIA.pdf", mime="application/pdf")

# 7. GUIA MESTRE (PONTO 3 - PRESERVADO)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia"):
    st.markdown("""
    ### 🛡️ Inteligência Forense Profissional
    1. **Forense de Imagem**: Anatomia crítica em IA.
    2. **e-Discovery & PST**: Auditoria de massa de e-mails.
    3. **Engenharia Social**: Desmascara táticas de manipulação.
    4. **Consistência Documental**: Auditoria de metadados.
    5. **Memória Iterativa**: Histórico para follow-up.
    6. **Ponzi & IoCs**: Identificação de pirâmides e IPs maliciosos.
    """)
