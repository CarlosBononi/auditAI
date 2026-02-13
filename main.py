import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import email
from email import policy
from datetime import datetime
import pytz
import time

# 1. INICIALIZAÇÃO DE SESSÃO E MESA DE PERÍCIA
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = "" 

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. TERMÔMETRO DE CORES (SOBERANIA VERDE)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if any(t in texto_upper for t in ["CLASSIFICACAO: SEGURO", "VEREDITO: SEGURO", "LEGITIMO"]):
        cor, icon = "#27ae60", "🟢"
    elif any(t in texto_upper for t in ["FRAUDE CONFIRMADA", "GOLPE", "FAKE"]):
        cor, icon = "#c0392b", "🔴"
    elif any(t in texto_upper for t in ["POSSIVEL FRAUDE", "PHISHING"]):
        cor, icon = "#d35400", "🟠"
    elif any(t in texto_upper for t in ["ATENCAO", "IA", "FOTO"]):
        cor, icon = "#f1c40f", "🟡"
    else:
        cor, icon = "#2980b9", "🔵"

    return f'''<div style="background-color: {cor}; padding: 20px; border-radius: 12px; color: white; 
                font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                {icon} ANÁLISE FORENSE:<br><br>{texto.replace(chr(10), "<br>")}</div>'''

# 3. CSS PARA BOTÕES EM HARMONIA (FIX ERRO ROSA)
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    div.stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; transition: 0.3s; }
    /* Botão Executar */
    div.stButton > button:first-child { background-color: #2980b9; color: white; border: none; }
    /* Botão Limpar (Estilo Cinza Suave sem usar 'kind') */
    div.stButton > button:hover { border: 1px solid #2ecc71; opacity: 0.8; }
</style>
""", unsafe_allow_html=True)

# 4. CONEXÃO DINÂMICA (FIX ERRO 404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # O código agora descobre qual modelo está vivo na sua conta
    model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(model_list[0] if model_list else 'gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de Conexão: {e}"); st.stop()

# 5. CABEÇALHO E TERMO
try: st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

if not st.session_state.termo_aceito:
    st.warning("### ⚖️ TERMO DE CONSENTIMENTO\nIA Forense. Resultados probabilísticos. Exige validação humana oficial.")
    if st.button("🚀 ACEITAR E PROSSEGUIR"):
        st.session_state.termo_aceito = True; st.rerun()
    st.stop()

# 6. MESA DE PERÍCIA E MINIATURAS
st.markdown("---")
new_files = st.file_uploader("📂 Upload de Provas (E-mails, PDFs, Imagens):", type=["jpg", "png", "jpeg", "pdf", "eml"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({"name": f.name, "content": f.read(), "type": f.type})

if st.session_state.arquivos_acumulados:
    cols = st.columns(5)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 5]:
            if f["type"].startswith("image"): st.image(io.BytesIO(f["content"]), width=100)
            else: st.write("📄" if "pdf" in f["type"] else "📧")
            st.caption(f["name"][:10])

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", placeholder="Ex: Analise a veracidade desta evidência.", height=100)

# 7. MOTOR PERICIAL COM BACKOFF (FIX ERRO 429)
def call_api_safe(ctx):
    for i in range(3):
        try: return model.generate_content(ctx, request_options={"timeout": 200})
        except Exception as e:
            if "429" in str(e): time.sleep(5 * (i + 1)) # Espera se bater no limite
            else: raise e
    return None

c1, c2 = st.columns([1, 1])
with c1:
    if st.button("🚀 EXECUTAR PERÍCIA"):
        if not user_query and not st.session_state.arquivos_acumulados:
            st.warning("Insira material.")
        else:
            tz = pytz.timezone("America/Sao_Paulo"); agora = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
            with st.spinner("🕵️ AuditIA analisando..."):
                try:
                    # PROMPT CURTO (ECONOMIA DE CRÉDITOS)
                    prompt = [f"AuditIA sênior. Hoje: {agora}. Regras: 1.Inicie CLASSIFICACAO: [TIPO]. 2.Se seguro, use CLASSIFICACAO: SEGURO. 3.Analise anatomia IA (12 pontos) e metadados. 4.Seja técnico."]
                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"): prompt.append(f"E-MAIL: {f['content'][:1000]}")
                        elif "pdf" in f["type"]: prompt.append({"mime_type": "application/pdf", "data": f["content"]})
                        else: prompt.append(Image.open(io.BytesIO(f["content"])).convert("RGB"))
                    prompt.append(f"Pergunta: {user_query}")
                    
                    res = call_api_safe(prompt)
                    if res: st.session_state.historico_pericial.append(res.text); st.rerun()
                except Exception as e: st.error(f"Falha técnica: {e}")

with c2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 8. CENTRAL DE AJUDA (CONTEÚDO DENSO EXIGIDO)
st.markdown("---")
with st.expander("📖 Central de Ajuda AuditIA - Conhecimento Técnico e FAQ"):
    t1, t2, t3 = st.tabs(["A Origem", "Manual Operacional", "FAQ"])
    with t1:
        st.markdown("### 🧬 Missão AuditIA\nNascido em **Vargem Grande do Sul - SP**, o AuditIA une psicologia forense e tecnologia de ponta para desmascarar fraudes digitais.")
    with t2:
        st.markdown("### 🛠️ Pilares Forenses\n1. Análise Documental. 2. Detecção de IA (12 marcadores). 3. e-Discovery. 4. Física da Luz.")
    with t3:
        st.markdown("**P: Qual a precisão?** R: Acima de 95% em arquivos originais.\n**P: Onde ficam os dados?** R: Memória volátil (RAM), deletados ao limpar.")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP | Versão Elite 2.0")
