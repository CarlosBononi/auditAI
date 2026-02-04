import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Estilo AuditIA (Fundo Branco e Cinza Tecnológico)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    /* Fundo geral e textos principais */
    .stApp { background-color: #ffffff; color: #333333; }
    
    /* Personalização do Botão (Cinza do Logotipo) */
    div.stButton > button:first-child {
        background-color: #4a4a4a;
        color: #ffffff;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        width: 100%;
        height: 3.5em;
        transition: 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #59ea63; /* Verde Néon apenas no hover para destaque */
        color: #000000;
    }
    
    /* Caixas de texto e entradas (Fundo cinza claro com bordas nítidas) */
    .stTextArea textarea { 
        background-color: #f0f2f6; 
        color: #333333; 
        border: 1px solid #4a4a4a; 
    }
    
    /* Correção de visibilidade do Upload de Arquivos */
    .stFileUploader label { color: #333333 !important; }
    .stFileUploader section { 
        background-color: #f0f2f6; 
        border: 1px dashed #4a4a4a; 
        color: #333333; 
    }

    /* Estilo do Relatório (Veredito) */
    .stAlert { 
        background-color: #f9f9f9; 
        border-left: 5px solid #59ea63; 
        color: #333333; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Títulos em Cinza Escuro */
    h1, h2, h3 { color: #4a4a4a !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com a Chave (Lógica de listagem automática)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho com o Logotipo
try:
    # O código tentará carregar o arquivo .png que está no seu GitHub
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=400) # Largura fixada em 400px para não ocupar a tela toda
except:
    st.title("👁️ AuditIA")

st.markdown("### Auditoria de Integridade Digital")
st.write("Analise prints e mensagens suspeitas com precisão técnica.")

# 4. Interface de Trabalho
uploaded_file = st.file_uploader("📸 Envie um print do golpe (opcional):", type=["jpg", "png", "jpeg"])
if uploaded_file:
    st.image(uploaded_file, caption="Evidência carregada", use_container_width=True)

user_input = st.text_area(
    "📝 Descreva ou pergunte sobre o caso:", 
    placeholder="Ex: Verifique se os dados deste print indicam uma fraude financeira...",
    height=150
)

if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça uma imagem ou texto para análise.")
    else:
        with st.spinner("🕵️ O AuditIA está processando..."):
            try:
                comando_base = "Aja como o AuditIA. Analise o conteúdo fornecido e dê um veredito técnico sobre riscos de golpe ou fraude."
                
                if uploaded_file and user_input:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([comando_base, img, user_input])
                elif uploaded_file:
                    img = Image.open(uploaded_file)
                    response = model.generate_content([comando_base, img])
                else:
                    response = model.generate_content(f"{comando_base} Conteúdo: {user_input}")
                
                st.subheader("📋 Relatório AuditIA")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Erro na análise: {e}")

# 5. Rodapé Informativo
st.markdown("---")
with st.expander("💡 Dicas Estratégicas"):
    st.markdown("""
    * **Prints Nítidos**: Certifique-se de que links e nomes de usuários estejam visíveis na imagem.
    * **Contexto**: Use o campo de texto para dizer onde você encontrou essa promessa (Ex: WhatsApp, anúncio patrocinado).
    * **Dúvidas Específicas**: Você pode perguntar: 'Esse CNPJ é real?' ou 'Esse link de pagamento é seguro?'.
    """)

st.caption("AuditIA - Tecnologia e Segurança Digital")
