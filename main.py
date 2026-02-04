import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Página
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️", layout="centered")

# 2. Conexão Segura (Recuperando sua chave das Secrets)
try:
    CHAVE_MESTRA = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=CHAVE_MESTRA)
    
    # Lógica vencedora: Listar o que está disponível para sua chave
    modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos_disponiveis[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Interface Unificada e Intuitiva
st.title("🛡️ Auditor Shield")
st.markdown("### Auditoria de Integridade Digital")
st.write("Envie um print, um link ou descreva a situação suspeita abaixo.")

# Upload de Imagem (Opcional)
uploaded_file = st.file_uploader("📸 Envie um print (opcional):", type=["jpg", "png", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, caption="Imagem para análise", use_container_width=True)

# Campo de Texto (Sempre visível para complementar a imagem)
user_input = st.text_area(
    "📝 O que você deseja saber sobre isso?", 
    placeholder="Ex: Analise o print acima e me diga se essa promessa de lucro é real...",
    height=150
)

# 4. Execução da Auditoria Combinada
if st.button("🚀 INICIAR AUDITORIA"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça uma imagem ou um texto para análise.")
    else:
        with st.spinner("🕵️ O Auditor Shield está investigando..."):
            try:
                comando_base = "Aja como o Auditor Shield, especialista em golpes. Analise o conteúdo fornecido (imagem e/ou texto) e dê um veredito direto e técnico."
                
                # Se houver imagem E texto, o Gemini lê os dois juntos
                if uploaded_file and user_input:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([comando_base, img, user_input])
                
                # Se houver apenas imagem
                elif uploaded_file:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([comando_base, img])
                
                # Se houver apenas texto
                else:
                    response = model.generate_content(f"{comando_base} Conteúdo: {user_input}")
                
                st.subheader("📋 Relatório do Auditor")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Erro na análise: {e}")

st.markdown("---")
st.caption("AuditIA Best Bot - Tecnologia e Psicologia Digital")
