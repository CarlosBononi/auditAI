import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime
import pytz
import re

# SESSION STATE
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligencia Pericial Senior", page_icon="👁️", layout="centered")

# CORES
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    if any(term in texto_upper for term in ["FRAUDE CONFIRMADA", "CRIME", "GOLPE", "SCAM"]):
        cor = "#ff4b4b"
    elif any(term in texto_upper for term in ["POSSÍVEL FRAUDE", "POSSIVEL FRAUDE", "PHISHING"]):
        cor = "#ffa500"
    elif any(term in texto_upper for term in ["ATENÇÃO", "ATENCAO", "IMAGEM", "FOTO", "IA", "SINTETICO"]):
        cor = "#f1c40f"
    elif any(term in texto_upper for term in ["SEGURO", "LEGITIMO", "AUTENTICIDADE"]):
        cor = "#2ecc71"
    else:
        cor = "#3498db"

    return f'<div style="background-color: {cor}; padding: 20px; border-radius: 10px; color: white; margin: 10px 0;">{texto.replace(chr(10), "<br>")}</div>'

# CSS
st.markdown('''
<style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child {
        background-color: #4a4a4a; color: white; border: none;
        border-radius: 10px; font-weight: bold; height: 3.5em; width: 100%;
    }
    div.stButton > button:hover {
        background-color: #59ea63; color: black;
    }
</style>
''', unsafe_allow_html=True)

# GEMINI - COM FIX CRÍTICO
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

        if modelos_disp:
            modelo_nome = modelos_disp[0]
            if modelo_nome.startswith('models/'):
                modelo_nome = modelo_nome.replace('models/', '')

            model = genai.GenerativeModel(modelo_nome)
        else:
            st.error("Nenhum modelo Gemini disponivel")
            st.stop()

except Exception as e:
    st.error(f"Erro de conexao: {e}")
    st.stop()

# HEADER
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("AuditIA - Inteligencia Pericial Senior")

st.warning("TERMO: Ferramenta de apoio. Nao substitui pericia oficial.")
st.markdown("---")

# UPLOAD
st.header("Upload de Provas")

new_files = st.file_uploader(
    "Arraste arquivos (JPG, PNG, PDF, EML)",
    type=["jpg", "png", "jpeg", "pdf", "eml"],
    accept_multiple_files=True
)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({
                "name": f.name,
                "content": f.read(),
                "type": f.type
            })

# MINIATURAS
if st.session_state.arquivos_acumulados:
    st.write("Mesa de Pericia:")
    cols = st.columns(4)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 4]:
            if f["type"].startswith("image"):
                try:
                    st.image(Image.open(io.BytesIO(f["content"])), width=150)
                except:
                    st.write("🖼️")
            elif f["type"] == "application/pdf":
                st.write("📄")
            else:
                st.write("📧")
            st.caption(f["name"])

st.markdown("---")

# HISTORICO
st.subheader("Linha de Investigacao")

if not st.session_state.historico_pericial:
    st.info("O historico aparecera aqui")
else:
    for idx, bloco in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"Analise #{idx}", expanded=(idx == len(st.session_state.historico_pericial))):
            st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

st.markdown("---")

# PERGUNTA - SEM ASPAS TRIPLAS NO PLACEHOLDER
st.subheader("Consulta ao Perito")

user_query = st.text_area(
    "Digite sua pergunta tecnica:",
    key="campo_pergunta",
    placeholder="Ex: Esta foto e real? Analise textura de pele e maos.",
    height=120
)

# FUNCOES
def gerar_pdf(conteudo, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "LAUDO PERICIAL - AUDITIA", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Data: {data}", ln=True, align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 9)
    texto = conteudo.encode('latin-1', 'replace').decode('latin-1')
    texto = re.sub(r'\*\*', '', texto)
    pdf.multi_cell(0, 6, texto)
    return pdf.output(dest='S').encode('latin-1')

# BOTOES
col1, col2 = st.columns(2)

with col1:
    if st.button("EXECUTAR PERICIA", on_click=processar_pericia, type="primary"):
        pergunta = st.session_state.get("pergunta_ativa", "")

        if not pergunta and not st.session_state.arquivos_acumulados:
            st.warning("Insira pergunta ou arquivos")
        else:
            agora = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

            with st.spinner("Analisando..."):
                try:
                    instrucao = f'''Perito forense. Hoje: {agora}.

PROTOCOLO V16:
1. IMAGENS: Analise anatomia (dedos, olhos), fisica da luz, textura de pele
2. E-MAILS: Verifique phishing, SPF, DKIM
3. RESPOSTA: Inicie com CLASSIFICACAO: [FRAUDE CONFIRMADA/POSSIVEL FRAUDE/ATENCAO/SEGURO]

Pergunta: {pergunta}'''

                    contexto = [instrucao]

                    for h in st.session_state.historico_pericial[-2:]:
                        contexto.append(f"[HISTORICO]: {h[:300]}")

                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"):
                            try:
                                msg = email.message_from_bytes(f["content"], policy=policy.default)
                                corpo = msg.get_body(preference=['plain']).get_content()
                                contexto.append(f"EMAIL: {corpo[:1000]}")
                            except:
                                pass
                        elif f["type"] == "application/pdf":
                            contexto.append({"mime_type": "application/pdf", "data": f["content"]})
                        elif f["type"].startswith("image"):
                            try:
                                img = Image.open(io.BytesIO(f["content"])).convert("RGB")
                                contexto.append(img)
                            except:
                                pass

                    contexto.append(pergunta)

                    response = model.generate_content(contexto, request_options={"timeout": 120})

                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro: {str(e)}")

with col2:
    if st.button("LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.session_state.pergunta_ativa = ""
        st.rerun()

# PDF
if st.session_state.historico_pericial:
    st.markdown("---")
    data = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    pdf = gerar_pdf(st.session_state.historico_pericial[-1], data)

    st.download_button(
        "Baixar Laudo PDF",
        pdf,
        f"Laudo_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        "application/pdf"
    )

st.markdown("---")

# FAQ SIMPLIFICADO
with st.expander("Central de Ajuda"):
    st.markdown('''
### Como usar

1. **Upload**: Arraste ate 5 arquivos (imagens, PDFs, emails)
2. **Pergunta**: Seja especifico (ex: "Esta foto e deepfake?")
3. **Analise**: Clique em "Executar Pericia"
4. **PDF**: Baixe o laudo antes de limpar

### Classificacoes

- 🟢 SEGURO: Autentico
- 🟡 ATENCAO: Suspeita moderada
- 🟠 POSSIVEL FRAUDE: Inconsistencias graves
- 🔴 FRAUDE CONFIRMADA: Manipulacao irrefutavel

### Limites

- Arquivos: ate 200MB cada
- PDFs: ate 1000 paginas
- Timeout: 2 minutos

### Privacidade

Nenhum dado e armazenado. Tudo e processado em memoria e destruido ao limpar.
''')

st.markdown("---")
st.caption("AuditIA v2.0 | Vargem Grande do Sul - SP")
st.caption("Ferramenta de apoio - Nao substitui pericia oficial")
