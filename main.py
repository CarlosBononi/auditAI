import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz
import re
import time

# 1. GESTÃO DE SESSÃO
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False
if "ultima_requisicao" not in st.session_state:
    st.session_state.ultima_requisicao = 0

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. TERMÔMETRO DE CORES COM HIERARQUIA SOBERANA
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "GOLPE", "CRIME", "VEREDITO: FRAUDE"]):
        cor = "#ff4b4b" # VERMELHO
    elif any(term in texto_upper for term in ["POSSÍVEL FRAUDE", "PHISHING", "SUSPEITO"]):
        cor = "#ffa500" # LARANJA
    elif any(term in texto_upper for term in ["ATENÇÃO", "IMAGEM", "FOTO", "IA"]):
        cor = "#f1c40f" # AMARELO
    elif any(term in texto_upper for term in ["SEGURO", "LEGÍTIMO", "AUTÊNTICO"]):
        cor = "#2ecc71" # VERDE
    else:
        cor = "#3498db" # AZUL

    return f"""<div style="background-color: {cor}; padding: 25px; border-radius: 12px; 
                color: white; font-weight: bold; margin: 15px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                {texto.replace(chr(10), "<br>")}
            </div>"""

# 3. CSS HARMONIZADO
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child {
        background-color: #2c3e50; color: white; border: none;
        border-radius: 10px; font-weight: bold; height: 3.5em; width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover { background-color: #2ecc71; color: white; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# 4. CONEXÃO DINÂMICA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(model_list[0] if model_list else 'gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro de conexão: {e}"); st.stop()

# 5. HEADER E TERMO
try: st.image(Image.open("Logo_AI_1.png"), width=500)
except: st.title("👁️ AuditIA")

if not st.session_state.termo_aceito:
    st.warning("### ⚖️ TERMO DE CONSENTIMENTO\nIA Forense. Resultados probabilísticos. Exige validação humana oficial.")
    if st.button("🚀 ACEITAR E PROSSEGUIR"):
        st.session_state.termo_aceito = True; st.rerun()
    st.stop()

# 6. MESA DE PERÍCIA
st.markdown("---")
st.header("📂 Upload de Provas Forenses")
new_files = st.file_uploader("Arraste até 5 arquivos:", type=["jpg", "png", "jpeg", "pdf", "eml"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({"name": f.name, "content": f.read(), "type": f.type})

if st.session_state.arquivos_acumulados:
    cols = st.columns(4)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 4]:
            if f["type"].startswith("image"): st.image(io.BytesIO(f["content"]), width=120)
            else: st.write("📄" if "pdf" in f["type"] else "📧")
            st.caption(f["name"][:15])

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", key="campo_pergunta", placeholder="Ex: Analise a veracidade desta evidência.", height=120)

# 7. MOTOR PERICIAL COM BLINDAGEM ANTI-QUOTA
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🔬 EXECUTAR PERÍCIA"):
        if not user_query and not st.session_state.arquivos_acumulados:
            st.warning("Insira material para análise.")
        else:
            tz_br = pytz.timezone("America/Sao_Paulo"); agora = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
            with st.spinner("🕵️ Realizando auditoria técnica profunda..."):
                try:
                    # PROMPT REFORÇADO PARA DETECÇÃO DE FRAUDE EM E-MAILS
                    instrucao = f"""Aja como AuditIA, perito sênior. Hoje: {agora}.
                    PROTOCOLO V16:
                    1. E-MAILS: Analise Display Name Spoofing, cabeçalhos ARC e urgência artificial. Se o remetente parecer legítimo mas o conteúdo for suspeito, classifique como POSSÍVEL FRAUDE.
                    2. IMAGENS: Scrutínio de 12 pontos anatômicos e ruído digital.
                    3. ESTRUTURA: Inicie com 'VEREDITO: [CLASSIFICAÇÃO]'. Seja técnico e cético.
                    4. Se for fraude confirmada, use obrigatoriamente 'CLASSIFICACAO: FRAUDE CONFIRMADA'."""
                    
                    contexto = [instrucao]
                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"):
                            msg = email.message_from_bytes(f["content"], policy=policy.default)
                            contexto.append(f"DADOS BRUTOS DO E-MAIL: {f['content'].decode('utf-8', errors='ignore')[:2000]}")
                        elif "pdf" in f["type"]: contexto.append({"mime_type": "application/pdf", "data": f["content"]})
                        else: contexto.append(Image.open(io.BytesIO(f["content"])).convert("RGB"))
                    
                    contexto.append(f"PERGUNTA: {user_query}")
                    
                    # SISTEMA DE RETENTATIVA (BACKOFF) CONTRA ERRO 429
                    def call_api(ctx, retries=3):
                        for i in range(retries):
                            try: return model.generate_content(ctx, request_options={"timeout": 150})
                            except Exception as e:
                                if "429" in str(e) and i < retries - 1: time.sleep(10 * (i + 1))
                                else: raise e
                    
                    response = call_api(contexto)
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha técnica: {e}. Tente reduzir o número de arquivos.")

with col2:
    if st.button("🗑️ LIMPAR CASO COMPLETO"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 8. CENTRAL DE AJUDA
st.markdown("---")
with st.expander("📖 CENTRAL DE AJUDA AUDITIA"):
    st.markdown("""
    ### 🧬 Missão AuditIA
    Nascido em **Vargem Grande do Sul - SP**, o AuditIA une psicologia forense e tecnologia de ponta.
    - **Capacidades**: Análise Documental, Detecção de IA, e-Discovery, Engenharia Social.
    - **Privacidade**: Processamento em memória volátil. LGPD Compliant.
    """)

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP | Versão 2.0 COMPLETA")
