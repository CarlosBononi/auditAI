import streamlit as st
import google.generativeai as genai

# 1. Configuração visual do Web App
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️", layout="wide")

# Barra lateral para configurações
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("Cole sua API Key do Google aqui:", type="password")
st.sidebar.info("Obtenha sua chave em: aistudio.google.com")

# 2. Título e cabeçalho principal
st.title("🛡️ Auditor Shield")
st.subheader("Seu guia definitivo contra golpes e promessas falsas")
st.markdown("---")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        system_prompt = """Você é o 'Auditor Shield', especialista em análise de integridade digital. 
        Sua missão é desmascarar golpes e promessas irreais. 
        Dê um diagnóstico de risco e um Veredito Final."""

        # NOME CORRIGIDO ABAIXO:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest", 
            system_instruction=system_prompt
        )

        user_input = st.text_area("O que deseja auditar hoje?", placeholder="Cole o link ou texto aqui...")

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("Investigando..."):
                    response = model.generate_content(user_input)
                    st.success("Auditoria Concluída!")
                    st.markdown(response.text)
            else:
                st.warning("Insira um conteúdo para análise.")

    except Exception as e:
        # Se ainda der erro de nome, o robô vai te avisar aqui
        st.error(f"Erro de conexão: {e}")
else:
    st.info("🛡️ Insira sua API Key na lateral para começar.")
