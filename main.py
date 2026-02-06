import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. MEMÓRIA DE SESSÃO (INVESTIGAÇÃO ITERATIVA)
if "historico" not in st.session_state:
    st.session_state.historico = []

st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

# 2. SISTEMA DE CORES SEMÂNTICAS
def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper:
        cor, font = "#ff4b4b", "white" # Vermelho
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper:
        cor, font = "#ffa500", "white" # Laranja
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper:
        cor, font = "#f1c40f", "black" # Amarelo
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper:
        cor, font = "#2ecc71", "white" # Verde
    else:
        cor, font = "#3498db", "white" # Azul (Informativo)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        {texto}
    </div>
    '''

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; border: none; font-size: 18px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transform: scale(1.01); }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO SEGURA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except:
    st.error("Erro na API."); st.stop()

# 4. CABEÇALHO (Logo 500px)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 5. INTERFACE DE PERÍCIA
uploaded_file = st.file_uploader("📂 Envie evidências (Prints, PDFs, E-mails .eml):", type=["jpg", "png", "jpeg", "pdf", "eml"])
if uploaded_file and uploaded_file.type != "application/pdf" and not uploaded_file.name.endswith('.eml'):
    st.image(uploaded_file, use_container_width=True)

# Exibição do Histórico de Investigação
st.subheader("🕵️ Linha de Investigação")
for msg in st.session_state.historico:
    st.markdown(aplicar_cor_veredito(msg), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", placeholder="Descreva o caso ou faça perguntas de acompanhamento sobre a evidência...", height=120)

# FUNÇÃO LAUDO PDF
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Emitido em: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 6. EXECUÇÃO
col1, col2 = st.columns([1, 1])
with col1:
    btn_auditar = st.button("🚀 EXECUTAR PERÍCIA")
with col2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico = []
        st.rerun()

if btn_auditar:
    if not user_query and not uploaded_file:
        st.warning("Forneça material para análise.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
        
        with st.spinner("🕵️ AuditIA realizando varredura forense profunda..."):
            try:
                instrucao = f"""
                Aja como o AuditIA, inteligência pericial avançada. Hoje é {data_br}.
                
                ESTRUTURA DA RESPOSTA:
                1. ABERTURA: 'Compreendido. Sou o AuditIA, operando em {data_br}.'
                2. CLASSIFICAÇÃO: Se houver risco, inicie com 'CLASSIFICAÇÃO: [TIPO]'.
                3. ANÁLISE: Responda DIRETAMENTE e com PROFUNDIDADE técnica à pergunta. 
                4. FECHAMENTO: 'Resumo do Veredito: [Conclusão Direta]'.
                """
                
                conteudo = [instrucao]
                # Mantém a memória para follow-up
                for h in st.session_state.historico:
                    conteudo.append(h)
                
                if uploaded_file:
                    if uploaded_file.name.endswith('.eml'):
                        msg = email.message_from_bytes(uploaded_file.read(), policy=policy.default)
                        corpo = msg.get_body(preferencelist=('plain')).get_content()
                        headers = "\n".join([f"{k}: {v}" for k, v in msg.items()])
                        conteudo.append(f"DADOS DO E-MAIL:\nHEADERS:\n{headers}\n\nCORPO:\n{corpo}")
                    elif uploaded_file.type == "application/pdf":
                        conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                    else:
                        conteudo.append(Image.open(uploaded_file).convert('RGB'))
                
                conteudo.append(user_query)
                
                response = model.generate_content(conteudo)
                resultado = response.text
                
                # Adiciona ao histórico e atualiza
                st.session_state.historico.append(resultado)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro: {e}")

# Exibe botão de PDF apenas se houver resultado
if st.session_state.historico:
    tz_br = pytz.timezone('America/Sao_Paulo')
    data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
    pdf_bytes = gerar_pdf_saida(st.session_state.historico[-1], data_br)
    st.download_button(label="📥 Baixar Laudo da Última Consulta (PDF)", data=pdf_bytes, file_name=f"Laudo_AuditIA_{datetime.now(tz_br).strftime('%d%m%Y')}.pdf", mime="application/pdf")

# 7. GUIA MESTRE (VISUAL)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ Inteligência Forense de Última Geração
    O **AuditIA** é uma plataforma multimodal projetada para neutralizar ameaças digitais complexas.
    
    * 🕵️‍♀️ **Forense de Imagem e Documentos:** Scrutínio de prints e PDFs buscando anomalias.
    * 🧠 **Investigação Iterativa:** Faça perguntas de acompanhamento sobre a mesma evidência.
    * ✉️ **Email Forensics:** Auditoria de cabeçalhos RFC822 e rastreamento de IPs.
    * 🚦 **Semáforo de Risco:** Vermelho (Fraude), Laranja (Suspeito), Amarelo (Atenção), Verde (Seguro), Azul (Informativo).
    """)

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
