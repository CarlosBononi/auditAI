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
st.subheader("Seu guia definitivo contra golpes, fakes e promessas falsas online")
st.markdown("---")

# 3. Lógica do Robô
if api_key:
    try:
        # Configura a conexão com a API do Google
        genai.configure(api_key=api_key)
        
        # O prompt de sistema que define a personalidade do Auditor
        system_prompt = """Você é o 'Auditor Shield', uma IA especialista em análise de integridade digital e proteção ao consumidor. 
        Sua missão é desmascarar golpes, esquemas de pirâmide e promessas irreais.
        Analise links, textos ou vídeos e responda com um diagnóstico de risco (Baixo a Crítico) e um Veredito Final."""

        # Configuração do modelo (Usando o nome estável para evitar o erro NotFound)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt
        )

        # Campo de entrada para o usuário
        user_input = st.text_area(
            "O que você deseja auditar hoje?", 
            placeholder="Cole aqui o link do Instagram, site do curso, ou texto da promessa...",
            height=150
        )

        if st.button("Iniciar Auditoria"):
            if user_input:
                with st.spinner("O Auditor Shield está investigando..."):
                    # O robô processa a informação
                    response = model.generate_content(user_input)
                    
                    # Exibe o resultado na tela
                    st.success("Auditoria Concluída!")
                    st.markdown(response.text)
            else:
                st.warning("Por favor, insira algum conteúdo para que eu possa analisar.")

    except Exception as e:
        st.error(f"Ocorreu um erro na conexão: {e}")
        st.info("Dica: Verifique se sua API Key é válida e se o modelo está disponível na sua região.")
else:
    st.info("🛡️ Bem-vindo! Para começar, insira sua API Key na barra lateral esquerda.")

# Rodapé informativo
st.markdown("---")
st.caption("Aviso: Esta ferramenta utiliza IA para análise e deve ser usada como um guia de apoio à decisão.")
