import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io

# Configuração de Estilo AuditIA
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
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; }
    </style>
    """, unsafe_allow_html=True)

# Conexão
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# Logo Grande à Esquerda
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=450)
except:
    st.title("👁️ AuditIA")

st.markdown("### Auditoria de Integridade Digital")

# Interface de Trabalho (Corrigida para Mobile)
uploaded_file = st.file_uploader("📸 Envie um print do golpe:", type=["jpg", "png", "jpeg"])

if uploaded_file:
    # Mostra a imagem e libera a memória do navegador imediatamente
    st.image(uploaded_file, caption="Evidência carregada", use_container_width=True)

user_input = st.text_area("📝 Descreva o caso:", placeholder="Ex: Analise este print...", height=120)

# Função PDF com tratamento de caracteres brasileiros
def gerar_pdf(texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio AuditIA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    # Remove emojis e caracteres que o PDF não entende
    texto_limpo = texto.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 10, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça imagem ou texto.")
    else:
        with st.spinner("🕵️ Auditando..."):
            try:
                comando = "Aja como o AuditIA. Analise e de um veredito direto."
                if uploaded_file:
                    # Converte para RGB para garantir que o Gemini leia qualquer formato de celular
                    img = Image.open(uploaded_file).convert('RGB')
                    response = model.generate_content([comando, img, user_input] if user_input else [comando, img])
                else:
                    response = model.generate_content(f"{comando} Conteudo: {user_input}")
                
                resultado = response.text
                st.subheader("📋 Relatório AuditIA")
                st.info(resultado)
                
                # O BOTÃO DE PDF SÓ APARECE APÓS A ANÁLISE
                pdf_bytes = gerar_pdf(resultado)
                st.download_button(
                    label="📥 Baixar Relatório em PDF",
                    data=pdf_bytes,
                    file_name="auditoria_auditIA.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro: {e}")
