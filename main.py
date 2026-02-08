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

# 2. SEMÁFORO DE CORES BLINDADO
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white" # Azul (Informativo / Neutro)
    
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

# 4. CABEÇALHO (Logo 500px à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA")

st.markdown("---")

# 5. ÁREA DE PERÍCIA
uploaded_file = st.file_uploader("📂 Upload de Provas (Prints, PDFs até 1000 pág, E-mails .eml ou .pst):", type=["jpg", "png", "jpeg", "pdf", "eml", "pst"])
if uploaded_file and uploaded_file.type not in ["application/pdf"] and not uploaded_file.name.endswith(('.eml', '.pst')):
    st.image(uploaded_file, use_container_width=True)

# HISTÓRICO COM RASTREABILIDADE
st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Esta imagem foi gerada por IA?' ou 'Analise as mãos desta pessoa'...", height=120)

# FUNÇÃO LAUDO PDF
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10); pdf.cell(200, 10, txt=f"Data da Perícia: {data_f}", ln=True, align='C')
    pdf.ln(10); pdf.set_font("Arial", size=11)
    texto_limpo = conteudo.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR PERICIAL COM PROTOCOLO DE DESCONFIANÇA MÁXIMA
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not uploaded_file:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando auditoria forense avançada..."):
                try:
                    instrucao = f"""
                    Aja como o AuditIA, inteligência forense de elite para auditorias e e-discovery. Data: {agora}.
                    
                    DIRETRIZ DE RIGOR EXTREMO EM IMAGENS:
                    1. Imagens geradas por IA (Wix, Midjourney, etc) estão se tornando hiper-realistas. Você deve buscar ativamente por MICRO-ANOMALIAS:
                       - MÃOS E DEDOS: Verifique fusões, número incorreto de dedos ou articulações estranhas.
                       - CABELOS E TEXTURAS: Observe se a textura é perfeitamente uniforme demais (plástica).
                       - FUNDO E FÍSICA: Verifique se as sombras e reflexos nos olhos (catchlights) obedecem a uma única fonte de luz.
                    2. NUNCA classifique uma imagem de pessoa como "SEGURO" ou "PROVAVELMENTE REAL" apenas por falta de provas óbvias. Na dúvida, use CLASSIFICAÇÃO: ATENÇÃO.
                    3. Se detectar erros anatômicos (como dedos fundidos), use CLASSIFICAÇÃO: FRAUDE CONFIRMADA.

                    ESTRUTURA DE RESPOSTA OBRIGATÓRIA:
                    - CABEÇALHO: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'
                    - CLASSIFICAÇÃO: [TIPO]
                    - RESPOSTA: Análise técnica cirúrgica, focada na dúvida do auditor.
                    - FECHAMENTO: 'Resumo do Veredito:'.
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
    st.download_button(label="📥 Baixar Laudo da Última Análise (PDF)", data=pdf_bytes, file_name="Laudo_AuditIA.pdf", mime="application/pdf")

# 7. GUIA MESTRE AUDITIA - RESTAURAÇÃO TOTAL (PILAR DO MVP)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    st.markdown("""
    ### 🛡️ O Poder da Perícia AuditIA
    O **AuditIA** é uma inteligência forense digital projetada para desmascarar crimes cibernéticos e realizar e-discovery profissional em tempo real.

    **Capacidades Técnicas Detalhadas:**
    1.  **Análise Multifacetada de Documentos**: Processamento profundo de prints (WhatsApp/Instagram), PDFs e blocos de texto em busca de anomalias visuais ou estruturais.
    2.  **Detecção de Artefatos de IA**: Scrutínio de micro-anomalias anatômicas, texturas sintéticas e inconsistências de física em imagens geradas por IA.
    3.  **e-Discovery & PST/EML**: Busca inteligente em massa dentro de arquivos de dados do Outlook (.pst) e e-mails individuais (.eml) para identificar intenções e fraudes corporativas.
    4.  **Identificação de Engenharia Social**: Análise de linguagem e comportamento sugerido para desmascarar tentativas de manipulação psicológica, phishing e spoofing.
    5.  **Reconhecimento de Esquemas Ponzi/Pirâmide**: Avaliação técnica de modelos de negócios com promessas de retorno garantido e remuneração baseada em recrutamento.
    6.  **Verificação de Consistência Documental**: Comparação de dados, fontes, metadados e selos de segurança em recibos, contratos e boletos.
    7.  **Indicadores de Compromisso (IoCs)**: Identificação técnica de URLs maliciosas, domínios e e-mails associados a atividades criminosas.

    ---
    ### 🚦 Semáforo de Risco Pericial:
    * 🔴 **FRAUDE CONFIRMADA**: Evidências robustas e irrefutáveis detectadas.
    * 🟠 **POSSÍVEL FRAUDE**: Fortes indícios de irregularidade que exigem validação humana.
    * 🟡 **ATENÇÃO**: Elementos suspeitos ou micro-anomalias que merecem investigação.
    * 🟢 **SEGURO**: Conformidade verificada nos parâmetros analisados.
    * 🔵 **AZUL (NEUTRO)**: Suporte preventivo e respostas institucionais sem juízo de valor.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
