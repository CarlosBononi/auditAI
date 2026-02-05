import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime, timedelta
import pytz

# Estilo e Semáforo (Cores que você pediu)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white"
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 1px solid #4a4a4a; font-size: 18px; text-align: center;">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; }
    </style>
    """, unsafe_allow_html=True)

# Conexão
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except:
    st.error("Erro de conexão."); st.stop()

# Logo Grande à Esquerda
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=480)
except:
    st.title("👁️ AuditIA")

# Interface
uploaded_file = st.file_uploader("📂 Upload de Provas (Print ou PDF):", type=["jpg", "png", "jpeg", "pdf"])
user_input = st.text_area("📝 Contexto da Auditoria:", placeholder="O que deseja analisar?", height=120)

def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=12)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Insira evidências.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
        with st.spinner("Analisando..."):
            try:
                instrucao = f"Aja como o AuditIA. Hoje é {data_br}. Classifique como: FRAUDE CONFIRMADA, POSSÍVEL FRAUDE, ATENÇÃO ou SEGURO."
                conteudo = [instrucao]
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                    else:
                        conteudo.append(Image.open(uploaded_file).convert('RGB'))
                if user_input: conteudo.append(user_input)
                
                response = model.generate_content(conteudo)
                resultado = response.text
                st.markdown(aplicar_cor_veredito(resultado), unsafe_allow_html=True)
                pdf_bytes = gerar_pdf_saida(resultado, data_br)
                st.download_button(label="📥 Baixar Laudo PDF", data=pdf_bytes, file_name=f"Laudo_{datetime.now(tz_br).strftime('%d%m%Y')}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Aguarde um instante e tente novamente (Limite de cota): {e}")

# Manual Master
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia"):
    st.markdown("""
    O **AuditIA** protege seu patrimônio analisando:
    * **Prints**: Detecta comprovantes falsos e manipulação emocional.
    * **PDFs**: Verifica boletos e contratos buscando por fraudes em CNPJs.
    * **Veredito**: Use o **Semáforo** (🔴 Vermelho, 🟠 Laranja, 🟡 Amarelo, 🟢 Verde) para decidir seu próximo passo.
    """)
