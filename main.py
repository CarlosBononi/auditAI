import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io

# 1. Estilo AuditIA (Layout Branco e Cinza Pericial)
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

# 2. Conexão Segura (Lógica de listagem para evitar erro 404)
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

# 4. Upload Habilitado para Imagens e PDF
uploaded_file = st.file_uploader(
    "📸 Envie um print ou documento PDF:", 
    type=["jpg", "png", "jpeg", "pdf"] # ADICIONADO PDF AQUI
)

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        st.success(f"📄 Arquivo PDF detectado: {uploaded_file.name}")
    else:
        st.image(uploaded_file, caption="Evidência carregada", use_container_width=True)

user_input = st.text_area("📝 Descreva o caso:", placeholder="Ex: Analise este contrato/print...", height=120)

# Função para Gerar o PDF de Saída (Relatório)
def gerar_pdf_saida(texto):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio de Auditoria - AuditIA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    # Limpeza de caracteres para evitar erro no PDF
    texto_limpo = texto.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 10, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. Execução da Auditoria
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça um arquivo ou texto.")
    else:
        with st.spinner("🕵️ AuditIA analisando evidências..."):
            try:
                instrucao = "Aja como o AuditIA. Analise o arquivo (PDF ou Imagem) e o texto fornecido. De um veredito direto sobre riscos de fraude."
                
                conteudo_para_ia = [instrucao]
                
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        # O Gemini 1.5 Flash processa bytes de PDF diretamente
                        pdf_data = uploaded_file.read()
                        conteudo_para_ia.append({"mime_type": "application/pdf", "data": pdf_data})
                    else:
                        img = Image.open(uploaded_file).convert('RGB')
                        conteudo_para_ia.append(img)
                
                if user_input:
                    conteudo_para_ia.append(user_input)
                
                response = model.generate_content(conteudo_para_ia)
                resultado = response.text
                
                st.subheader("📋 Relatório AuditIA")
                st.info(resultado)
                
                # Botão para baixar o relatório gerado em PDF
                pdf_bytes = gerar_pdf_saida(resultado)
                st.download_button(
                    label="📥 Baixar Veredito em PDF",
                    data=pdf_bytes,
                    file_name="relatorio_auditIA.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro na análise: {e}")

st.markdown("---")
st.caption("AuditIA - Tecnologia e Segurança Digital")
