import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime
import pytz

# 1. ESTILO E SEMÁFORO PERICIAL DE ALTA PRECISÃO
st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    # A cor agora só muda se o veredito estiver explícito no início ou destaque
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper or texto_upper.startswith("FRAUDE CONFIRMADA"):
        cor, font = "#ff4b4b", "white" # VERMELHO (Risco Crítico)
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper or texto_upper.startswith("POSSÍVEL FRAUDE"):
        cor, font = "#ffa500", "white" # LARANJA (Risco Alto)
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper or texto_upper.startswith("ATENÇÃO"):
        cor, font = "#f1c40f", "black" # AMARELO (Risco Médio)
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper or texto_upper.startswith("SEGURO"):
        cor, font = "#2ecc71", "white" # VERDE (Seguro)
    else:
        cor, font = "#3498db", "white" # AZUL (Informativo/Neutro)
    
    return f'<div style="background-color: {cor}; padding: 30px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; font-size: 18px; text-align: left; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; border: none; font-size: 18px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transform: scale(1.01); transition: 0.2s; }
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

user_input = st.text_area("📝 Descreva o caso ou realize uma pergunta técnica:", placeholder="Ex: Analise este comprovante de PIX ou este contrato suspeito...", height=150)

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
                Aja como o AuditIA. Hoje é {data_br}. Analise profundamente as evidências.
                Para riscos reais, inicie sua resposta OBRIGATORIAMENTE com:
                CLASSIFICAÇÃO: FRAUDE CONFIRMADA, CLASSIFICAÇÃO: POSSÍVEL FRAUDE, CLASSIFICAÇÃO: ATENÇÃO ou CLASSIFICAÇÃO: SEGURO.
                Se for uma pergunta informativa ou explicativa, responda de forma direta e técnica sem usar as classificações de risco no início.
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

# 6. GUIA MESTRE AUDITIA (A VERSÃO ROBUSTA QUE VOCÊ EXIGIU)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ O Poder da Perícia AuditIA
    O **AuditIA** é uma inteligência forense digital projetada para desmascarar crimes cibernéticos em tempo real através de algoritmos avançados.
    
    **Capacidades Técnicas do Robô:**
    1.  **Análise Multifacetada de Documentos**: Processamento profundo de prints (WhatsApp/Instagram), arquivos PDF e blocos de texto em busca de anomalias visuais ou estruturais.
    2.  **Detecção de Padrões de Fraude**: Identificação de esquemas de fraude financeira, roubo de identidade e irregularidades complexas através do cruzamento de dados bancários e termos legais.
    3.  **Identificação de Engenharia Social**: Análise de linguagem e comportamento sugerido para desmascarar tentativas de manipulação psicológica, phishing, spoofing e pretexting.
    4.  **Reconhecimento de Esquemas Ponzi/Pirâmide**: Avaliação de modelos de negócios com promessas de retorno garantido e estruturas de remuneração baseadas em recrutamento.
    5.  **Verificação de Consistência Documental**: Comparação de dados, fontes e metadados para apontar adulterações ou falta de elementos de segurança em documentos digitais.
    6.  **Indicadores de Compromisso (IoCs)**: Identificação técnica de URLs, domínios e e-mails associados a atividades maliciosas.

    ### 🚦 O Significado das Cores (Semáforo de Risco):
    * 🔴 **FRAUDE CONFIRMADA**: Evidências robustas e diretas de atividade criminosa.
    * 🟠 **POSSÍVEL FRAUDE**: Indícios fortes que sugerem fraude, exigindo validação humana.
    * 🟡 **ATENÇÃO**: Elementos suspeitos que merecem investigação, mas sem evidência conclusiva.
    * 🟢 **SEGURO**: Nenhuma anomalia detectada nos parâmetros analisados.
    * 🔵 **AZUL (NEUTRO)**: Respostas informativas e suporte preventivo sem juízo de valor.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
