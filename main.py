import streamlit as st
import google.generativeai as genai

# Configuração visual
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️")
st.title("🛡️ Auditor Shield")

# Chave que você me passou
api_key = st.sidebar.text_input("Cole sua API Key aqui:", type="password")

if api_key:
    try:
        # Configuração da API
        genai.configure(api_key=api_key)
        
        # AJUSTE TÉCNICO: Forçamos o uso do modelo 1.5-flash com o nome completo
        # que o projeto AuditIA exige para conexões externas
        model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")

        user_input = st.text_area("O que deseja auditar?")

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("O Auditor está trabalhando..."):
                    # Instrução embutida para evitar erro de configuração de sistema
                    prompt = f"Aja como o Auditor Shield, especialista em identificar golpes. Analise isto e dê um veredito técnico: {user_input}"
                    
                    response = model.generate_content(prompt)
                    st.success("Auditoria Concluída!")
                    st.write(response.text)
            else:
                st.warning("Por favor, digite algo.")
                
    except Exception as e:
        st.error(f"Erro: {e}")
        st.info("Se o erro 404 persistir, precisamos liberar o uso da API no Console do Google Cloud.")
else:
    st.info("🛡️ Aguardando sua chave na barra lateral.")
