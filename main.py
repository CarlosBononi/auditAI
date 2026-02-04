import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Configuração de Estilo AuditIA (SEU LAYOUT ORIGINAL MANTIDO)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    
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
        background-color: #59ea63;
        color: #000000;
    }
    
    .stTextArea textarea { 
        background-color: #f0f2f6; 
        color: #333333; 
        border: 1px solid #4a4a4a; 
    }
    
    .stFileUploader label { color: #333333 !important; }
    .stFileUploader section { 
        background-color: #f0f2f6; 
        border: 1px dashed #4a4a4a; 
        color: #333333; 
    }

    .stAlert { 
        background-color: #f9f9f9; 
        border-left: 5px solid #59ea63; 
        color: #333333; 
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    }
    
    h1, h2, h3 { color: #4a4a4a !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão com a Chave (Lógica vencedora do histórico)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 3. Cabeçalho com o Logotipo
try:
    logo = Image.open("Logo_AI_1.png")
    # Centralização otimizada para todas as telas
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(logo, width=300) 
except:
    st.title("👁️ AuditIA")

st.markdown("<h3 style='text-align: center;'>Auditoria de Integridade Digital</h3>", unsafe_allow_html=True)
st.write("<p style='text-align: center;'>Analise prints e mensagens suspeitas com precisão técnica.</p>", unsafe_allow_html=True)

# 4. Interface de Trabalho (COM AJUSTE PARA CELULAR)
# 'label_visibility' ajuda o navegador móvel a focar no botão de upload
uploaded_file = st.file_uploader(
    "📸 Envie um print do golpe (opcional):", 
    type=["jpg", "png", "jpeg"],
    label_visibility="visible"
)

if uploaded_file:
    # Abrir a imagem com tratamento de erro para mobile
    try:
        img_temp = Image.open(uploaded_file)
        st.image(img_temp, caption="Evidência carregada", use_container_width=True)
    except:
        st.error("Erro ao carregar imagem. Tente tirar um novo print.")

user_input = st.text_area(
    "📝 Descreva ou pergunte sobre o caso:", 
    placeholder="Ex: Verifique se os dados deste print indicam uma fraude financeira...",
    height=150
)

# 5. Execução da Auditoria
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Por favor, forneça uma imagem ou texto para análise.")
    else:
        with st.spinner("🕵️ O AuditIA está processando..."):
            try:
                comando_base = "Aja como o AuditIA. Analise o conteúdo e dê um veredito direto."
                
                if uploaded_file:
                    img_input = Image.open(uploaded_file)
                    if user_input:
                        response = model.generate_content([comando_base, img_input, user_input])
                    else:
                        response = model.generate_content([comando_base, img_input])
                else:
                    response = model.generate_content(f"{comando_base} Conteúdo: {user_input}")
                
                st.subheader("📋 Relatório AuditIA")
                st.info(response.text)
                
            except Exception as e:
                st.error(f"Erro na análise: {e}")

# 6. Rodapé
st.markdown("---")
with st.expander("💡 Dicas Estratégicas"):
    st.markdown("""
    * **Prints Nítidos**: Certifique-se de que links estejam visíveis.
    * **Contexto**: Diga onde encontrou a promessa (Ex: WhatsApp).
    * **Dúvidas**: Pergunte sobre CNPJs ou links de pagamento.
    """)

st.caption("AuditIA - Tecnologia e Segurança Digital")
