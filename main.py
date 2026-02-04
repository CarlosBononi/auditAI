import streamlit as st
import google.generativeai as genai

# 1. Configuração visual do Web App
st.set_page_config(page_title="Auditor Shield", page_icon="🛡️")
st.title("🛡️ Auditor Shield")
st.subheader("Análise de Integridade Digital")

# Barra lateral para a chave
api_key = st.sidebar.text_input("Cole sua API Key aqui:", type="password")

if api_key:
    try:
        # Configura a conexão oficial
        genai.configure(api_key=api_key)
        
        # SOLUÇÃO PARA O ERRO 404: 
        # Em vez de escrever o nome, perguntamos ao Google quais modelos você pode usar
        modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Escolhemos o primeiro da lista (que será o gemini-1.5-flash ou gemini-pro)
        modelo_escolhido = modelos_disponiveis[0]
        model = genai.GenerativeModel(modelo_escolhido)

        # 2. Área de trabalho
        user_input = st.text_area("O que você deseja auditar hoje?", placeholder="Cole links ou textos aqui...")

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("O Auditor Shield está processando..."):
                    # Instrução direta
                    comando = f"Aja como o Auditor Shield. Analise se o seguinte conteúdo possui indícios de golpe: {user_input}"
                    response = model.generate_content(comando)
                    
                    st.success("Auditoria Concluída!")
                    st.markdown(response.text)
            else:
                st.warning("Por favor, forneça um conteúdo.")
                
    except Exception as e:
        st.error(f"Erro detectado: {e}")
else:
    st.info("🛡️ Para começar, cole sua API Key na barra lateral esquerda.")
