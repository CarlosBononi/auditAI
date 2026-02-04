import streamlit as st
import google.generativeai as genai

# 1. Configuração visual e de título
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️")
st.title("🛡️ Auditor Shield")
st.subheader("Análise de Integridade Digital")

# 2. Entrada da API Key na barra lateral
api_key = st.sidebar.text_input("Cole sua API Key aqui:", type="password")

if api_key:
    try:
        # Configura a conexão oficial
        genai.configure(api_key=api_key)
        
        # Como a API está ativada, este modelo agora é reconhecido imediatamente
        model = genai.GenerativeModel('gemini-1.5-flash')

        # 3. Área de trabalho do usuário
        user_input = st.text_area("O que você deseja auditar hoje?", placeholder="Cole links ou textos aqui...")

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("O Auditor Shield está processando os dados..."):
                    # Instrução direta e eficaz
                    comando = f"Aja como o Auditor Shield. Analise se o seguinte conteúdo possui indícios de golpe ou fraude: {user_input}"
                    response = model.generate_content(comando)
                    
                    st.success("Auditoria Finalizada!")
                    st.markdown(response.text)
            else:
                st.warning("Por favor, forneça um conteúdo para análise.")
                
    except Exception as e:
        # Exibe erros de forma clara caso a chave seja colada incorretamente
        st.error(f"Atenção: {e}")
else:
    st.info("🛡️ Para começar, cole sua API Key na barra lateral esquerda.")
