import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO E ACÚMULO DE ARQUIVOS (PONTO 4)
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Forense Estável", page_icon="👁️", layout="wide")

# 2. SEMÁFORO DE CORES BLINDADO (PONTO 1)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "FRAUDE CONFIRMADA" in texto_upper: cor, font = "#ff4b4b", "white"
    elif "POSSÍVEL FRAUDE" in texto_upper: cor, font = "#ffa500", "white"
    elif "ATENÇÃO" in texto_upper: cor, font = "#f1c40f", "black"
    elif "SEGURO" in texto_upper: cor, font = "#2ecc71", "white"
    else: cor, font = "#3498db", "white"
    return f'<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">{texto}</div>'

st.markdown("""<style>.stApp { background-color: #ffffff; color: #333333; } div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 4em; border-radius: 10px; } div.stButton > button:first-child:hover { background-color: #59ea63; color: black; transition: 0.3s; } .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; font-size: 16px; }</style>""", unsafe_allow_html=True)

# 3. CONEXÃO ESTÁVEL (FIX ERRO 404/NOTFOUND)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Busca dinâmica do modelo para evitar erro de versão
    model_name = 'gemini-1.5-flash-latest' 
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error(f"Erro Crítico de Inicialização: {e}"); st.stop()

# SIDEBAR - ASSISTENTE INTELIGENTE (PONTO 5)
with st.sidebar:
    st.header("🤖 Assistente AuditIA")
    pergunta_suporte = st.text_input("Dúvida rápida sobre o sistema?")
    if pergunta_suporte:
        try:
            prompt_sup = f"Aja como assistente do AuditIA. Responda: {pergunta_suporte}. No final, diga que para casos complexos o usuário pode falar com o perito no link: https://wa.me/5511913556631"
            res_sup = model.generate_content(prompt_sup)
            st.info(res_sup.text)
        except: st.write("Para suporte avançado: [Clique aqui](https://wa.me/5511913556631)")
    st.markdown("---")
    st.caption("AuditIA V22 - Vargem Grande do Sul - SP")

# 4. CABEÇALHO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

st.markdown("---")

# 5. INGESTÃO CUMULATIVA (PONTO 4)
new_files = st.file_uploader("📂 Arraste seus documentos, imagens ou e-mails aqui ou clique para fazer o upload:", 
                               type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({'name': f.name, 'content': f.read(), 'type': f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Provas Acumuladas para Análise:**")
    cols = st.columns(min(len(st.session_state.arquivos_acumulados), 5))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 5]: st.caption(f"✅ {f['name']}")

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: 'Analise estes arquivos em conjunto buscando fraudes'...", height=120)

# FUNÇÃO LAUDO PDF
def gerar_pdf_pericial(conteudo, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16); pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=11); pdf.ln(10)
    pdf.multi_cell(0, 8, txt=conteudo.encode('latin-1', 'replace').decode('latin-1'))
    return pdf.output(dest='S').encode('latin-1')

# 6. MOTOR DE AUDITORIA (PONTOS 1, 2 E 3)
col_ex, col_limp = st.columns([1, 1])
with col_ex:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Insira material.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo'); agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            with st.spinner("🕵️ Realizando auditoria..."):
                try:
                    instrucao = f"""Aja como AuditIA, perito forense. Data: {agora}.
                    OBRIGATÓRIO: 
                    1. Inicie com **CLASSIFICAÇÃO: [TIPO]** em negrito e maiúsculas.
                    2. Logo abaixo: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'.
                    3. Analise TODOS os arquivos acumulados em conjunto.
                    4. Se houver e-mails, foque em texto/cabeçalhos. Se houver imagens, foque em anatomia de IA.
                    5. Encerre com **RESUMO DO VEREDITO:**."""
                    
                    contexto = [instrucao]
                    for h in st.session_state.historico_pericial: contexto.append(h)
                    for f in st.session_state.arquivos_acumulados:
                        if f['name'].endswith('.eml'):
                            msg = email.message_from_bytes(f['content'], policy=policy.default)
                            contexto.append(f"E-MAIL ({f['name']}): {msg.get_body(preferencelist=('plain')).get_content()}")
                        elif f['name'].endswith('.pdf'): contexto.append({"mime_type": "application/pdf", "data": f['content']})
                        elif f['name'].lower().endswith(('jpg', 'jpeg', 'png')):
                            contexto.append(Image.open(io.BytesIO(f['content'])))
                    
                    contexto.append(pergunta_efetiva)
                    response = model.generate_content(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e: st.error(f"Erro na análise: {e}")

with col_limp:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

if st.session_state.historico_pericial:
    pdf_bytes = gerar_pdf_pericial(st.session_state.historico_pericial[-1], datetime.now().strftime("%d/%m/%Y"))
    st.download_button(label="📥 Baixar Laudo PDF", data=pdf_bytes, file_name="Laudo_AuditIA.pdf", mime="application/pdf")

# 7. GUIA MESTRE (PONTO 3 - PRESERVADO)
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia"):
    st.markdown("""### 🛡️ Inteligência Forense Profissional
    1. **Forense de Imagem**: Anatomia crítica e artefatos de IA.
    2. **e-Discovery & PST**: Auditoria de massa de e-mails corporativos.
    3. **Engenharia Social**: Desmascara phishing e manipulação.
    4. **Consistência Documental**: Auditoria de metadados.
    5. **Memória Iterativa**: Histórico para follow-up sem perda de contexto.""")
