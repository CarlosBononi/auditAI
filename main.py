import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import email
from email import policy
from datetime import datetime
import pytz
import time
import os

# Inicialização de sessão
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "arquivos_gemini" not in st.session_state:
    st.session_state.arquivos_gemini = []  # IDs de arquivos uploadados no Gemini
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# Estilo termômetro de cores
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

# CSS
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    div.stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; transition: 0.3s; }
    div.stButton > button:first-child { background-color: #2c3e50; color: white; border: none; }
    div.stButton > button:hover { background-color: #2ecc71; color: white; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; }
</style>""", unsafe_allow_html=True)

# Conexão segura
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de Conexão API: Verifique GOOGLE_API_KEY em Secrets. Detalhes: {e}")
    st.stop()

# Header e Termo
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("👁️ AuditIA")

if not st.session_state.termo_aceito:
    st.warning("### ⚖️ TERMO DE CONSENTIMENTO\nIA Forense. Resultados probabilísticos sujeitos a erro. Validação humana obrigatória.")
    if st.button("🚀 ACEITAR E PROSSEGUIR"):
        st.session_state.termo_aceito = True
        st.rerun()
    st.stop()

# Mesa de Perícia
st.markdown("---")
new_files = st.file_uploader("📂 Upload de Provas (E-mails, PDFs, Imagens):", type=["jpg", "png", "jpeg", "pdf", "eml"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            content = f.read()
            st.session_state.arquivos_acumulados.append({"name": f.name, "content": content, "type": f.type})
            # Upload imediato para Gemini se PDF ou EML
            if f.name.lower().endswith(('.pdf', '.eml')):
                try:
                    uploaded_file = genai.upload_file(path=f.name, content=content)
                    st.session_state.arquivos_gemini.append(uploaded_file.name)
                    st.success(f"✅ {f.name} enviado para análise Gemini")
                except Exception as e:
                    st.warning(f"⚠️ Erro upload {f.name}: {e}")

# Visualizar arquivos
if st.session_state.arquivos_acumulados:
    st.write("📦 **Mesa de Perícia (Evidências):**")
    cols = st.columns(5)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 5]:
            if f["type"].startswith("image"):
                st.image(io.BytesIO(f["content"]), width=100)
            else:
                st.write("📄" if "pdf" in f["type"] or f["name"].lower().endswith('.pdf') else "📧")
            st.caption(f["name"][:15])

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

st.session_state.campo_pergunta = st.text_area("📝 Pergunta ao Perito:", value=st.session_state.pergunta_ativa, height=100, placeholder="Analise a veracidade...")

# Botões de ação
c1, c2 = st.columns([1, 1])
with c1:
    if st.button("🚀 EXECUTAR PERÍCIA"):
        if not st.session_state.campo_pergunta.strip() and not st.session_state.arquivos_acumulados:
            st.warning("❌ Insira pergunta ou arquivo.")
        else:
            tz = pytz.timezone("America/Sao_Paulo")
            agora = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
            with st.spinner("🕵️ Realizando auditoria forense..."):
                try:
                    tem_imagem = any(f["type"].startswith("image") for f in st.session_state.arquivos_acumulados)
                    tem_email = any(f["name"].lower().endswith('.eml') for f in st.session_state.arquivos_acumulados)

                    instrucao = f"Aja como AuditIA sênior. Hoje: {agora}. Regras: 1. Inicie com CLASSIFICACAO: [TIPO]. 2. Seja técnico e objetivo.\n"
                    if tem_imagem:
                        instrucao += "PROTOCOLO IMAGEM: Analise mãos, olhos, luz, texturas, EXIF. Sem EXIF: CLASSIFICACAO: ATENCAO (POSSIVEL IA).\n"
                    if tem_email:
                        instrucao += "PROTOCOLO E-MAIL: SPF, DKIM, ARC, spoofing. Ignore imagens.\n"

                    contexto = [instrucao, st.session_state.campo_pergunta]

                    # Adicionar arquivos Gemini (PDF/EML)
                    if st.session_state.arquivos_gemini:
                        contexto.extend([genai.get_file(id) for id in st.session_state.arquivos_gemini])

                    # Adicionar imagens PIL
                    for f in st.session_state.arquivos_acumulados:
                        if f["type"].startswith("image"):
                            contexto.append(Image.open(io.BytesIO(f["content"])))

                    # Geração com retry robusto para 429
                    for attempt in range(5):
                        try:
                            response = model.generate_content(
                                contexto,
                                request_options={"timeout": 300.0}
                            )
                            st.session_state.historico_pericial.append(response.text)
                            st.session_state.pergunta_ativa = ""
                            st.rerun()
                            break
                        except Exception as e:
                            if "429" in str(e) or "quota" in str(e).lower():
                                sleep_time = (2 ** attempt) + random.uniform(0, 1)
                                time.sleep(sleep_time)
                                if attempt == 4:
                                    st.error("❌ Quota excedida. Verifique https://aistudio.google.com/app/apikey")
                            else:
                                st.error(f"Erro pericial: {e}")
                                break
                except Exception as e:
                    st.error(f"Falha geral: {e}")

with c2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.session_state.arquivos_gemini = []
        st.session_state.pergunta_ativa = ""
        st.rerun()

# Central de Ajuda
st.markdown("---")
with st.expander("📖 Central de Ajuda AuditIA"):
    st.markdown("""
### 🧬 Os 7 Pilares
- 1. Análise Documental
- 2. Detecção de IA (12 marcadores)
- 3. e-Discovery
- 4. Engenharia Social
- 5. Física da Luz
- 6. Ponzi Detection
- 7. Consistência de Metadados
    """)

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP | Versão 2.2 Rigor Forense (Corrigida)")
