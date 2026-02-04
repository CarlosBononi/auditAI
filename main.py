import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime # Importação para pegar a data atual

# 1. Estilo AuditIA (Fundo Branco e Cinza Pericial)
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

# 2. Conexão Segura
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
uploaded_file = st.file_uploader(
    "📸 Envie um print ou documento PDF:", 
    type=["jpg", "png", "jpeg", "pdf"]
)

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        st.success(f"📄 Arquivo PDF detectado: {uploaded_file.name}")
    else:
        st.image(uploaded_file, caption="Evidência carregada", use_container_width=True)

user_input = st.text_area("📝 Descreva o caso:", placeholder="Ex: Analise este documento...", height=120)

# Função para Gerar o Relatório PDF de Saída
def gerar_pdf_saida(texto, data_atual):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio de Auditoria - AuditIA", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Data da Analise: {data_atual}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    texto_limpo = texto.encode('ascii', 'ignore').decode('ascii')
    pdf.multi_cell(0, 10, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. Execução da Auditoria com Data Atualizada
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça um arquivo ou texto.")
    else:
        # Pega a data e hora atual do sistema
        data_agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        with st.spinner("🕵️ AuditIA analisando evidências em tempo real..."):
            try:
                # O PULO DO GATO: Inserimos a data atual na instrução para a IA
                instrucao = f"""
                Aja como o AuditIA, especialista em segurança digital e perito em fraudes.
                INFORMAÇÃO CRÍTICA DE CONTEXTO: Hoje é dia {data_agora}. 
                Use esta data para validar prazos, vencimentos de boletos e atualidade das informações enviadas.
                Analise o arquivo e/ou texto e dê um veredito direto sobre riscos de fraude.
                """
                
                conteudo_para_ia = [instrucao]
                
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
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
                
                # Botão para baixar o relatório com a data correta no documento
                pdf_bytes = gerar_pdf_saida(resultado, data_agora)
                st.download_button(
                    label="📥 Baixar Veredito em PDF",
                    data=pdf_bytes,
                    file_name=f"auditoria_{datetime.now().strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Erro na análise: {e}")

st.markdown("---")
st.caption(f"AuditIA - Atualizado em {datetime.now().strftime('%Y')}")
