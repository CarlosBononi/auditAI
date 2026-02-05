import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime
import pytz

# 1. IDENTIDADE VISUAL E SEMÁFORO DE ALTA PRECISÃO
st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    # A lógica agora é baseada estritamente no início da resposta para evitar falsos positivos
    if texto_upper.startswith("CLASSIFICAÇÃO: FRAUDE CONFIRMADA"):
        cor, font = "#ff4b4b", "white" # VERMELHO (Risco Crítico)
    elif texto_upper.startswith("CLASSIFICAÇÃO: POSSÍVEL FRAUDE"):
        cor, font = "#ffa500", "white" # LARANJA (Risco Alto)
    elif texto_upper.startswith("CLASSIFICAÇÃO: ATENÇÃO"):
        cor, font = "#f1c40f", "black" # AMARELO (Risco Médio)
    elif texto_upper.startswith("CLASSIFICAÇÃO: SEGURO"):
        cor, font = "#2ecc71", "white" # VERDE (Conforme)
    else:
        cor, font = "#3498db", "white" # AZUL (Informativo/Institucional)
    
    return f'<div style="background-color: {cor}; padding: 30px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; font-size: 18px; text-align: left; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; border: none; font-size: 18px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transition: 0.2s; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except:
    st.error("Erro na API. Verifique o faturamento no Google Cloud."); st.stop()

# 3. CABEÇALHO (Logo Grande à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 4. ÁREA DE PERÍCIA
uploaded_file = st.file_uploader("📂 Envie evidências para análise (Prints ou PDFs):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Descreva o caso ou realize uma pergunta técnica:", placeholder="Ex: Analise este comprovante de PIX ou descreva suas capacidades...", height=150)

# FUNÇÃO LAUDO PDF
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TECNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data da Perícia: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. EXECUÇÃO
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, insira o material para perícia.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
        with st.spinner("🕵️ AuditIA realizando varredura pericial..."):
            try:
                instrucao = f"""
                Aja como o AuditIA. Hoje é {data_br}.
                DIRETRIZ DE CLASSIFICAÇÃO:
                1. Se o usuário enviar uma evidência de crime/fraude, você DEVE iniciar com 'CLASSIFICAÇÃO: [TIPO]'.
                2. Se o usuário fizer perguntas informativas sobre você, suas funções ou segurança digital geral, responda de forma técnica e elegante SEM usar os prefixos de classificação no início.
                Seu objetivo é ser um perito sério, eficaz e preciso.
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
                
                st.subheader("📋 Resultado da Auditoria")
                st.markdown(aplicar_cor_veredito(resultado), unsafe_allow_html=True)
                
                pdf_bytes = gerar_pdf_saida(resultado, data_br)
                st.download_button(label="📥 Baixar Laudo Completo em PDF", data=pdf_bytes, file_name=f"Laudo_AuditIA_{datetime.now(tz_br).strftime('%d%m%Y')}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Erro na análise: {e}")

# 6. GUIA MESTRE AUDITIA (A VERSÃO ELITE ROBUSTA)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ Inteligência Forense de Última Geração
    O **AuditIA** é uma plataforma de perícia digital projetada para identificar e neutralizar ameaças complexas através de múltiplos vetores de análise.
    
    **Capacidades Técnicas Avançadas:**
    1.  **Análise Multifacetada de Documentos**: Scrutínio profundo de capturas de tela (WhatsApp/Instagram), arquivos PDF e blocos de texto, buscando anomalias estruturais e visuais.
    2.  **Detecção de Padrões de Fraude Financeira**: Identificação de esquemas de lavagem, comprovantes de PIX alterados e inconsistências em dados bancários cruzados com termos legais.
    3.  **Identificação de Engenharia Social (Forense Comportamental)**: Desconstrução de roteiros de manipulação psicológica, phishing, spoofing e pretexting.
    4.  **Reconhecimento de Esquemas Ponzi e Pirâmides**: Avaliação técnica de promessas de rendimento e estruturas de remuneração insustentáveis.
    5.  **Verificação de Integridade Documental**: Análise de metadados, fontes e selos de segurança para apontar falsificações em recibos e contratos.
    6.  **Extração de Indicadores de Compromisso (IoCs)**: Mapeamento de URLs maliciosas, domínios falsificados e e-mails associados a redes criminosas.

    ### 🚦 Semáforo de Risco Pericial:
    * 🔴 **FRAUDE CONFIRMADA**: Evidências irrefutáveis de atividade maliciosa detectadas.
    * 🟠 **POSSÍVEL FRAUDE**: Fortes indícios de irregularidade que exigem validação humana imediata.
    * 🟡 **ATENÇÃO**: Elementos suspeitos ou pontos fracos em processos que merecem investigação.
    * 🟢 **SEGURO**: Conformidade verificada nos parâmetros analisados.
    * 🔵 **AZUL (NEUTRO)**: Suporte consultivo, respostas técnicas e orientações preventivas.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Inteligência Pericial | Vargem Grande do Sul - SP")
