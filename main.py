import streamlit as st
import google.generativeai as genai

# Configuração visual do site
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️")
st.title("🛡️ Auditor Shield")
st.subheader("Seu guia contra golpes e promessas falsas")

# Aqui você cola a sua chave que pegou no Passo 1
api_key = st.sidebar.text_input("Cole sua API Key do Google aqui:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    
    # Instruções que você já criou no Studio AI
    system_prompt = "Você é o Auditor Shield, especialista em identificar golpes..." # O prompt que te dei antes vai aqui
    
    model = genai.GenerativeModel(
        model_name="gemini-pro",
        system_instruction=system_prompt
    )

    # Campo para o usuário colar o que quer analisar
    user_input = st.text_area("O que você deseja auditar hoje? (Cole links, textos ou promessas)")

    if st.button("Iniciar Auditoria"):
        if user_input:
            with st.spinner("Analisando integridade digital..."):
                response = model.generate_content(user_input)
                st.markdown(response.text)
        else:
            st.warning("Por favor, cole alguma informação para análise.")
else:

    st.info("Por favor, insira sua API Key na barra lateral para começar.")
