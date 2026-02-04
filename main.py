import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime
import pytz # Para o horário de Brasília exato

# 1. Configuração de Página e Estilo (Branco e Cinza)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    cor, font_cor = "#3498db", "white" # Padrão Azul (Neutro)
    if any(x in texto_upper for x in ["FRAUDE CONFIRMADA", "GOLPE CONFIRMADO"]): cor = "#ff4b4b"
    elif any(x in texto_upper for x in ["POSSÍVEL FRAUDE", "PROVÁVEL GOLPE"]): cor = "#ffa500"
    elif any(x in texto_upper for x in ["ATENÇÃO", "INDICAÇÕES SUSPEITAS"]): cor = "#f1c40f"; font_cor = "black"
    elif any(x in texto_upper for x in ["SEGURO", "TUDO OK"]): cor = "#2ecc71"
    
    return f'<div style="background-color: {cor}; padding: 20px; border-radius: 10px; color: {font_cor}; font-weight: bold; border: 1px solid #4a4a4a;">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão Segura e Listagem de Modelos
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}"); st.stop()

# 3. Cabeçalho (Logo Grande à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=450)
except:
    st.title("👁️ AuditIA")

st.markdown("### Auditoria de Integridade Digital")

# 4. Interface de Trabalho (Imagens e PDF)
uploaded_file = st.file_uploader("📸 Envie evidências (Print ou PDF):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Descreva o caso ou cole o link:", placeholder="Ex: Analise este contrato/print e me diga se há riscos...", height=120)

# Função para Gerar PDF de Saída
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio de Auditoria - AuditIA", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Data da Analise: {data_f}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. Execução
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça algum conteúdo.")
    else:
        # Fuso horário de Brasília exato
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
        
        with st.spinner("🕵️ O AuditIA está rastreando padrões..."):
            try:
                instrucao = f"Aja como o AuditIA. Hoje é {data_br}. No início do veredito, use obrigatoriamente um destes termos: FRAUDE CONFIRMADA, POSSÍVEL FRAUDE, ATENÇÃO, SEGURO ou NEUTRO."
                conteudo = [instrucao]
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                    else:
                        conteudo.append(Image.open(uploaded_file).convert('RGB'))
                if user_input: conteudo.append(user_input)
                
                response = model.generate_content(conteudo)
                resultado = response.text
                
                st.subheader("📋 Relatório AuditIA")
                st.markdown(aplicar_cor_veredito(resultado), unsafe_allow_html=True)
                
                # Download PDF
                pdf_bytes = gerar_pdf_saida(resultado, data_br)
                st.download_button(label="📥 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"auditIA_{datetime.now(tz_br).strftime('%d%m%Y')}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Erro: {e}")

# 6. Manual Robustecido de Utilização
st.markdown("---")
with st.expander("💡 MANUAL DE UTILIZAÇÃO ROBUSTO - Como dominar o AuditIA"):
    st.markdown("""
    O **AuditIA** é uma inteligência pericial multimodal. Para obter diagnósticos 100% precisos, siga estas diretrizes:
    
    * **Análise de Prints (WhatsApp/Instagram)**: Ao enviar um print, não apenas suba o arquivo. Use o campo de texto para perguntar: *"Este tom de linguagem condiz com uma empresa real ou parece engenharia social?"*.
    * **Verificação de Documentos (PDF)**: O robô pode ler contratos e boletos. Peça para ele: *"Verifique se o CNPJ citado neste PDF é válido e se há cláusulas abusivas ou suspeitas"*.
    * **Rastreamento de Dados Bancários**: Se houver uma chave PIX ou conta na imagem, o AuditIA analisa a estrutura do dado para identificar se pertence a contas "laranjas" comumente usadas em golpes.
    * **Validação de Prazos**: O AuditIA sabe a data de hoje. Use isso para verificar se uma oferta com "contagem regressiva" é uma pressão psicológica falsa.
    * **O Semáforo de Risco**: 
        * 🔴 **FRAUDE**: Pare imediatamente qualquer transação.
        * 🟠 **POSSÍVEL FRAUDE**: Alto índice de inconsistência.
        * 🟡 **ATENÇÃO**: Há elementos suspeitos que precisam de mais investigação.
        * 🟢 **SEGURO**: Os dados seguem padrões de integridade digital.
    """)

st.caption(f"AuditIA - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
