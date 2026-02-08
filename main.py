import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO PERICIAL
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. SEMÁFORO DE CORES (LÓGICA INVERTIDA E BLINDADA)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    # SE O ROBÔ DESOBEDECER E USAR AZUL PARA IMAGEM DE PESSOA, FORÇA O AMARELO
    if "CLASSIFICAÇÃO: SEGURO" in texto_upper or ("INFORMATIVO" in texto_upper and ("IMAGEM" in texto_upper or "FOTO" in texto_upper)):
        cor, font = "#f1c40f", "black" # AMARELO (ATENÇÃO FORÇADA)
    elif "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    else: cor, font = "#3498db", "white" # Azul (Informativo genuíno sobre documentos/texto)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        {texto}
    </div>
    '''

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transition: 0.3s; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO SEGURA (ANTI-404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos_disp[0])
except Exception as e:
    st.error(f"Erro de Conexão: {e}"); st.stop()

# 4. CABEÇALHO (Logo 500px)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 5. ÁREA DE PERÍCIA MULTIMODAL
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints, PDFs, E-mails .eml, .pst):", type=["jpg", "png", "jpeg", "pdf", "eml", "pst"])
if uploaded_file and uploaded_file.type not in ["application/pdf"] and not uploaded_file.name.endswith(('.eml', '.pst')):
    st.image(uploaded_file, use_container_width=True)

# HISTÓRICO COM RASTREABILIDADE
st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Esta imagem foi gerada por IA?'...", height=120)

# FUNÇÃO LAUDO PDF
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = conteudo.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR PERICIAL COM FILTRO DE FRAUDE OBRIGATÓRIO
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not uploaded_file:
            st.warning("Forneça material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Executando Protocolo de Fraude por IA..."):
                try:
                    instrucao = f"""
                    Aja como o AuditIA, inteligência forense de elite. Data: {agora}.
                    
                    REGRA DE OURO (INVERSÃO DO ÔNUS DA PROVA):
                    1. PARA IMAGENS FOTORREALISTAS DE PESSOAS: Assuma que é GERAÇÃO POR IA (FRAUDE) até que se prove o contrário com evidências FÍSICAS (não visuais), como ruído de sensor ou aberração cromática.
                    2. PROIBIÇÃO DE 'SEGURO': Você NÃO PODE classificar uma imagem de pessoa como "SEGURO" ou "REAL" baseando-se apenas em "parecer real". 
                    3. CLASSIFICAÇÃO OBRIGATÓRIA: Se a imagem for de uma pessoa e não apresentar erro anatômico óbvio, você DEVE usar 'CLASSIFICAÇÃO: ATENÇÃO (ALTA PROBABILIDADE DE IA)'. Se houver erro, use 'FRAUDE CONFIRMADA'.
                    4. ESTRUTURA: Inicie com 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"', seguido de 'CLASSIFICAÇÃO: [TIPO]'.
                    """
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    
                    if uploaded_file:
                        if uploaded_file.name.endswith('.eml'):
                            msg = email.message_from_bytes(uploaded_file.read(), policy=policy.default)
                            corpo = msg.get_body(preferencelist=('plain')).get_content()
                            contexto.append(f"DADOS DO E-MAIL: {corpo}")
                        elif uploaded_file.type == "application/pdf":
                            contexto.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                        else:
                            contexto.append(Image.open(uploaded_file).convert('RGB'))
                    
                    contexto.append(pergunta_efetiva)
                    response = model.generate_content(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e:
                    if "exceeds the supported page limit" in str(e): st.error("⚠️ Limite de 1000 páginas excedido.")
                    else: st.error(f"Erro técnico: {e}")

with col2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.rerun()

# DOWNLOAD PDF
if st.session_state.historico_pericial:
    tz_br = pytz.timezone('America/Sao_Paulo')
    pdf_bytes = gerar_pdf_pericial(st.session_state.historico_pericial[-1], datetime.now(tz_br).strftime("%d/%m/%Y %H:%M"))
    st.download_button(label="📥 Baixar Laudo PDF", data=pdf_bytes, file_name="Laudo_AuditIA.pdf", mime="application/pdf")

# 7. GUIA MESTRE AUDITIA (COMPLETO)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ Inteligência Forense Profissional
    O **AuditIA** é uma inteligência forense multimodal projetada para desmascarar crimes cibernéticos e realizar e-discovery profissional.

    **Capacidades Técnicas Detalhadas:**
    1.  **Análise Multifacetada de Documentos**: Processamento profundo de prints e PDFs buscando anomalias visuais.
    2.  **Detecção de Artefatos de IA**: Scrutínio de micro-anomalias anatômicas em imagens geradas.
    3.  **e-Discovery & PST/EML**: Busca inteligente em massa de e-mails para identificar intenções.
    4.  **Identificação de Engenharia Social**: Desmascara táticas de phishing e spoofing comportamental.
    5.  **Reconhecimento de Esquemas Ponzi**: Avaliação de modelos de pirâmide financeira.
    6.  **Verificação de Consistência Documental**: Comparação de metadados em recibos e contratos.
    7.  **Indicadores de Compromisso (IoCs)**: Mapeamento de URLs e IPs maliciosos.

    ---
    ### 🚦 Semáforo de Risco Pericial:
    * 🔴 **FRAUDE CONFIRMADA** | 🟠 **POSSÍVEL FRAUDE** | 🟡 **ATENÇÃO** | 🟢 **SEGURO** | 🔵 **AZUL (INFORMATIVO)**.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
