import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GERENCIAMENTO DE SESSÃO E LIMPEZA DE INPUT
if "historico" not in st.session_state:
    st.session_state.historico = []

def reset_pergunta():
    st.session_state.pergunta_atual = st.session_state.widget_pergunta
    st.session_state.widget_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

# 2. SISTEMA DE CORES E CLASSIFICAÇÃO EXPLÍCITA
def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white" # Azul (Informativo / Neutro)
    
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 20px;">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 10px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Erro na API."); st.stop()

# 4. CABEÇALHO
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 5. INTERFACE DE PERÍCIA
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints, PDFs, E-mails):", type=["jpg", "png", "jpeg", "pdf", "eml"])
if uploaded_file and uploaded_file.type != "application/pdf" and not uploaded_file.name.endswith('.eml'):
    st.image(uploaded_file, use_container_width=True)

# Exibição do Histórico com Pergunta e Horário no Topo
st.subheader("🕵️ Linha de Investigação")
for msg in st.session_state.historico:
    st.markdown(aplicar_cor_veredito(msg), unsafe_allow_html=True)

# Caixa de texto com limpeza automática
user_query = st.text_area("📝 Pergunta ao Perito:", key="widget_pergunta", placeholder="Faça sua pergunta de acompanhamento aqui...", height=100)

# FUNÇÃO LAUDO PDF
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 6. EXECUÇÃO
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=reset_pergunta):
        pergunta_para_ia = st.session_state.get('pergunta_atual', '')
        if not pergunta_para_ia and not uploaded_file:
            st.warning("Forneça material.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Auditando..."):
                try:
                    instrucao = f"""
                    Aja como o AuditIA. Hoje é {agora}.
                    REGRA DE OURO: Responda PRIMEIRO e DIRETAMENTE à pergunta do auditor. Não resuma o documento se não for solicitado.
                    ESTRUTURA:
                    1. TÍTULO: 'PERGUNTA FEITA EM {agora}: "{pergunta_para_ia}"'
                    2. CLASSIFICAÇÃO: Se for neutro, inicie com 'CLASSIFICAÇÃO: INFORMATIVO / NEUTRO'. Se houver risco, use os termos padrão.
                    3. RESPOSTA: Seja profundo, técnico e direto ao ponto.
                    4. FECHAMENTO: 'Resumo do Veredito:'.
                    """
                    conteudo = [instrucao]
                    for h in st.session_state.historico: conteudo.append(h)
                    
                    if uploaded_file:
                        if uploaded_file.name.endswith('.eml'):
                            msg = email.message_from_bytes(uploaded_file.read(), policy=policy.default)
                            corpo = msg.get_body(preferencelist=('plain')).get_content()
                            conteudo.append(f"E-MAIL: {corpo}")
                        elif uploaded_file.type == "application/pdf":
                            conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                        else:
                            conteudo.append(Image.open(uploaded_file).convert('RGB'))
                    
                    conteudo.append(pergunta_para_ia)
                    response = model.generate_content(conteudo)
                    st.session_state.historico.append(response.text)
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

with col2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico = []
        st.rerun()

# Botão de PDF
if st.session_state.historico:
    tz_br = pytz.timezone('America/Sao_Paulo')
    pdf_bytes = gerar_pdf_saida(st.session_state.historico[-1], datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S"))
    st.download_button(label="📥 Baixar Laudo da Última Consulta (PDF)", data=pdf_bytes, file_name="Laudo_AuditIA.pdf", mime="application/pdf")

# 7. GUIA MESTRE
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia"):
    st.markdown("""
    ### 🛡️ Inteligência Forense
    * 🕵️‍♀️ **Forense de Imagem e Documentos:** Scrutínio de prints e PDFs.
    * 🧠 **Investigação Iterativa:** Memória de contexto para follow-up.
    * 🔵 **AZUL (INFORMATIVO/NEUTRO):** Respostas técnicas e orientações preventivas.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
