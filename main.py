import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Auditor Shield", page_icon="🛡️")

# Interface lateral
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("Cole sua API Key do Google aqui:", type="password")

st.title("🛡️ Auditor Shield")
st.subheader("Análise de Integridade Digital")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Nome exato que o Google exige para o modelo que você selecionou
        model = genai.GenerativeModel('gemini-1.5-flash')

        user_input = st.text_area("O que deseja analisar?")

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("Analisando..."):
                    # Aqui incluímos as instruções direto no comando
                    prompt_completo = f"Aja como um Auditor especialista em golpes. Analise isto: {user_input}"
                    response = model.generate_content(prompt_completo)
                    st.success("Resultado:")
                    st.write(response.text)
            else:
                st.warning("Insira um link ou texto.")
    except Exception as e:
        st.error(f"Erro técnico: {e}")
else:
    st.info("Coloque sua API Key na esquerda.")
