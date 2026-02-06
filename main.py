import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO E MEMÓRIA PERICIAL
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" # Limpa a caixa de texto automaticamente

st.set_page_config(page_title="AuditIA - Inteligência Pericial", page_icon="👁️", layout="centered")

# 2. SEMÁFORO DE CORES COM CLASSIFICAÇÃO EXPLÍCITA
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white" # Vermelho
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white" # Laranja
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black" # Amarelo
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper: cor, font = "#2ecc71", "white" # Verde
    else: cor, font = "#3498db", "white" # Azul (Informativo / Neutro)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        {texto}
    </div>
    '''

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXÃO SEGURA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Erro na API."); st.stop()

# 4. CABEÇALHO (Branding Profissional)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 5. INTERFACE DE COLETA DE EVIDÊNCIAS
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints, PDFs, E-mails .eml):", type=["jpg", "png", "jpeg", "pdf", "eml"])
if uploaded_file and uploaded_file.type != "application/pdf" and not uploaded_file.name.endswith('.eml'):
    st.image(uploaded_file, use_container_width=True)

# EXIBIÇÃO DA LINHA DE INVESTIGAÇÃO (Histórico com Pergunta no Topo)
st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

# Entrada de texto com limpeza automática via callback
user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Faça sua pergunta de acompanhamento sobre a evidência...", height=120)

# FUNÇÃO LAUDO PDF CONSOLIDADO
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = conteudo.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR DE EXECUÇÃO PERICIAL
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not uploaded_file:
            st.warning("Por favor, insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            data_atual = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            
            with st.spinner("🕵️ Realizando auditoria forense..."):
                try:
                    instrucao_mestre = f"""
                    Aja como o AuditIA. Data e Hora: {data_atual}.
                    DIRETRIZES DE RESPOSTA:
                    1. TÍTULO OBRIGATÓRIO: Inicie SEMPRE com: 'PERGUNTA REALIZADA EM {data_atual}: "{pergunta_efetiva}"'
                    2. RESPOSTA DIRETA: Responda IMEDIATAMENTE à dúvida técnica. Não faça resumos longos do documento se não for solicitado.
                    3. CLASSIFICAÇÃO: Se a análise não detectar fraude, inicie o parágrafo de veredito com 'CLASSIFICAÇÃO: INFORMATIVO / NEUTRO'. 
                       Se houver risco, use 'FRAUDE CONFIRMADA', 'POSSÍVEL FRAUDE' ou 'ATENÇÃO'.
                    4. ESTRUTURA: Use termos periciais técnicos (engenharia social, metadados, integridade documental).
                    5. FECHAMENTO: 'Resumo do Veredito:'.
                    """
                    
                    contexto_ia = [instrucao_mestre]
                    for h in st.session_state.historico_pericial: contexto_ia.append(h)
                    
                    if uploaded_file:
                        if uploaded_file.name.endswith('.eml'):
                            msg = email.message_from_bytes(uploaded_file.read(), policy=policy.default)
                            corpo_email = msg.get_body(preferencelist=('plain')).get_content()
                            contexto_ia.append(f"DADOS DO E-MAIL: {corpo_email}")
                        elif uploaded_file.type == "application/pdf":
                            contexto_ia.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                        else:
                            contexto_ia.append(Image.open(uploaded_file).convert('RGB'))
                    
                    contexto_ia.append(pergunta_efetiva)
                    
                    response = model.generate_content(contexto_ia)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro técnico: {e}")

with col2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.rerun()

# GERADOR DE PDF DA SESSÃO
if st.session_state.historico_pericial:
    tz_br = pytz.timezone('America/Sao_Paulo')
    pdf_bytes = gerar_pdf_pericial(st.session_state.historico_pericial[-1], datetime.now(tz_br).strftime("%d/%m/%Y %H:%M"))
    st.download_button(label="📥 Baixar Laudo da Última Análise (PDF)", data=pdf_bytes, file_name="Laudo_AuditIA.pdf", mime="application/pdf")

# 7. GUIA MESTRE (ROADMAP E-DISCOVERY)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ Inteligência Forense de Última Geração
    O **AuditIA** é uma plataforma multimodal projetada para auditorias complexas e *e-discovery*.
    
    * 🕵️‍♀️ **Forense de Imagem e Documentos:** Scrutínio de prints e PDFs buscando anomalias visuais.
    * 🧠 **Investigação Iterativa:** Memória de contexto para follow-up de auditoria (Padrão Guti).
    * ✉️ **Email Forensics:** Auditoria de cabeçalhos e análise de e-mails em massa.
    * 🔵 **AZUL (INFORMATIVO / NEUTRO):** Classificação explícita para consultas técnicas e preventivas.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
