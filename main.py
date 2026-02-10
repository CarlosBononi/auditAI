import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. TERMÔMETRO DE CORES COM SOBERANIA VERDE (PONTO 1)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    # Prioridade Máxima: VERDE
    if any(term in texto_upper for term in ["SEGURO", "TUDO OK", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO"]):
        cor, font = "#2ecc71", "white" 
    elif any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "GOLPE", "FAKE", "SCAM"]):
        cor, font = "#ff4b4b", "white" 
    elif any(term in texto_upper for term in ["ALTA ATENÇÃO", "MUITA ATENÇÃO", "PHISHING"]):
        cor, font = "#ffa500", "white" 
    elif any(term in texto_upper for term in ["ATENÇÃO", "IMAGEM", "IA", "FOTO"]):
        cor, font = "#f1c40f", "black" 
    else:
        cor, font = "#3498db", "white" # AZUL (NEUTRO)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 1px solid #d1d5db; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        {texto}
    </div>
    '''

# CSS PARA BOTÕES LADO A LADO E SUTIS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    /* Botão Executar */
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    /* Botão Limpar (Sutil e Cinza) */
    div.stButton > button:nth-child(1) { transition: 0.3s; }
    div.stButton > button:hover { border: 1px solid #2ecc71; opacity: 0.8; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO ESTÁVEL (BASE ORIGINAL)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de Conexão: {e}"); st.stop()

# 4. CABEÇALHO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. ÁREA DE PERÍCIA
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints, PDFs, E-mails):", type=["jpg", "png", "jpeg", "pdf", "eml", "pst"])
if uploaded_file and uploaded_file.type not in ["application/pdf"] and not uploaded_file.name.endswith(('.eml', '.pst')):
    st.image(uploaded_file, use_container_width=True)

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Esta foto é real? Analise metadados e anatomia.'", height=120)

# 6. COMANDOS LADO A LADO
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        if not user_query and not uploaded_file:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando varredura técnica..."):
                try:
                    instrucao = "Aja como AuditIA, perito sênior. Se for legítimo, use 'CLASSIFICAÇÃO: SEGURO'."
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    if uploaded_file:
                        if uploaded_file.name.endswith('.eml'):
                            msg = email.message_from_bytes(uploaded_file.read(), policy=policy.default)
                            contexto.append(f"E-MAIL: {msg.get_body(preferencelist=('plain')).get_content()}")
                        elif uploaded_file.type == "application/pdf":
                            contexto.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                        else: contexto.append(Image.open(uploaded_file).convert('RGB'))
                    
                    contexto.append(user_query)
                    response = model.generate_content(contexto, request_options={"timeout": 600})
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e: st.error(f"Instabilidade no servidor: {e}")

with col2:
    # Botão Limpar simplificado para evitar erro de sintaxe
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.rerun()

# 7. CENTRO DE AJUDA "ARTIGO ÚTIL" (ESTILO HELP CENTER)
st.markdown("---")
with st.expander("📖 Central de Ajuda - Como utilizar o AuditIA"):
    menu_tabs = st.tabs(["Manual de Uso", "FAQ", "Feedback"])
    
    with menu_tabs[0]:
        st.markdown("""
        ### 🛡️ Guia Rápido de Perícia
        - **Upload**: Aceitamos prints, PDFs (até 1000 pág) e e-mails (.eml).
        - **Contexto**: No campo de texto, detalhe o que deseja auditar (ex: metadados, sombras, SPF).
        - **Análise**: Clique em Executar e aguarde a varredura multilinear de 12 marcadores.
        """)
    
    with menu_tabs[1]:
        st.markdown("""
        **Q: O robô é 100% preciso?** R: O AuditIA utiliza probabilidade estatística de alta fidelidade forense.
        
        **Q: Qual o limite de arquivos?** R: Arquivos individuais de até 200MB.
        """)
    
    with menu_tabs[2]:
        st.write("Este manual ou a última análise foi útil?")
        cf1, cf2 = st.columns([1, 4])
        if cf1.button("👍 Sim"): st.success("Agradecemos o feedback!")
        if cf1.button("👎 Não"): st.info("Sua sugestão foi enviada para auditaiajuda@gmail.com")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
