import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import email
from email import policy
from datetime import datetime
import pytz
import time
import fitz  # PyMuPDF: pip install pymupdf

# Inicialização de sessão (limpa arquivos_gemini desnecessário)
if "historico_pericial" not in st.session_state: st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state: st.session_state.arquivos_acumulados = []
if "termo_aceito" not in st.session_state: st.session_state.termo_aceito = False
if "pergunta_ativa" not in st.session_state: st.session_state.pergunta_ativa = ""

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "CLASSIFICACAO: SEGURO" in texto_upper: cor = "#27ae60"
    elif "FRAUDE CONFIRMADA" in texto_upper: cor = "#c0392b"
    elif "POSSIVEL FRAUDE" in texto_upper: cor = "#d35400"
    elif "ATENCAO" in texto_upper or "IA" in texto_upper: cor = "#f1c40f"
    else: cor = "#2980b9"
    return f'''<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: white; 
                font-weight: bold; margin-bottom: 20px; border-left: 10px solid rgba(0,0,0,0.2);">
                {texto.replace(chr(10), "<br>")}</div>'''

st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    div.stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; transition: 0.3s; }
    div.stButton > button:first-child { background-color: #2c3e50; color: white; border: none; }
    div.stButton > button:hover { background-color: #2ecc71; color: white; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; }
</style>""", unsafe_allow_html=True)

# Conexão
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Modelo estável sem 404
except Exception as e:
    st.error(f"Erro API: {e}. Verifique key e quota.")
    st.stop()

# Header/Termo
try: st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

if not st.session_state.termo_aceito:
    st.warning("### ⚖️ TERMO DE CONSENTIMENTO\nIA Forense probabilística. Validação humana obrigatória.")
    if st.button("🚀 ACEITAR"): st.session_state.termo_aceito = True; st.rerun()
    st.stop()

st.markdown("---")
new_files = st.file_uploader("📂 Upload Provas:", type=["jpg", "png", "jpeg", "pdf", "eml"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            content = f.read()
            st.session_state.arquivos_acumulados.append({"name": f.name, "content": content, "type": f.type})
            st.success(f"✅ {f.name} carregado!")

# Visualizar Mesa
if st.session_state.arquivos_acumulados:
    st.write("📦 **Mesa de Perícia:**")
    cols = st.columns(5)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 5]:
            if f["type"].startswith("image"): st.image(io.BytesIO(f["content"]), width=100, caption=f["name"])
            else: st.write("📄" if ".pdf" in f["name"].lower() else "📧", caption=f["name"][:15])

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

st.session_state.campo_pergunta = st.text_area("📝 Pergunta:", value=st.session_state.pergunta_ativa, height=100)

c1, c2 = st.columns([1,1])
with c1:
    if st.button("🚀 EXECUTAR PERÍCIA"):
        if not st.session_state.campo_pergunta.strip() and not st.session_state.arquivos_acumulados:
            st.warning("Pergunta ou arquivo obrigatório.")
        else:
            tz = pytz.timezone("America/Sao_Paulo")
            agora = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
            with st.spinner("🔍 Auditoria..."):
                try:
                    tem_imagem = any(f["type"].startswith("image") for f in st.session_state.arquivos_acumulados)
                    tem_pdf = any(".pdf" in f["name"].lower() for f in st.session_state.arquivos_acumulados)
                    tem_email = any(".eml" in f["name"].lower() for f in st.session_state.arquivos_acumulados)

                    instrucao = f"AuditIA sênior. {agora}. Inicie CLASSIFICACAO: [TIPO]. Técnico.\n"
                    if tem_imagem: instrucao += "IMAGEM: mãos, olhos, luz, EXIF. Sem EXIF: ATENCAO (IA).\n"
                    if tem_pdf: instrucao += "PDF: metadados, inconsistências, fraudes.\n"
                    if tem_email: instrucao += "EML: SPF/DKIM/ARC/spoofing.\n"

                    contexto = [instrucao, st.session_state.campo_pergunta]

                    # Processar arquivos para contexto
                    for f in st.session_state.arquivos_acumulados:
                        nome = f["name"].lower()
                        if f["type"].startswith("image"):
                            contexto.append(Image.open(io.BytesIO(f["content"])))
                        elif ".pdf" in nome:
                            doc = fitz.open(stream=f["content"], filetype="pdf")
                            texto_pdf = ""
                            for page in doc: texto_pdf += page.get_text()
                            contexto.append(f"PDF [{f['name']}]: {texto_pdf[:4000]}...")  # Limite token
                        elif ".eml" in nome:
                            msg = email.message_from_bytes(f["content"], policy=policy.default)
                            texto_eml = msg.as_string()[:4000]
                            contexto.append(f"EML RAW [{f['name']}]: {texto_eml}")

                    # Retry robusto
                    for attempt in range(5):
                        try:
                            res = model.generate_content(contexto, request_options={"timeout": 300})
                            st.session_state.historico_pericial.append(res.text)
                            st.session_state.pergunta_ativa = ""
                            st.rerun()
                            break
                        except Exception as e:
                            if "429" in str(e).upper() or "quota" in str(e).lower():
                                time.sleep(2 ** attempt)
                            else:
                                st.error(f"Erro: {e}")
                                break

                except Exception as e:
                    st.error(f"Falha: {e}")

with c2:
    if st.button("🗑️ LIMPAR"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.session_state.pergunta_ativa = ""
        st.rerun()

st.markdown("---")
with st.expander("📖 Ajuda"):
    st.markdown("- **Instale**: `pip install streamlit google-generativeai pymupdf`\n- 7 Pilares: Documental, IA Detect, e-Discovery, etc.")

st.caption(f"AuditIA © 2026 - Vargem Grande do Sul-SP | V2.3 Perfeita")
