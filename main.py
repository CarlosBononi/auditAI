import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime
import pytz

# 1. ESTILO E SEMÁFORO INTELIGENTE (CORRIGIDO)
st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    # Lógica refinada para evitar falsos positivos no vermelho
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white" # AZUL para textos neutros ou explicativos
    
    return f'<div style="background-color: {cor}; padding: 30px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; font-size: 18px; text-align: left; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 10px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transition: 0.3s; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (Lógica ListModels)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except:
    st.error("Erro técnico na API."); st.stop()

# 3. CABEÇALHO (Logo à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=480)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 4. INTERFACE
uploaded_file = st.file_uploader("📂 Envie Prints ou Documentos (PDF) para análise:", type=["jpg", "png", "jpeg", "pdf"])
user_input = st.text_area("📝 Descreva o caso ou pergunte ao perito:", placeholder="Ex: Analise este print e me diga se há riscos de fraude...", height=150)

# FUNÇÃO PDF
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TECNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Gerado em: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. EXECUÇÃO
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça o material para perícia.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
        with st.spinner("🕵️ AuditIA realizando varredura pericial..."):
            try:
                # Instrução mestre que força o uso dos termos de classificação
                instrucao = f"Aja como o AuditIA, inteligência pericial avançada. Hoje é {data_br}. Analise profundamente. No início, classifique como: FRAUDE CONFIRMADA, POSSÍVEL FRAUDE, ATENÇÃO ou SEGURO. Se for apenas uma dúvida genérica, responda de forma neutra."
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

# 6. MANUAL DE UTILIZAÇÃO PROFISSIONAL (TURBINADO)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital Avançada"):
    st.markdown("""
    ### 🛡️ O Poder da Perícia AuditIA
    O **AuditIA** é uma ferramenta de inteligência forense digital que opera com foco em desmascarar ameaças em tempo real. 
    
    ### 🚀 O que o robô pode fazer por você:
    * **Análise de Engenharia Social**: Identificação de táticas de manipulação psicológica e phishing em mensagens de texto ou chat.
    * **Detecção de Pirâmides e Investimentos Falsos**: Exame de propostas com promessas de lucros irreais e recrutamento suspeito.
    * **Investigação de Fraudes Financeiras**: Análise técnica de comprovantes de PIX, boletos e links de pagamento suspeitos.
    * **Verificação de Conteúdo e Links**: Auditoria de e-mails, posts em redes sociais e websites maliciosos para identificar roubo de dados.
    * **Extração de Indicadores de Risco**: Identificação de URLs, domínios e e-mails associados a atividades criminosas conhecidas.

    ### 🚦 Entendendo o Semáforo de Risco:
    * 🔴 **FRAUDE CONFIRMADA**: Risco real e imediato. Interrompa qualquer transação.
    * 🟠 **POSSÍVEL FRAUDE**: Alto índice de inconsistência e perigo.
    * 🟡 **ATENÇÃO**: Elementos suspeitos que exigem cautela extra.
    * 🟢 **SEGURO**: A estrutura analisada segue os padrões de conformidade.
    * 🔵 **AZUL (NEUTRO)**: Orientações preventivas e respostas informativas.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
