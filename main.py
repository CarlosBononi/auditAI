import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Estilo AuditIA (Layout Branco e Cinza Pericial)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    /* Fundo geral e textos nítidos */
    .stApp { background-color: #ffffff; color: #333333; }
    
    /* Botão em Cinza Tecnológico (Extraído do olho da logo) */
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
        background-color: #59ea63; /* Destaque em Verde Néon no hover */
        color: #000000;
        box-shadow: 0 4px 15px rgba(89, 234, 99, 0.3);
    }
    
    /* Campos de Entrada com Fundo Suave */
    .stTextArea textarea { 
        background-color: #f8f9fa; 
        color: #333333; 
        border: 1px solid #d1d5db; 
    }
    
    /* Área de Upload Visível e Estilizada */
    .stFileUploader section { 
        background-color: #f8f9fa; 
        border: 1px dashed #4a4a4a; 
        color: #333333; 
    }

    /* Relatório de Auditoria */
    .stAlert { 
        background-color: #ffffff; 
        border-left: 5px solid #59ea63; 
        color: #333333; 
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Títulos em Cinza Escuro */
    h1, h2, h3 { color: #4a4a4a !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão Segura e Listagem de Modelos
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho com a Logo Redimensionada
try:
    logo = Image.open("Logo_AI_1.png")
    # Centralização manual da imagem
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo, width=300) 
except:
    st.title("👁️ AuditIA")

st.markdown("<h3 style='text-align: center;'>Auditoria de Integridade Digital</h3>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Analise prints e mensagens suspeitas com precisão técnica.</p>", unsafe_allow_html=True)

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

# 5. Dicas Estratégicas
st.markdown("---")
with st.expander("💡 Dicas Estratégicas"):
    st.markdown("""
    * **Foco no Detalhe**: Se houver um link no print, peça especificamente para o AuditIA analisá-lo.
    * **Dados Bancários**: O AuditIA pode identificar se chaves PIX citadas em imagens já foram reportadas como fraudulentas.
    * **Urgência Falsa**: O robô analisa se o tom da mensagem tenta te forçar a agir rápido, um sinal clássico de golpe.
    """)

st.caption("AuditIA - Tecnologia e Segurança Digital")
