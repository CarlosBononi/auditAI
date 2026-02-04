import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração do Layout (Fundo Branco e Cinza conforme solicitado)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    /* Estilo para manter o fundo branco e fontes cinza escuro */
    .stApp { background-color: #ffffff; color: #333333; }
    
    /* Botão Cinza Escuro (Cor do olho da logo) */
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
        background-color: #59ea63; /* Verde Néon apenas no hover */
        color: #000000;
    }
    
    /* Campos de entrada com cores visíveis em qualquer tela */
    .stTextArea textarea { 
        background-color: #f8f9fa; 
        color: #333333; 
        border: 1px solid #d1d5db; 
    }
    
    /* Upload de arquivos otimizado para clique no celular */
    .stFileUploader section { 
        background-color: #f8f9fa; 
        border: 1px dashed #4a4a4a; 
        color: #333333; 
    }

    /* Alerta de Veredito nítido */
    .stAlert { 
        background-color: #ffffff; 
        border-left: 5px solid #59ea63; 
        color: #333333; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    h1, h2, h3 { color: #4a4a4a !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão Segura (Lógica de listagem para evitar erro 404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho com Logo Centralizada
try:
    logo = Image.open("Logo_AI_1.png")
    # Centralização responsiva
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo, use_container_width=True) 
except:
    st.title("👁️ AuditIA")

st.markdown("<h3 style='text-align: center;'>Auditoria de Integridade Digital</h3>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Analise prints e mensagens suspeitas com precisão técnica.</p>", unsafe_allow_html=True)

# 4. Interface de Trabalho Unificada
# accept_multiple_files=False garante compatibilidade mobile
uploaded_file = st.file_uploader(
    "📸 Envie um print do golpe (opcional):", 
    type=["jpg", "png", "jpeg"],
    accept_multiple_files=False
)

if uploaded_file:
    img_temp = Image.open(uploaded_file)
    st.image(img_temp, caption="Evidência carregada", use_container_width=True)

user_input = st.text_area(
    "📝 Descreva ou pergunte sobre o caso:", 
    placeholder="Ex: Verifique se os dados deste print indicam uma fraude financeira...",
    height=150
)

# 5. Execução da Auditoria Inteligente
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça uma imagem ou texto para análise.")
    else:
        with st.spinner("🕵️ O AuditIA está rastreando padrões de fraude..."):
            try:
                comando = "Aja como o AuditIA. Analise o conteúdo fornecido (imagem e/ou texto) e dê um veredito direto sobre riscos de fraude."
                
                if uploaded_file:
                    img_input = Image.open(uploaded_file)
                    if user_input:
                        response = model.generate_content([comando, img_input, user_input])
                    else:
                        response = model.generate_content([comando, img_input])
                else:
                    response = model.generate_content(f"{comando} Conteúdo: {user_input}")
                
                st.subheader("📋 Relatório AuditIA")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Erro na análise: {e}")

# 6. Rodapé com Dicas
st.markdown("---")
with st.expander("💡 Dicas Estratégicas"):
    st.markdown("""
    * **Prints Nítidos**: Garanta que os links estejam legíveis.
    * **Análise de Chaves**: O AuditIA pode identificar riscos em chaves PIX citadas em imagens.
    * **Combinação**: Use o texto para perguntar sobre detalhes específicos da imagem carregada.
    """)

st.caption("AuditIA - Tecnologia e Segurança Digital")
