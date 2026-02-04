import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Página e Estilo
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

# 2. Conexão Segura (Secrets)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Mantendo a lógica de listagem que foi nossa única vitória real contra o erro 404
    modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos_disponiveis[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho com Logotipo
# Certifique-se de que o arquivo Logo_AI_1.jpg está na mesma pasta do main.py no GitHub
try:
    logo = Image.open("Logo_AI_1.jpg")
    st.image(logo, use_container_width=True)
except:
    st.title("👁️ AuditIA")
    st.caption("Auditoria Digital Inteligente")

st.markdown("---")

# 4. Interface de Auditoria
st.write("Analise prints, links ou promessas duvidosas agora.")

uploaded_file = st.file_uploader("📸 Envie um print (opcional):", type=["jpg", "png", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, caption="Imagem carregada", use_container_width=True)

user_input = st.text_area(
    "📝 O que você deseja saber?", 
    placeholder="Ex: Analise este print e veja se os dados bancários são suspeitos...",
    height=150
)

if st.button("🚀 INICIAR AUDITORIA"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça uma imagem ou texto.")
    else:
        with st.spinner("🕵️ O AuditIA está investigando..."):
            try:
                comando_base = "Aja como o AuditIA, especialista em segurança digital. Analise o conteúdo e seja direto no veredito."
                
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
                st.error(f"Erro na análise: {e}")

# 5. Seção de Dicas Estratégicas
st.markdown("---")
with st.expander("💡 Dicas de como utilizar o AuditIA"):
    st.markdown("""
    * **Prints do WhatsApp**: Envie capturas de tela de conversas suspeitas para analisar o tom da abordagem.
    * **Dados Bancários**: Ao enviar um print, peça: *'Extraia links ou chaves PIX desta imagem e veja se há riscos'*.
    * **Promessas de Lucro**: Descreva o valor oferecido. O AuditIA cruza dados para identificar promessas irreais.
    * **Análise Combinada**: Sempre que enviar uma imagem, use o campo de texto para perguntar algo específico sobre um detalhe dela.
    """)

st.caption("AuditIA - Tecnologia a serviço da sua segurança digital.")
