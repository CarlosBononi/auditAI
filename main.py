import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import email
from email import policy
from datetime import datetime
import pytz
import time
import base64  # Adicionado para PDF correto

# 1. GESTÃO DE SESSÃO E MESA DE PERÍCIA
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

# 2. TERMÔMETRO DE CORES (FIX DE ASSOCIAÇÃO)
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

# 3. CSS HARMONIZADO
st.markdown("""<style>
    .stApp { background-color: #ffffff; }
    div.stButton > button { border-radius: 8px; font-weight: bold; height: 3.5em; width: 100%; transition: 0.3s; }
    div.stButton > button:first-child { background-color: #2c3e50; color: white; border: none; }
    div.stButton > button:hover { background-color: #2ecc71; color: white; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; }
</style>""", unsafe_allow_html=True)

# 4. CONEXÃO SEGURA (MODELO FIX)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash-latest')  # Versão estável sem 404
except Exception as e:
    st.error(f"Erro de Conexão: {e}")
    st.stop()

# 5. HEADER E TERMO
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

# 6. MESA DE PERÍCIA
st.markdown("---")
new_files = st.file_uploader("📂 Upload de Provas (E-mails, PDFs, Imagens):", type=["jpg", "png", "jpeg", "pdf", "eml"], accept_multiple_files=True)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({"name": f.name, "content": f.read(), "type": f.type})

if st.session_state.arquivos_acumulados:
    st.write("📦 **Mesa de Perícia (Evidências):**")
    cols = st.columns(5)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 5]:
            if f["type"].startswith("image"): 
                st.image(io.BytesIO(f["content"]), width=100)
            else: 
                st.write("📄" if "pdf" in f["type"].lower() or ".pdf" in f["name"].lower() else "📧")
            st.caption(f["name"][:10])

st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area("📝 Pergunta ao Perito:", placeholder="Analise a veracidade...", height=100)

# 7. MOTOR PERICIAL CORRIGIDO (PDF base64 + retry melhor)
c1, c2 = st.columns([1, 1])
with c1:
    if st.button("🚀 EXECUTAR PERÍCIA"):
        if not user_query and not st.session_state.arquivos_acumulados:
            st.warning("Insira material.")
        else:
            tz = pytz.timezone("America/Sao_Paulo")
            agora = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
            with st.spinner("🕵️ Realizando auditoria segregada..."):
                try:
                    tem_imagem = any(f["type"].startswith("image") for f in st.session_state.arquivos_acumulados)
                    tem_email = any(f["name"].lower().endswith(".eml") for f in st.session_state.arquivos_acumulados)

                    instrucao = f"Aja como AuditIA sênior. Hoje: {agora}. Regras: 1.Inicie CLASSIFICACAO: [TIPO]. 2.Seja técnico.\n"
                    if tem_imagem:
                        instrucao += "PROTOCOLO IMAGEM: mãos, olhos, luz, texturas. Sem EXIF: CLASSIFICACAO: ATENCAO (POSSIVEL IA).\n"
                    if tem_email:
                        instrucao += "PROTOCOLO E-MAIL: SPF, DKIM, ARC, spoofing.\n"
                    
                    contexto = [instrucao]
                    
                    # FIX PDF: base64 para multimodal correto
                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].lower().endswith(".eml"):
                            contexto.append(f"E-MAIL RAW: {f['content'].decode('utf-8', errors='ignore')[:2000]}")
                        elif "pdf" in f["type"].lower() or ".pdf" in f["name"].lower():
                            pdf_base64 = base64.b64encode(f["content"]).decode()
                            contexto.append({
                                "mime_type": "application/pdf", 
                                "data": pdf_base64
                            })
                        elif f["type"].startswith("image"):
                            contexto.append(Image.open(io.BytesIO(f["content"])).convert("RGB"))
                    
                    contexto.append(f"PERGUNTA: {user_query}")
                    
                    # RETRY MELHOR PARA 429 E TIMEOUT
                    for attempt in range(5):
                        try:
                            res = model.generate_content(
                                contexto, 
                                request_options={"timeout": 300.0}
                            )
                            st.session_state.historico_pericial.append(res.text)
                            st.rerun()
                            break
                        except Exception as e:
                            if "429" in str(e) or "quota" in str(e).lower():
                                time.sleep(3 * (attempt + 1))
                            elif "404" in str(e):
                                st.error("Modelo indisponível. Use quota maior.")
                            else:
                                raise e
                except Exception as e: 
                    st.error(f"Falha técnica: {e}")

with c2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.rerun()

# 8. CENTRAL DE AJUDA
st.markdown("---")
with st.expander("📖 Central de Ajuda AuditIA - Conhecimento Técnico"):
    st.markdown("### 🧬 Os 7 Pilares\n1. Análise Documental. 2. Detecção de IA (12 marcadores). 3. e-Discovery. 4. Engenharia Social. 5. Física da Luz. 6. Ponzi Detection. 7. Consistência de Metadados.")

st.caption(f"AuditIA © {datetime.now().year} - Vargem Grande do Sul - SP | Versão 2.2 FIX PDF/429")
