import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

st.set_page_config(
    page_title="AuditIA - Inteligencia Pericial Senior",
    page_icon="👁️",
    layout="centered"
)

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception as e:
    st.error(f"Erro ao configurar API: {str(e)}")
    st.stop()

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    modelo_nome = 'gemini-1.5-flash'
except Exception as e:
    try:
        modelos = genai.list_models()
        modelo_encontrado = False

        for m in modelos:
            if 'generateContent' in m.supported_generation_methods:
                nome = m.name
                if nome.startswith('models/'):
                    nome = nome.replace('models/', '')

                try:
                    model = genai.GenerativeModel(nome)
                    modelo_nome = nome
                    modelo_encontrado = True
                    break
                except:
                    continue

        if not modelo_encontrado:
            st.error("Nenhum modelo disponivel")
            st.stop()
    except Exception as e2:
        st.error(f"Erro: {str(e2)}")
        st.stop()

if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    if "FRAUDE CONFIRMADA" in texto_upper or "PHISHING" in texto_upper:
        cor = "#ff4b4b"
    elif "POSSIVEL FRAUDE" in texto_upper:
        cor = "#ffa500"
    elif "ATENCAO" in texto_upper or "IA" in texto_upper:
        cor = "#f1c40f"
    elif "SEGURO" in texto_upper:
        cor = "#2ecc71"
    else:
        cor = "#3498db"

    return f'<div style="background-color: {cor}; padding: 20px; border-radius: 10px; color: white; margin: 10px 0;">{texto}</div>'

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
    pdf.multi_cell(0, 6, texto)
    return pdf.output(dest='S').encode('latin-1')

import os
try:
    if os.path.exists("Logo_AI_1.png"):
        st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("AuditIA")

st.sidebar.success(f"Modelo: {modelo_nome}")
st.warning("TERMO: Ferramenta de apoio. Nao substitui pericia oficial.")
st.markdown("---")

st.header("Upload de Provas")

new_files = st.file_uploader(
    "Envie arquivos",
    type=["jpg", "png", "jpeg", "pdf", "eml"],
    accept_multiple_files=True,
    key="uploader1"
)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({
                "name": f.name,
                "content": f.read(),
                "type": f.type
            })

if st.session_state.arquivos_acumulados:
    st.write("Arquivos carregados:")
    for f in st.session_state.arquivos_acumulados:
        st.caption(f["name"])

st.subheader("Historico")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

user_query = st.text_area(
    "Pergunta",
    key="campo_pergunta",
    placeholder="Ex: Este email e phishing?",
    height=100
)

col1, col2 = st.columns(2)

with col1:
    if st.button("ANALISAR", on_click=processar_pericia, key="btn1"):
        pergunta = st.session_state.get("pergunta_ativa", "")

        if not pergunta and not st.session_state.arquivos_acumulados:
            st.warning("Envie arquivos ou pergunta")
        else:
            agora = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")

            with st.spinner("Analisando..."):
                try:
                    prompt = f"Perito forense. Hoje: {agora}. Analise: {pergunta}. Responda com CLASSIFICACAO: [FRAUDE CONFIRMADA/POSSIVEL FRAUDE/ATENCAO/SEGURO]"

                    contexto = [prompt]

                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"):
                            try:
                                msg = email.message_from_bytes(f["content"], policy=policy.default)
                                corpo = msg.get_body(preference=['plain']).get_content()
                                contexto.append(f"EMAIL: {corpo[:1000]}")
                            except:
                                pass
                        elif f["type"].startswith("image"):
                            try:
                                img = Image.open(io.BytesIO(f["content"]))
                                contexto.append(img)
                            except:
                                pass

                    response = model.generate_content(contexto, request_options={"timeout": 120})

                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro: {str(e)}")

with col2:
    if st.button("LIMPAR", key="btn2"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.rerun()

if st.session_state.historico_pericial:
    data = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
    pdf = gerar_pdf(st.session_state.historico_pericial[-1], data)

    st.download_button(
        "Baixar PDF",
        pdf,
        f"Laudo_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        "application/pdf",
        key="btn3"
    )

st.markdown("---")
st.caption("AuditIA v4.0 | Vargem Grande do Sul - SP")
