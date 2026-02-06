import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime
import pytz

# 1. CONFIGURAÇÃO DE SESSÃO (MEMÓRIA DO AUDITOR)
if "historico" not in st.session_state:
    st.session_state.historico = []

st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white"
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 1px solid #4a4a4a; margin-bottom: 15px;">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except:
    st.error("Erro na API."); st.stop()

# 3. CABEÇALHO (Logo 500px à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 4. ÁREA DE PERÍCIA (MULTIMODAL)
uploaded_file = st.file_uploader("📂 Envie as evidências (Prints, PDFs ou E-mails):", type=["jpg", "png", "jpeg", "pdf", "eml"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

# Interface de Chat (Follow-up)
st.subheader("🕵️ Linha de Investigação")
for mensagem in st.session_state.historico:
    st.markdown(aplicar_cor_veredito(mensagem), unsafe_allow_html=True)

# Caixa de input que não limpa o histórico
user_query = st.text_area("📝 Faça sua pergunta ao perito (ou pergunta de acompanhamento):", placeholder="Ex: 'Este documento foi gerado por IA?' ou 'Analise o rodapé'...", height=100)

col1, col2 = st.columns([1, 1])
with col1:
    btn_auditar = st.button("🚀 EXECUTAR PERÍCIA")
with col2:
    if st.button("🗑️ LIMPAR INVESTIGAÇÃO"):
        st.session_state.historico = []
        st.rerun()

# 5. LÓGICA DE AUDITORIA ITERATIVA
if btn_auditar:
    if not user_query and not uploaded_file:
        st.warning("Forneça material.")
    else:
        tz_br = pytz.timezone('America/Sao_Paulo')
        data_br = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
        
        with st.spinner("Analisando..."):
            try:
                instrucao = f"""
                Aja como o AuditIA. Hoje é {data_br}.
                DIRETRIZ: Responda DIRETAMENTE à pergunta técnica do auditor. Evite resumos genéricos.
                Se for a primeira pergunta, inicie com 'ABERTURA'. Se for follow-up, mantenha o contexto.
                Ao final de análises de risco, use 'CLASSIFICAÇÃO: [TIPO]'.
                Termine com 'Resumo do Veredito:'.
                """
                
                conteudo = [instrucao]
                # Adiciona o histórico para a IA ter memória
                for h in st.session_state.historico:
                    conteudo.append(h)
                
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                    else:
                        conteudo.append(Image.open(uploaded_file).convert('RGB'))
                
                conteudo.append(user_query)
                
                response = model.generate_content(conteudo)
                resposta_final = response.text
                
                # Guarda no histórico para a próxima pergunta
                st.session_state.historico.append(f"PERGUNTA: {user_query}\n\nRESPOSTA: {resposta_final}")
                st.rerun() # Atualiza a tela para mostrar a nova mensagem no topo
                
            except Exception as e:
                st.error(f"Erro: {e}")

# 6. MANUAL DE ELITE (ROADMAP INVESTIDOR)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital"):
    st.markdown("""
    ### 🛡️ Sua Inteligência Pericial Avançada
    O **AuditIA** agora suporta **Investigação Iterativa**, permitindo que o auditor faça perguntas de acompanhamento sobre a mesma evidência.
    
    **Módulos de Performance:**
    * 🕵️‍♀️ **Forense de Imagem e Documentos:** Scrutínio de prints e PDFs.
    * 🧠 **Engenharia Social:** Identificação de táticas de manipulação.
    * ✉️ **E-Discovery (Beta):** Análise de grandes volumes de e-mails para auditorias internas.
    """)
