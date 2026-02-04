import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Página e Estilo Profissional
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️", initial_sidebar_state="collapsed")

# 2. Conexão Segura com a Chave Embutida
try:
    # Busca a chave que você salvou nas 'Secrets' do Streamlit
    CHAVE_MESTRA = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=CHAVE_MESTRA)
    
    # NOME TÉCNICO COMPLETO: Isso evita o erro 404 que apareceu no seu teste
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error("Erro de configuração. Verifique se a chave está nas 'Secrets'.")
    st.stop()

# 3. Interface Intuitiva para o Usuário
st.title("🛡️ Auditor Shield")
st.markdown("### Analise agora a integridade de qualquer promessa digital")
st.write("Envie um texto, link ou uma imagem (print) do que achou suspeito.")

# Abas para organizar a entrada do usuário
tab1, tab2 = st.tabs(["📝 Texto ou Link", "📸 Imagem (Print)"])

with tab1:
    user_text = st.text_area("Descreva a situação:", placeholder="Ex: Recebi uma proposta de lucro de 5% ao dia...")

with tab2:
    uploaded_file = st.file_uploader("Envie um print (PNG, JPG):", type=["jpg", "png", "jpeg"])
    if uploaded_file:
        st.image(uploaded_file, caption="Imagem carregada com sucesso", use_container_width=True)

# 4. Botão de Execução
if st.button("🚀 INICIAR AUDITORIA"):
    if not user_text and not uploaded_file:
        st.warning("Por favor, insira um texto ou envie uma imagem primeiro.")
    else:
        with st.spinner("🕵️ O Auditor Shield está investigando..."):
            try:
                # Instrução de Especialista
                prompt = "Aja como o Auditor Shield. Analise se este conteúdo possui indícios de golpe ou fraude. Seja direto no veredito."
                
                if uploaded_file:
                    # O Gemini analisa a imagem enviada
                    img = Image.open(uploaded_file)
                    response = model.generate_content([prompt, img])
                else:
                    # O Gemini analisa apenas o texto
                    response = model.generate_content(f"{prompt} Conteúdo: {user_text}")
                
                st.subheader("📋 Relatório da Auditoria")
                st.info(response.text)
                st.success("Auditoria concluída com sucesso!")
                
            except Exception as e:
                # Caso o Google mude algo, o erro aparecerá aqui de forma limpa
                st.error(f"Erro na análise: {e}")
                st.info("Dica: Tente novamente em alguns segundos ou verifique se a imagem está nítida.")

st.markdown("---")
st.caption("Ferramenta desenvolvida para suporte à decisão. Não substitui assessoria jurídica oficial.")
