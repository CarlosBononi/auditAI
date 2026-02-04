import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Estilo (Removemos a barra lateral para ficar mais limpo)
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️", initial_sidebar_state="collapsed")

# 2. Conexão com a Chave Embutida
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Selecionamos o modelo Flash que você ativou no Google Cloud
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Erro de configuração nas Secrets. Verifique sua API Key.")
    st.stop()

# 3. Interface Amigável
st.title("🛡️ Auditor Shield")
st.markdown("### Analise agora a integridade de qualquer promessa digital")
st.write("Você pode colar um texto/link ou enviar uma imagem (print) do que achou suspeito.")

# Abas para diferentes tipos de entrada
tab1, tab2 = st.tabs(["📝 Texto ou Link", "📸 Imagem (Print)"])

with tab1:
    user_text = st.text_area("Descreva a situação ou cole o link:", placeholder="Ex: Recebi uma proposta de lucro de 5% ao dia...")

with tab2:
    uploaded_file = st.file_uploader("Envie uma captura de tela (PNG, JPG):", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Imagem carregada", use_container_width=True)

# 4. Processamento da Auditoria
if st.button("🚀 INICIAR AUDITORIA"):
    with st.spinner("O Auditor Shield está investigando..."):
        try:
            prompt = "Aja como o Auditor Shield. Analise se este conteúdo possui indícios de golpe, fraude ou promessa irreal. Seja direto e dê um veredito técnico."
            
            if uploaded_file:
                # O robô 'olha' para a imagem
                img = Image.open(uploaded_file)
                response = model.generate_content([prompt, img])
            elif user_text:
                response = model.generate_content(f"{prompt} Conteúdo: {user_text}")
            else:
                st.warning("Por favor, insira um texto ou carregue uma imagem.")
                st.stop()
                
            st.subheader("📋 Relatório de Auditoria")
            st.info(response.text)
            
        except Exception as e:
            st.error(f"Ocorreu um erro no processamento: {e}")

st.markdown("---")
st.caption("Ferramenta desenvolvida para suporte à decisão. Não substitui assessoria jurídica oficial.")
