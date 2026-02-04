import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Layout e Estilo (Fundo Branco e Cinza)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    
    /* Botão Cinza Escuro */
    div.stButton > button:first-child {
        background-color: #4a4a4a;
        color: #ffffff;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        width: 100%;
        height: 3.5em;
    }
    div.stButton > button:first-child:hover {
        background-color: #59ea63;
        color: #000000;
    }
    
    /* Inputs */
    .stTextArea textarea { background-color: #f8f9fa; color: #333333; border: 1px solid #d1d5db; }
    .stFileUploader section { background-color: #f8f9fa; border: 1px dashed #4a4a4a; }

    h3 { color: #4a4a4a !important; margin-top: -20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão Segura
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho: Logo Grande e à Esquerda
try:
    logo = Image.open("Logo_AI_1.png")
    # Usamos colunas para forçar o alinhamento à esquerda
    col_logo, col_espaco = st.columns([2, 1])
    with col_logo:
        st.image(logo, width=500) # Aumentado para 500px conforme seu pedido
except:
    st.title("👁️ AuditIA")

st.markdown("### Auditoria de Integridade Digital")
st.write("Analise prints e mensagens com precisão técnica.")

# 4. Upload Robusto (Resolve o erro de algumas imagens não carregarem)
uploaded_file = st.file_uploader(
    "📸 Envie um print do golpe:", 
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=False
)

if uploaded_file:
    # Mostra a imagem imediatamente
    st.image(uploaded_file, caption="Evidência detectada", use_container_width=True)

user_input = st.text_area(
    "📝 Descreva o caso:", 
    placeholder="Ex: Verifique este print...",
    height=150
)

# 5. Processamento
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, insira um conteúdo.")
    else:
        with st.spinner("🕵️ Processando..."):
            try:
                comando = "Aja como o AuditIA. Analise o conteúdo e dê um veredito direto."
                if uploaded_file:
                    # Abrimos a imagem de forma que o celular não trave
                    img = Image.open(uploaded_file)
                    if user_input:
                        response = model.generate_content([comando, img, user_input])
                    else:
                        response = model.generate_content([comando, img])
                else:
                    response = model.generate_content(f"{comando} Conteúdo: {user_input}")
                
                st.subheader("📋 Relatório AuditIA")
                st.info(response.text)
            except Exception as e:
                st.error(f"Erro: {e}")

st.markdown("---")
st.caption("AuditIA - Tecnologia e Segurança Digital")
