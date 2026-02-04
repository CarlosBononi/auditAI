import streamlit as st
import google.generativeai as genai

# Configuração visual
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️")
st.title("🛡️ Auditor Shield")

# Configuração na barra lateral
api_key = st.sidebar.text_input("Cole sua API Key aqui:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Usaremos o 'gemini-pro' que é o modelo mais estável e compatível 
        # com quase todas as chaves geradas no AI Studio
        model = genai.GenerativeModel('gemini-pro')

        user_input = st.text_area("O que deseja auditar?")

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("Analisando..."):
                    # Colocamos a personalidade do Auditor direto no pedido
                    comando = f"Aja como o Auditor Shield, um perito em golpes digitais. Analise se isto é fraude ou promessa falsa e dê um veredito: {user_input}"
                    
                    response = model.generate_content(comando)
                    st.success("Resultado da Auditoria:")
                    st.write(response.text)
            else:
                st.warning("Por favor, cole um texto ou link.")
                
    except Exception as e:
        # Se der erro, ele vai nos dizer exatamente o porquê agora
        st.error(f"Erro de Conexão: {e}")
else:
    st.info("Aguardando API Key na barra lateral...")
