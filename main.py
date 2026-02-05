import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime
import pytz

# 1. ESTILO E SEMÁFORO PERICIAL CALIBRADO
st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    # Lógica rigorosa para evitar alarmes falsos
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper and "RISCO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white" # AZUL para informações e suporte
    
    return f'<div style="background-color: {cor}; padding: 30px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; font-size: 18px; text-align: left; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; border: none; font-size: 18px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transform: scale(1.01); transition: 0.2s; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA (Lógica ListModels Profissional)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except:
    st.error("Erro técnico na API. Verifique o faturamento no Google Cloud."); st.stop()

# 3. CABEÇALHO (Logo Grande à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 4. INTERFACE DE TRABALHO
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints ou Documentos PDF):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Contextualização da Auditoria:", placeholder="Descreva o caso ou pergunte ao perito especificamente...", height=150)

# FUNÇÃO GERADORA DE LAUDO PDF
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TECNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data da Analise: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. EXECUÇÃO DA AUDITORIA
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça evidências para análise.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
        
        with st.spinner("🕵️ O AuditIA está realizando a perícia digital..."):
            try:
                instrucao = f"""
                Aja como o AuditIA, a inteligência pericial mais avançada em crimes digitais.
                Data e Hora Local: {data_br}. Analise profundamente prints, PDFs e textos. 
                Identifique padrões de fraude, engenharia social, pirâmides e inconsistências em documentos.
                Ao final, classifique obrigatoriamente como: FRAUDE CONFIRMADA, POSSÍVEL FRAUDE, ATENÇÃO ou SEGURO.
                Se o texto for informativo, responda de forma neutra.
                """
                
                conteudo = [instrucao]
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                    else:
                        conteudo.append(Image.open(uploaded_file).convert('RGB'))
                if user_input: conteudo.append(user_input)
                
                response = model.generate_content(conteudo)
                resultado = response.text
                
                st.subheader("📋 Relatório Pericial")
                st.markdown(aplicar_cor_veredito(resultado), unsafe_allow_html=True)
                
                pdf_bytes = gerar_pdf_saida(resultado, data_br)
                st.download_button(label="📥 Baixar Laudo Completo em PDF", data=pdf_bytes, file_name=f"Laudo_AuditIA_{datetime.now(tz_br).strftime('%d%m%Y')}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Erro na análise: {e}")

# 6. GUIA MESTRE AUDITIA (ROBUSTO E PROFISSIONAL)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital"):
    st.markdown("""
    ### 🛡️ Sua Inteligência Pericial Avançada
    O **AuditIA** opera como um escudo implacável para desmascarar ameaças digitais, protegendo seu patrimônio em tempo real.
    
    **Capacidades Periciais do Robô:**
    1.  **Análise de Engenharia Social**: Identificação de táticas de manipulação psicológica e phishing em chats e e-mails.
    2.  **Detecção de Pirâmides Financeiras**: Exame de promessas de lucros irreais e esquemas Ponzi camuflados.
    3.  **Investigação de Fraudes Financeiras**: Análise de boletos, chaves PIX suspeitas e links de pagamento fraudulentos.
    4.  **Auditoria de Documentos (PDF)**: Verificação de idoneidade de CNPJs, termos contratuais e inconsistências em documentos digitais.
    5.  **Extração de Indicadores de Risco**: Identificação técnica de URLs e domínios maliciosos.

    ### 🚦 O Significado das Cores:
    * 🔴 **FRAUDE CONFIRMADA**: Risco crítico e padrão de crime identificado.
    * 🟠 **POSSÍVEL FRAUDE**: Alto índice de inconsistência e perigo latente.
    * 🟡 **ATENÇÃO**: Elementos suspeitos que exigem investigação humana cautelosa.
    * 🟢 **SEGURO**: Estrutura analisada segue padrões de conformidade conhecidos.
    * 🔵 **AZUL (NEUTRO)**: Orientações preventivas e respostas informativas.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Inteligência Pericial | Vargem Grande do Sul - SP")
