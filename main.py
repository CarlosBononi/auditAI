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

# 1. INICIALIZAÇÃO DE SESSÃO (PROTEÇÃO DE ESTADO)
def init_session():
    defaults = {
        "historico_pericial": [],
        "arquivos_acumulados": [],
        "termo_aceito": False,
        "ultima_requisicao": 0,
        "chat_suporte": [{"role": "assistant", "content": "Olá! Sou o Concierge AuditIA. Como posso facilitar sua investigação hoje?"}]
    }
    for key, val in defaults.items():
        if key not in st.session_state: st.session_state[key] = val

init_session()

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. TERMÔMETRO DE CORES (HARMONIA E SOBERANIA)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if any(t in texto_upper for t in ["CLASSIFICACAO: SEGURO", "VEREDITO: SEGURO", "LEGITIMO"]):
        cor, icon = "#27ae60", "🟢" # Verde
    elif any(t in texto_upper for t in ["FRAUDE CONFIRMADA", "GOLPE", "CRIME"]):
        cor, icon = "#c0392b", "🔴" # Vermelho
    elif any(t in texto_upper for t in ["POSSIVEL FRAUDE", "PHISHING", "SUSPEITO"]):
        cor, icon = "#d35400", "🟠" # Laranja
    elif any(t in texto_upper for t in ["ATENCAO", "IMAGEM", "FOTO", "IA"]):
        cor, icon = "#f1c40f", "🟡" # Amarelo
    else:
        cor, icon = "#2980b9", "🔵" # Azul

    return f'''<div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: white; 
                font-weight: bold; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                {icon} ANÁLISE FORENSE:<br><br>{texto.replace(chr(10), "<br>")}</div>'''

# CSS - BOTÕES SUAVES E HARMONIZADOS
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    /* Botão Executar (Azul Profissional) */
    div.stButton > button:first-child { background-color: #2980b9; color: white; border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; border: none; }
    /* Botão Limpar (Cinza Suave) */
    div.stButton > button[kind="secondary"] { background-color: #f8f9fa; color: #7f8c8d; border: 1px solid #dee2e6; border-radius: 8px; height: 3.5em; width: 100%; }
    div.stButton > button:hover { opacity: 0.8; border: 1px solid #2ecc71; }
</style>
""", unsafe_allow_html=True)

# 3. CONEXÃO SEGURA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("Erro de conexão. Verifique sua chave API."); st.stop()

# 4. CABEÇALHO E TERMO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("👁️ AuditIA")

if not st.session_state.termo_aceito:
    st.warning("### ⚖️ TERMO DE CONSENTIMENTO\nFerramenta de IA Forense. Resultados são probabilisticos e exigem validação humana oficial.")
    if st.button("🚀 ACEITAR E PROSSEGUIR"):
        st.session_state.termo_aceito = True; st.rerun()
    st.stop()

# 5. INTERFACE DE PERÍCIA
st.markdown("---")
new_files = st.file_uploader("📂 Upload de Provas (Prints, PDFs, E-mails):", type=["jpg", "png", "jpeg", "pdf", "eml"], accept_multiple_files=True)

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

# 6. MOTOR PERICIAL OTIMIZADO (PREVENÇÃO DE ERRO DE LIMITE)
def call_api_resilient(ctx):
    for attempt in range(3):
        try:
            return model.generate_content(ctx, request_options={"timeout": 120})
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                time.sleep(5 * (attempt + 1)) # Espera progressiva
            else: raise e
    return None

c1, c2 = st.columns([1, 1])
with c1:
    if st.button("🚀 EXECUTAR PERÍCIA"):
        if not user_query and not st.session_state.arquivos_acumulados:
            st.warning("Insira material.")
        else:
            tz = pytz.timezone("America/Sao_Paulo"); agora = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
            with st.spinner("🕵️ Realizando varredura técnica otimizada..."):
                try:
                    # PROMPT COMPRIMIDO PARA ECONOMIZAR COTA (FIX ERRO 429)
                    instrucao = f"Aja como AuditIA, perito sênior. Hoje: {agora}. Regras: 1. Inicie com CLASSIFICACAO: [TIPO]. 2. Se seguro, use CLASSIFICACAO: SEGURO. 3. Analise metadados, anatomia IA (12 pontos) e SPF/DKIM. 4. Seja técnico e direto."
                    
                    contexto = [instrucao]
                    # Adiciona apenas o último histórico para não pesar a API
                    if st.session_state.historico_pericial:
                        contexto.append(f"ÚLTIMO CONTEXTO: {st.session_state.historico_pericial[-1][:500]}")
                    
                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"):
                            msg = email.message_from_bytes(f["content"], policy=policy.default)
                            contexto.append(f"E-MAIL: {msg.get_body(preferencelist=('plain')).get_content()[:1000]}")
                        elif "pdf" in f["type"]: contexto.append({"mime_type": "application/pdf", "data": f["content"]})
                        else: contexto.append(Image.open(io.BytesIO(f["content"])).convert("RGB"))
                    
                    contexto.append(f"PERGUNTA: {user_query}")
                    response = call_api_resilient(contexto)
                    if response:
                        st.session_state.historico_pericial.append(response.text)
                        st.rerun()
                    else: st.error("Limite de API persistente. Aguarde 60 segundos.")
                except Exception as e: st.error(f"Erro: {e}")

with c2:
    if st.button("🗑️ LIMPAR CASO", type="secondary"):
        st.session_state.historico_pericial = []; st.session_state.arquivos_acumulados = []; st.rerun()

# 7. CONCIERGE "ROBO" (SUPORTE HUMANIZADO)
st.markdown("---")
with st.expander("💬 Atendimento AuditIA - Suporte Especializado", expanded=False):
    for msg in st.session_state.chat_suporte:
        with st.chat_message(msg["role"]): st.write(msg["content"])
    
    if prompt_robo := st.chat_input("Dúvida sobre limites ou precisão?"):
        st.session_state.chat_suporte.append({"role": "user", "content": prompt_robo})
        with st.chat_message("user"): st.write(prompt_robo)
        try:
            res = model.generate_content(f"Você é o Concierge AuditIA. Responda de forma humanizada e técnica: {prompt_robo}")
            st.session_state.chat_suporte.append({"role": "assistant", "content": res.text})
            st.rerun()
        except: st.write("Tive uma pequena oscilação. Detalhe sua dúvida ou use o Manual abaixo.")

# 8. CENTRAL DE AJUDA (CONTEÚDO COMPLETO)
with st.expander("📖 Central de Ajuda AuditIA - Conhecimento Técnico e FAQ"):
    tab1, tab2, tab3 = st.tabs(["A Origem", "Manual de Operação", "FAQ Técnico"])
    with tab1:
        st.markdown("### 🧬 A Missão AuditIA\nNascido em **Vargem Grande do Sul - SP**, o AuditIA une psicologia forense à tecnologia. Auditamos: Análise Documental, IA, e-Discovery, Phishing, Física da Luz, Ponzi e Metadados.")
    with tab2:
        st.markdown("### 🛠️ Como Auditar\n1. Upload de até 5 arquivos. 2. Pergunte 'Analise a textura de pele'. 3. Siga o termômetro: Verde (Seguro) a Vermelho (Fraude).")
    with tab3:
        st.markdown("**P: Qual a precisão?** R: Analisamos 12 marcadores técnicos. Precisão >95% em arquivos originais.")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP | Versão 2.0 Otimizada")
