import streamlit as st
import google.generativeai as genai

# Configuração visual do Web App
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️", layout="wide")

st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("Cole sua API Key do Google aqui:", type="password")

st.title("🛡️ Auditor Shield")
st.subheader("Seu guia contra golpes e promessas falsas")
st.markdown("---")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Lista de nomes possíveis para o modelo, do mais novo ao mais comum
        model_options = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]
        
        system_prompt = "Você é o 'Auditor Shield', especialista em identificar golpes e fakes."

        user_input = st.text_area("O que deseja auditar hoje?")

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("Investigando..."):
                    success = False
                    # Tenta cada modelo até um funcionar
                    for model_name in model_options:
                        try:
                            model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                            response = model.generate_content(user_input)
                            st.success(f"Auditoria Concluída!")
                            st.markdown(response.text)
                            success = True
                            break 
                        except:
                            continue
                    
                    if not success:
                        st.error("Não conseguimos conectar com os modelos do Google. Verifique se sua chave está correta no AI Studio.")
            else:
                st.warning("Insira um conteúdo para análise.")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
else:
    st.info("🛡️ Insira sua API Key na lateral para começar.")
