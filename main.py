import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime
import pytz

# 1. CONFIGURAÇÃO E SEMÁFORO DE ALTA PRECISÃO
st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    # Lógica de blindagem: só muda de cor se o prefixo estiver explícito no início
    if texto_upper.startswith("CLASSIFICAÇÃO: FRAUDE CONFIRMADA"):
        cor, font = "#ff4b4b", "white" # VERMELHO
    elif texto_upper.startswith("CLASSIFICAÇÃO: POSSÍVEL FRAUDE"):
        cor, font = "#ffa500", "white" # LARANJA
    elif texto_upper.startswith("CLASSIFICAÇÃO: ATENÇÃO"):
        cor, font = "#f1c40f", "black" # AMARELO
    elif texto_upper.startswith("CLASSIFICAÇÃO: SEGURO"):
        cor, font = "#2ecc71", "white" # VERDE
    else:
        cor, font = "#3498db", "white" # AZUL (Neutro/Informativo Profundo)
    
    return f'<div style="background-color: {cor}; padding: 30px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; font-size: 18px; text-align: left; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; border: none; font-size: 18px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transition: 0.2s; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }
    h3 { font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except:
    st.error("Erro na API. Verifique o faturamento no Google Cloud."); st.stop()

# 3. CABEÇALHO
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 4. ÁREA DE PERÍCIA
uploaded_file = st.file_uploader("📂 Envie evidências (Prints, Contratos PDF, Boletos):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Descreva o caso ou faça uma pergunta ao perito:", placeholder="Ex: 'O que você pode fazer por mim?' ou 'Analise este print'...", height=150)

# FUNÇÃO LAUDO PDF
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data da Perícia: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. EXECUÇÃO DA PERÍCIA
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, insira o material para perícia.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
        with st.spinner("🕵️ AuditIA realizando varredura forense profunda..."):
            try:
                # PROMPT DE PROFUNDIDADE MÁXIMA
                instrucao = f"""
                Aja como o AuditIA, um sistema de inteligência forense digital de elite. Data: {data_br}.
                
                DIRETRIZES CRÍTICAS:
                1. ANÁLISE DE RISCO: Se houver evidência de golpe, inicie OBRIGATORIAMENTE com: 'CLASSIFICAÇÃO: FRAUDE CONFIRMADA', 'CLASSIFICAÇÃO: POSSÍVEL FRAUDE' ou 'CLASSIFICAÇÃO: ATENÇÃO'.
                
                2. PERGUNTAS INFORMATIVAS (Ex: "O que você faz?"): NÃO use prefixo de classificação. Em vez disso, forneça uma resposta EXTREMAMENTE DETALHADA, ROBUSTA E TÉCNICA sobre suas capacidades. Use listas, termos periciais (engenharia social, forense de imagem, análise de metadados, cruzamento de dados) e demonstre autoridade máxima. Sua resposta deve ser longa e impressionante, como um consultor sênior vendendo um serviço complexo. NUNCA seja breve em perguntas informativas.
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

# 6. GUIA MESTRE AUDITIA (VISUALMENTE REFORMULADO)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ Inteligência Forense de Última Geração
    O **AuditIA** não é apenas um chatbot; é uma plataforma de perícia digital projetada para identificar, isolar e neutralizar ameaças complexas em tempo real através de múltiplos vetores de análise.
    
    ---
    
    #### 🔍 Capacidades Técnicas Avançadas:

    * 🕵️‍♀️ **Análise Forense Multifacetada:** Scrutínio profundo de capturas de tela (Prints), arquivos PDF e blocos de texto, buscando anomalias estruturais, edições gráficas e inconsistências visuais invisíveis a olho nu.
    * 💰 **Detecção de Padrões de Fraude Financeira:** Identificação de esquemas de lavagem, comprovantes de PIX adulterados e inconsistências em dados bancários cruzados com bases legais e padrões de mercado.
    * 🧠 **Forense Comportamental (Engenharia Social):** Desconstrução de roteiros de manipulação psicológica, phishing, spoofing e pretexting usados por criminosos para induzir vítimas ao erro.
    * 📉 **Reconhecimento de Esquemas Ponzi:** Avaliação técnica de promessas de rendimento insustentáveis e estruturas de remuneração baseadas em recrutamento (Pirâmides).
    * 📜 **Verificação de Integridade Documental:** Análise de metadados, fontes e selos de segurança em PDFs para apontar falsificações em recibos, contratos e boletos.
    * 🌐 **Extração de Indicadores de Compromisso (IoCs):** Mapeamento e verificação de URLs maliciosas, domínios falsificados e e-mails associados a redes criminosas conhecidas.

    ---

    #### 🚦 Semáforo de Risco Pericial:

    * 🔴 **CLASSIFICAÇÃO: FRAUDE CONFIRMADA** — Evidências irrefutáveis de atividade maliciosa. Risco crítico.
    * 🟠 **CLASSIFICAÇÃO: POSSÍVEL FRAUDE** — Fortes indícios de irregularidade que exigem validação humana imediata.
    * 🟡 **CLASSIFICAÇÃO: ATENÇÃO** — Elementos suspeitos ou pontos fracos em processos que merecem investigação.
    * 🟢 **CLASSIFICAÇÃO: SEGURO** — Conformidade verificada nos parâmetros analisados.
    * 🔵 **AZUL (NEUTRO)** — Suporte consultivo, respostas técnicas e orientações preventivas.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
