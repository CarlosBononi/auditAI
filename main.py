import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io

# 1. Configuração de Estilo AuditIA
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child {
        background-color: #4a4a4a;
        color: #ffffff;
        border-radius: 8px;
        width: 100%;
        height: 3.5em;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: #000000; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; }
    h3 { color: #4a4a4a !important; margin-top: -20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho (Logo Grande à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=450)
except:
    st.title("👁️ AuditIA")

st.markdown("### Auditoria de Integridade Digital")

# 4. Interface de Trabalho
uploaded_file = st.file_uploader("📸 Envie um print do golpe:", type=["jpg", "png", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, caption="Evidência carregada", use_container_width=True)

user_input = st.text_area("📝 Descreva o caso:", placeholder="Ex: Analise este print...", height=120)

# Função para gerar PDF
def gerar_pdf(texto_auditoria):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatório de Auditoria Digital - AuditIA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=texto_auditoria)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# 5. Execução
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, insira um conteúdo.")
    else:
        with st.spinner("🕵️ Auditando..."):
            try:
                comando = "Aja como o AuditIA. Analise o conteúdo e dê um veredito técnico sobre riscos de fraude."
                if uploaded_file:
                    img = Image.open(uploaded_file).convert('RGB') # Força conversão para evitar erro mobile
                    response = model.generate_content([comando, img, user_input] if user_input else [comando, img])
                else:
                    response = model.generate_content(f"{comando} Conteúdo: {user_input}")
                
                resultado = response.text
                st.subheader("📋 Relatório AuditIA")
                st.info(resultado)
                
                # Opção de Download em PDF
                pdf_bytes = gerar_pdf(resultado)
                st.download_button(
                    label="📥 Baixar Relatório em PDF",
                    data=pdf_bytes,
                    file_name="auditoria_auditIA.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro: {e}")

st.markdown("---")
st.caption("AuditIA - Tecnologia e Segurança Digital")
