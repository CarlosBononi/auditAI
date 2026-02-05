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
    # A cor agora é definida pela presença da classificação no corpo do texto
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper:
        cor, font = "#ff4b4b", "white" # VERMELHO
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper:
        cor, font = "#ffa500", "white" # LARANJA
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper:
        cor, font = "#f1c40f", "black" # AMARELO
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper:
        cor, font = "#2ecc71", "white" # VERDE
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
    st.error("Erro na API. Verifique o faturamento."); st.stop()

# 3. CABEÇALHO (Logo 500px à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 4. ÁREA DE PERÍCIA
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints, PDFs, Boletos):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Descreva o caso ou faça uma pergunta técnica:", placeholder="Ex: 'O que você faz?' ou 'Analise este documento'...", height=150)

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
        st.warning("Por favor, forneça evidências.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
        with st.spinner("🕵️ AuditIA realizando varredura pericial..."):
            try:
                instrucao = f"""
                Aja como o AuditIA, inteligência pericial avançada. Hoje é {data_br}.
                
                ESTRUTURA OBRIGATÓRIA DA RESPOSTA:
                1. ABERTURA: Comece sempre com: 'Compreendido. Eu sou o AuditIA, sua inteligência pericial avançada em crimes digitais, operando com a data e hora local de {data_br}.'
                
                2. CLASSIFICAÇÃO: Se for análise de risco, logo após a abertura, insira em linha nova: 'CLASSIFICAÇÃO: [FRAUDE CONFIRMADA, POSSÍVEL FRAUDE, ATENÇÃO ou SEGURO]'.
                
                3. ANÁLISE PROFUNDA: Desenvolva uma explicação técnica, longa e detalhada. Use termos periciais. Se for pergunta informativa, seja EXTREMAMENTE ROBUSTO.
                
                4. FECHAMENTO: Termine sempre com um parágrafo curto iniciado por: 'Resumo do Veredito:' seguido de uma conclusão direta.
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

# 6. GUIA MESTRE AUDITIA (ELITE VISUAL)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ Inteligência Forense de Última Geração
    O **AuditIA** é uma plataforma de perícia digital de elite projetada para desmascarar crimes cibernéticos em tempo real.
    
    ---
    #### 🔍 Especialidades do Robô:
    * 🕵️‍♀️ **Forense de Imagem e Documentos:** Scrutínio de prints e PDFs buscando anomalias visuais e estruturais.
    * 🧠 **Engenharia Social:** Identificação de táticas de manipulação psicológica e phishing.
    * 💰 **Rastreador de Fraudes PIX:** Análise técnica de comprovantes e fluxos de pagamentos suspeitos.
    * 📈 **Análise de Pirâmides:** Avaliação de modelos de negócios e promessas de lucro irreais.
    * 📜 **Integridade Documental:** Verificação de metadados, fontes e selos de segurança em recibos e contratos.

    ---
    #### 🚦 Semáforo de Risco:
    * 🔴 **FRAUDE CONFIRMADA** — Risco crítico detectado.
    * 🟠 **POSSÍVEL FRAUDE** — Indícios fortes de irregularidade.
    * 🟡 **ATENÇÃO** — Elementos que exigem investigação humana.
    * 🟢 **SEGURO** — Conformidade verificada.
    * 🔵 **AZUL (NEUTRO)** — Suporte técnico e consultoria preventiva.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
