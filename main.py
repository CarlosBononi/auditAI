import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime, timedelta

# 1. Configuração de Estilo e Semáforo
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper or "GOLPE CONFIRMADO" in texto_upper:
        return f'<div style="background-color: #ff4b4b; padding: 20px; border-radius: 10px; color: white; font-weight: bold;">{texto}</div>'
    elif "POSSÍVEL FRAUDE" in texto_upper or "PROVÁVEL GOLPE" in texto_upper:
        return f'<div style="background-color: #ffa500; padding: 20px; border-radius: 10px; color: white; font-weight: bold;">{texto}</div>'
    elif "ATENÇÃO" in texto_upper or "INDICAÇÕES SUSPEITAS" in texto_upper:
        return f'<div style="background-color: #f1c40f; padding: 20px; border-radius: 10px; color: black; font-weight: bold;">{texto}</div>'
    elif "SEGURO" in texto_upper or "TUDO OK" in texto_upper:
        return f'<div style="background-color: #2ecc71; padding: 20px; border-radius: 10px; color: white; font-weight: bold;">{texto}</div>'
    else:
        return f'<div style="background-color: #3498db; padding: 20px; border-radius: 10px; color: white; font-weight: bold;">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error(f"Erro: {e}"); st.stop()

# 3. Cabeçalho (Logo à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=450)
except:
    st.title("👁️ AuditIA")

st.markdown("### Auditoria de Integridade Digital")

# 4. Interface
uploaded_file = st.file_uploader("📸 Envie evidências (Imagem ou PDF):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Contexto da auditoria:", placeholder="Descreva o que deseja analisar...")

# 5. Execução com Horário de Brasília
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Forneça conteúdo.")
    else:
        # AJUSTE DE HORÁRIO: UTC-3 (Brasília)
        data_br = datetime.now() - timedelta(hours=3)
        data_str = data_br.strftime("%d/%m/%Y %H:%M:%S")
        
        with st.spinner("Auditando..."):
            try:
                instrucao = f"""
                Aja como o AuditIA. Hoje é {data_str}. 
                Ao final da sua análise, você DEVE escolher uma destas classificações e escrevê-la em LETRAS MAIÚSCULAS no início do veredito:
                - FRAUDE CONFIRMADA
                - POSSÍVEL FRAUDE
                - ATENÇÃO (Para indicações suspeitas)
                - SEGURO (Caso esteja tudo ok)
                - NEUTRO (Caso não haja dados suficientes)
                """
                
                conteudo = [instrucao]
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                    else:
                        conteudo.append(Image.open(uploaded_file).convert('RGB'))
                if user_input: conteudo.append(user_input)
                
                response = model.generate_content(conteudo)
                resultado = response.text
                
                st.subheader("📋 Veredito AuditIA")
                # Aplica a cor dinamicamente
                st.markdown(aplicar_cor_veredito(resultado), unsafe_allow_html=True)
                
                # Botão PDF
                # (O código do PDF continua aqui igual ao anterior)
            except Exception as e:
                st.error(f"Erro: {e}")

st.markdown("---")
st.caption(f"AuditIA - Localização: Vargem Grande do Sul, SP")
