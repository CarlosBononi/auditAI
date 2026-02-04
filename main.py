import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime, timedelta
import pytz

# 1. ESTILO E SEMÁFORO
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper: cor = "#ff4b4b"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor = "#ffa500"
    elif "ATENÇÃO" in texto_upper: cor = "#f1c40f"; font = "black"
    elif "SEGURO" in texto_upper: cor = "#2ecc71"
    else: cor = "#3498db"; font = "white"
    
    font = "white" if cor != "#f1c40f" else "black"
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 1px solid #4a4a4a; font-size: 18px;">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; border: none; font-size: 18px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; box-shadow: 0px 0px 15px rgba(89, 234, 99, 0.5); }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (Lógica ListModels para evitar 404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error("Erro técnico na API. Verifique o faturamento no Google Cloud."); st.stop()

# 3. CABEÇALHO (Logo à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

# 4. INTERFACE
uploaded_file = st.file_uploader("📸 Suba o Print do Golpe ou Contrato (PDF):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Descreva detalhes ou cole links suspeitos:", placeholder="O que você deseja que o perito analise?", height=150)

# FUNÇÃO PDF ROBUSTA
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="RELATORIO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Analise realizada em: {data_f}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. AUDITORIA
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, insira o material para análise.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
        
        with st.spinner("🕵️ O AuditIA está realizando a perícia digital..."):
            try:
                instrucao = f"""
                Aja como o AuditIA, a inteligência pericial mais avançada em crimes digitais.
                Data e Hora Local: {data_br}.
                Seu objetivo é desmascarar fraudes, pirâmides, engenharia social e golpes de pix.
                Ao final, você DEVE classificar obrigatoriamente como: FRAUDE CONFIRMADA, POSSÍVEL FRAUDE, ATENÇÃO ou SEGURO.
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
                
                st.subheader("📋 Veredito Pericial")
                st.markdown(aplicar_cor_veredito(resultado), unsafe_allow_html=True)
                
                pdf_bytes = gerar_pdf_saida(resultado, data_br)
                st.download_button(label="📥 Baixar Relatório Pericial em PDF", data=pdf_bytes, file_name=f"Laudo_AuditIA_{datetime.now(tz_br).strftime('%d%m%Y')}.pdf", mime="application/pdf")
            except Exception as e:
                if "429" in str(e):
                    st.error("Limite de requisições atingido. Ative o faturamento no Google Cloud para uso ilimitado.")
                else:
                    st.error(f"Erro: {e}")

# 6. MANUAL DE UTILIZAÇÃO MASTER
st.markdown("---")
with st.expander("🎓 MANUAL MASTER AUDITIA - Como realizar perícias de alto nível"):
    st.markdown("""
    ### 🛡️ O que o AuditIA realmente analisa:
    Diferente de uma IA comum, o **AuditIA** foi treinado para identificar as 'impressões digitais' de criminosos virtuais.
    
    * **Análise de Metadados Visuais**: Ao enviar um print, o robô analisa inconsistências gráficas, fontes erradas em comprovantes de PIX e elementos de 'pressão psicológica' (senso de urgência falso).
    * **Verificação de Documentos Periciais (PDF)**: O AuditIA disseca contratos, termos de uso de plataformas e boletos. Ele busca por erros de ortografia (comuns em golpes), CNPJs baixados ou links de pagamento que levam a gateways suspeitos.
    * **Engenharia Social**: Se você colar uma conversa, o robô avalia o roteiro do golpista (abordagem, ganho fácil, solicitação de código ou depósito antecipado).
    
    ### 🚀 Como extrair o máximo do robô:
    1.  **Contextualize**: Sempre escreva onde encontrou o material (Ex: 'Recebi este link por SMS de um número desconhecido').
    2.  **Combine Evidências**: Envie o print da promessa de lucro e cole o link do site abaixo. O robô cruzará as informações.
    3.  **Perguntas Diretas**: Você pode perguntar: *"Este rendimento de 3% ao dia é sustentável?"* ou *"Este comprovante de transferência tem indícios de edição?"*.
    
    ### 🚦 Entendendo o Semáforo de Risco:
    * 🔴 **FRAUDE CONFIRMADA**: Padrão de crime identificado. Não clique em links e bloqueie o contato imediatamente.
    * 🟠 **POSSÍVEL FRAUDE**: Alto risco. Os dados sugerem uma estrutura de golpe camuflada.
    * 🟡 **ATENÇÃO**: Há furos na história ou inconsistências leves que exigem cautela extra.
    * 🟢 **SEGURO**: A estrutura analisada condiz com padrões éticos e legais conhecidos.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Inteligência Pericial | Vargem Grande do Sul - SP")
