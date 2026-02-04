import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração Visual (Interface limpa e intuitiva)
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️", initial_sidebar_state="collapsed")

# 2. Conexão Segura (Usando a chave que você salvou nas Secrets)
try:
    CHAVE_MESTRA = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=CHAVE_MESTRA)
    
    # ESTA É A PARTE QUE DEU CERTO: Perguntar ao Google o que ele liberou para você
    modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    # Selecionamos o primeiro da lista que o Google te deu (ex: gemini-1.5-flash)
    model = genai.GenerativeModel(modelos_disponiveis[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Interface Centralizada
st.title("🛡️ Auditor Shield")
st.markdown("### Analise agora a integridade de qualquer promessa digital")

tab1, tab2 = st.tabs(["📝 Texto ou Link", "📸 Imagem (Print)"])

with tab1:
    user_text = st.text_area("Descreva a situação:", placeholder="Cole links ou textos suspeitos aqui...")

with tab2:
    uploaded_file = st.file_uploader("Envie um print do golpe:", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Imagem carregada", use_container_width=True)

# 4. Ação de Auditoria
if st.button("🚀 INICIAR AUDITORIA"):
    if not user_text and not uploaded_file:
        st.warning("Por favor, insira um texto ou uma imagem.")
    else:
        with st.spinner("🕵️ Investigando..."):
            try:
                comando = "Aja como o Auditor Shield. Analise se isto é golpe ou fraude e dê um veredito direto."
                
                if uploaded_file:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([comando, img])
                else:
                    response = model.generate_content(f"{comando} Conteúdo: {user_text}")
                
                st.subheader("📋 Relatório do Auditor")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")

st.markdown("---")
st.caption("A Vida Que Me Escolheu - Auditoria Digital")
