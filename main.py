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

st.set_page_config(page_title="AuditIA - e-Discovery & Forense", page_icon="👁️", layout="wide")

# 2. SEMÁFORO INTELIGENTE V18
def aplicar_estilo_pericial(texto, tipo_arquivo):
    texto_upper = texto.upper()
    
    # Se for imagem de pessoa, mantém o rigor do amarelo/laranja
    if tipo_arquivo in ['jpg', 'png', 'jpeg'] and "CLASSIFICAÇÃO: SEGURO" in texto_upper:
        cor, font = "#f1c40f", "black" # ATENÇÃO FORÇADA PARA IMAGENS
    elif "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white" # Azul (Neutro/Informativo)
    
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

# 3. CONEXÃO E SUPORTE
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos_disp[0])
except:
    st.error("Erro de Conexão API."); st.stop()

# SIDEBAR - CHATBOT E SUPORTE (Ponto 5)
with st.sidebar:
    st.header("🕵️ Suporte AuditIA")
    with st.expander("🤖 Chatbot de Dúvidas"):
        st.write("Como posso ajudar na sua perícia hoje?")
        duvida = st.text_input("Sua dúvida rápida:")
        if duvida:
            st.info("Para dúvidas técnicas complexas, use o botão de suporte abaixo.")
    
    st.markdown("---")
    whatsapp_url = "https://wa.me/5511913556631?text=Olá,%20preciso%20de%20suporte%20técnico%20avançado%20no%20AuditIA."
    st.link_button("📞 Falar com Especialista", whatsapp_url, use_container_width=True)
    st.caption("Suporte Direto via WhatsApp (Mascarado)")

# 4. CABEÇALHO
col_logo, _ = st.columns([2, 1])
with col_logo:
    try:
        logo = Image.open("Logo_AI_1.png")
        st.image(logo, width=500)
    except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. ÁREA DE INGESTÃO (DRAG AND DROP REFORÇADO)
uploaded_file = st.file_uploader("📂 Arraste e solte provas aqui (Prints, PDFs, E-mails .eml ou .pst):", type=["jpg", "png", "jpeg", "pdf", "eml", "pst"])

if uploaded_file and uploaded_file.type not in ["application/pdf"] and not uploaded_file.name.endswith(('.eml', '.pst')):
    st.image(uploaded_file, width=400)

st.subheader("🕵️ Linha de Investigação")
extensao = uploaded_file.name.split('.')[-1].lower() if uploaded_file else "texto"

for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco, extensao), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Analise este e-mail em busca de inconsistências financeiras'...", height=120)

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

# 6. MOTOR PERICIAL CONTEXTUAL (Ponto 2)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not uploaded_file:
            st.warning("Insira material.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Analisando evidências..."):
                try:
                    # PROMPT CONTEXTUALIZADO
                    if extensao in ['eml', 'pst', 'pdf']:
                        instrucao = f"""Aja como AuditIA, perito em e-discovery e documentos. Hoje: {agora}.
                        FOCO: Analise o TEXTO e os CABEÇALHOS. Não mencione análise de imagem ou anatomia.
                        ESTRUTURA: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"' -> CLASSIFICAÇÃO -> ANÁLISE TÉCNICA."""
                    else:
                        instrucao = f"""Aja como AuditIA, perito forense de imagem. Hoje: {agora}.
                        FOCO: Anatomia, artefatos de IA, luz e textura. Seja cético com fotos de pessoas.
                        ESTRUTURA: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"' -> CLASSIFICAÇÃO -> ANÁLISE TÉCNICA."""
                    
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    
                    if uploaded_file:
                        if extensao == 'eml':
                            msg = email.message_from_bytes(uploaded_file.read(), policy=policy.default)
                            contexto.append(f"E-MAIL: {msg.get_body(preferencelist=('plain')).get_content()}")
                        elif extensao == 'pdf':
                            contexto.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                        elif extensao == 'pst':
                            contexto.append(f"ARQUIVO PST: {uploaded_file.name}. Realize busca em massa.")
                        else:
                            contexto.append(Image.open(uploaded_file).convert('RGB'))
                    
                    contexto.append(pergunta_efetiva)
                    response = model.generate_content(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e:
                    if "429" in str(e): st.error("⚠️ Limite de cota. Aguarde 60s.")
                    else: st.error(f"Erro: {e}")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.rerun()

if st.session_state.historico_pericial:
    tz_br = pytz.timezone('America/Sao_Paulo')
    pdf_bytes = gerar_pdf_pericial(st.session_state.historico_pericial[-1], datetime.now(tz_br).strftime("%d/%m/%Y %H:%M"))
    st.download_button(label="📥 Baixar Laudo PDF", data=pdf_bytes, file_name="Laudo_AuditIA.pdf", mime="application/pdf")

# 7. GUIA MESTRE (RESTAURAÇÃO TOTAL - Ponto 3)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital"):
    st.markdown("""
    ### 🛡️ Inteligência Forense de Elite
    1. **Forense de Imagem**: Detecção de micro-anomalias anatômicas.
    2. **e-Discovery & PST**: Busca em massa de e-mails corporativos.
    3. **Engenharia Social**: Desmascara táticas de phishing e manipulação.
    4. **Esquemas Ponzi**: Avaliação técnica de pirâmides financeiras.
    5. **Consistência Documental**: Auditoria de metadados em contratos e recibos.
    6. **Memória Iterativa**: Histórico para follow-up de investigação.
    7. **IoCs**: Identificação de URLs e IPs maliciosos.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP")
