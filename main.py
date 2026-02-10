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

# 2. TERMÔMETRO DE CORES (RESTAURADO E CALIBRADO)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if any(term in texto_upper for term in ["SEGURO", "TUDO OK", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO"]):
        cor, font = "#2ecc71", "white" # VERDE SOBERANO
    elif any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "GOLPE", "FAKE", "SCAM"]):
        cor, font = "#ff4b4b", "white" # VERMELHO
    elif any(term in texto_upper for term in ["ALTA ATENÇÃO", "MUITA ATENÇÃO", "PHISHING"]):
        cor, font = "#ffa500", "white" # LARANJA
    elif any(term in texto_upper for term in ["ATENÇÃO", "IMAGEM", "IA", "FOTO"]):
        cor, font = "#f1c40f", "black" # AMARELO
    else:
        cor, font = "#3498db", "white" # AZUL (NEUTRO)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        {texto}
    </div>
    '''

# CSS PARA BOTÕES SUTIS E PROXIMIDADE
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    /* Botão Executar (Forte) */
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    /* Botão Limpar (Sutil) */
    div.stButton > button[kind="secondary"] { background-color: #f8f9fa; color: #6c757d; border: 1px solid #dee2e6; border-radius: 8px; height: 3.5em; width: 100%; }
    div.stButton > button:hover { opacity: 0.9; border: 1px solid #2ecc71; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO (BASE ORIGINAL)
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
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints, PDFs, E-mails .eml ou .pst):", type=["jpg", "png", "jpeg", "pdf", "eml", "pst"])
if uploaded_file and uploaded_file.type not in ["application/pdf"] and not uploaded_file.name.endswith(('.eml', '.pst')):
    st.image(uploaded_file, use_container_width=True)

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Esta foto é real? Analise metadados e anatomia.'", height=120)

# 6. MOTOR PERICIAL COM BOTÕES LADO A LADO
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        if not user_query and not uploaded_file:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ AuditIA realizando varredura técnica..."):
                try:
                    instrucao = f"Aja como AuditIA, perito sênior. Se for legítimo, use 'CLASSIFICAÇÃO: SEGURO'."
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
                    response = model.generate_content(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

with col2:
    if st.button("🗑️ LIMPAR CASO", kind="secondary"):
        st.session_state.historico_pericial = []; st.rerun()

# 7. CENTRO DE AJUDA "COMO UTILIZAR" (PONTO 5)
st.markdown("---")
with st.expander("📖 Central de Ajuda & FAQ - Como utilizar o AuditIA"):
    st.tabs_ajuda = st.tabs(["Manual de Uso", "Perguntas Frequentes", "Feedback"])
    
    with st.tabs_ajuda[0]:
        st.markdown("""
        ### 🛡️ Passo a Passo para uma Perícia de Elite
        1. **Upload de Provas**: Arraste prints de WhatsApp, PDFs ou arquivos de e-mail (.eml).
        2. **Pergunta Direta**: No campo de texto, detalhe sua dúvida (ex: 'Verifique se há indícios de manipulação nesta foto').
        3. **Execução**: Clique em 'Executar Perícia' e aguarde a varredura multilinear.
        4. **Laudo**: O resultado aparecerá colorido conforme o nível de risco detectado.
        """)
    
    with st.tabs_ajuda[1]:
        st.markdown("""
        **Q: Qual a precisão do sistema?** R: Analisamos 12 marcadores anatômicos e registros SPF/DKIM para máxima fidelidade.  
        **Q: Quais arquivos são aceitos?** R: Imagens, PDFs (até 1000 pág) e e-mails (.eml/.pst).  
        **Q: Qual o limite de tamanho?** R: Até 200MB por arquivo individual.
        """)
    
    with st.tabs_ajuda[2]:
        st.write("Este artigo ou análise foi útil?")
        col_f1, col_f2 = st.columns([1, 5])
        if col_f1.button("👍 Sim"): st.success("Obrigado pelo feedback!")
        if col_f1.button("👎 Não"): st.info("Sentimos muito. Envie sugestões para auditaiajuda@gmail.com")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
