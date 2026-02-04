import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Estilo AuditIA (Verde Néon e Preto)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    /* Fundo escuro tecnológico */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Botão Verde Néon */
    div.stButton > button:first-child {
        background-color: #59ea63;
        color: #000000;
        border-radius: 10px;
        border: none;
        font-weight: bold;
        width: 100%;
        height: 3.5em;
        transition: 0.3s;
        font-size: 18px;
    }
    div.stButton > button:first-child:hover {
        background-color: #ffffff;
        color: #59ea63;
        box-shadow: 0 0 15px #59ea63;
    }
    
    /* Caixas de entrada personalizadas */
    .stTextArea textarea { background-color: #1e2129; color: #ffffff; border: 1px solid #59ea63; }
    .stFileUploader section { background-color: #1e2129; border: 1px dashed #59ea63; }
    
    /* Títulos e alertas */
    h1, h2, h3 { color: #59ea63 !important; }
    .stAlert { background-color: #1e2129; border-left: 5px solid #59ea63; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com a API (Lógica de listagem que funciona)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho com o Logotipo (Ajustado para .png)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, use_container_width=True)
except:
    st.title("👁️ AuditIA")
    st.caption("Auditoria Digital Inteligente")

st.markdown("### Bem-vindo à sua Auditoria de Integridade")
st.write("Analise prints e mensagens suspeitas com inteligência pericial.")

# 4. Interface Unificada
uploaded_file = st.file_uploader("📸 Envie um print do golpe (opcional):", type=["jpg", "png", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, caption="Evidência carregada", use_container_width=True)

user_input = st.text_area(
    "📝 O que você deseja auditar?", 
    placeholder="Ex: Analise este print e me diga se há riscos de fraude...",
    height=150
)

if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça uma imagem ou texto para análise.")
    else:
        with st.spinner("🕵️ O AuditIA está rastreando padrões de fraude..."):
            try:
                comando_base = "Aja como o AuditIA, especialista em segurança digital. Analise o conteúdo fornecido e dê um veredito direto sobre riscos de golpe ou fraude."
                
                if uploaded_file and user_input:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([comando_base, img, user_input])
                elif uploaded_file:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([comando_base, img])
                else:
                    response = model.generate_content(f"{comando_base} Conteúdo: {user_input}")
                
                st.subheader("📋 Relatório AuditIA")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Ocorreu um erro na análise: {e}")

# 5. Dicas de Uso
st.markdown("---")
with st.expander("💡 Dicas de como utilizar o AuditIA"):
    st.markdown("""
    * **Análise de Prints**: Envie capturas de tela do WhatsApp ou Instagram para identificar abordagens suspeitas.
    * **Extração de Dados**: Peça para o robô identificar chaves PIX ou links ocultos na imagem.
    * **Cálculo de Promessas**: Descreva rendimentos oferecidos; o robô avalia se a promessa é matematicamente impossível.
    * **Pergunta Contextual**: Use o campo de texto para focar a análise em um detalhe específico da imagem carregada.
    """)

st.caption("AuditIA - Tecnologia e Segurança Digital")
