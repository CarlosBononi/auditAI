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
import os

st.set_page_config(
    page_title="AuditIA - Inteligência Forense Digital",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="expanded"
)

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    MODELO_USAR = modelos_disponiveis[0] if modelos_disponiveis else 'gemini-1.5-flash'
except Exception as e:
    st.error(f"⚠️ Erro ao configurar API do Gemini: {str(e)}")
    st.stop()

# CSS com tema dark tecnológico
st.markdown("""
<style>
    :root {
        --verde-logo: #8BC34A;
        --cinza-fundo: #1a1a1a;
        --cinza-medio: #2d2d2d;
    }

    .stApp {
        background-color: var(--cinza-fundo);
        color: #e0e0e0;
    }

    /* Sidebar dark com texto verde */
    [data-testid="stSidebar"] {
        background-color: #1a1a1a;
    }

    [data-testid="stSidebar"] .element-container {
        color: var(--verde-logo) !important;
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: var(--verde-logo) !important;
    }

    /* Botões cinza */
    .stButton > button {
        background-color: #424242;
        color: #e0e0e0;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        background-color: #616161;
        transform: translateY(-2px);
    }

    /* Botão Analisar verde */
    div[data-testid="column"]:first-child .stButton > button {
        background-color: var(--verde-logo);
        color: #000000;
        font-weight: 600;
    }

    div[data-testid="column"]:first-child .stButton > button:hover {
        background-color: #9CCC65;
    }

    /* Inputs com fundo cinza e borda verde */
    .stTextArea textarea,
    .stTextInput input {
        background-color: var(--cinza-medio) !important;
        color: #e0e0e0 !important;
        border: 1px solid var(--verde-logo) !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: var(--cinza-medio);
        border: 1px solid var(--verde-logo);
        border-radius: 8px;
        padding: 1rem;
    }

    [data-testid="stFileUploader"] label {
        color: #e0e0e0 !important;
    }

    /* Título Upload igual ao Analisando */
    h1 {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        color: #e0e0e0;
    }

    /* Subtítulo */
    .subtitle-custom {
        font-size: 0.9rem;
        color: var(--verde-logo);
        font-weight: 400;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    /* VEREDITO e CLASSIFICAÇÃO maiores e em negrito */
    .resultado-box h2 {
        font-size: 1.5rem !important;
        font-weight: 800 !important;
    }

    .resultado-box h3 {
        font-size: 1.3rem !important;
        font-weight: 800 !important;
    }

    /* Resumo final */
    .resumo-final {
        background-color: var(--cinza-medio);
        border-left: 4px solid var(--verde-logo);
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        color: #e0e0e0;
    }

    .resumo-final strong {
        color: var(--verde-logo);
        font-size: 1.1rem;
    }

    /* Info box (dica) em cinza claro */
    .stAlert {
        background-color: var(--cinza-medio) !important;
        color: #e0e0e0 !important;
        border-left: 4px solid #757575 !important;
    }

    /* Termo no final */
    .termo-consentimento {
        background-color: var(--cinza-medio);
        border-left: 4px solid var(--verde-logo);
        padding: 1.2rem;
        border-radius: 8px;
        margin-top: 2rem;
        color: #e0e0e0;
    }

    .termo-consentimento h4 {
        color: var(--verde-logo);
    }

    /* Imagens */
    .stImage img {
        max-width: 300px !important;
        max-height: 300px !important;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Estado da sessão
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False

def iniciar_novo_caso():
    st.session_state.historico_pericial = []
    st.session_state.pergunta_ativa = ""
    st.rerun()

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.get("campo_pergunta", "")

def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    # Detecção de nível com prioridade
    if "CLASSIFICAÇÃO: SEGURO" in texto_upper or "VEREDITO: SEGURO" in texto_upper:
        cor, font, nivel = "#388e3c", "white", "SEGURO"
    elif "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper or "GOLPE CONFIRMADO" in texto_upper:
        cor, font, nivel = "#d32f2f", "white", "FRAUDE CONFIRMADA"
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper or "PHISHING" in texto_upper:
        cor, font, nivel = "#f57c00", "white", "POSSÍVEL FRAUDE"
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper:
        cor, font, nivel = "#fbc02d", "black", "ATENÇÃO"
    else:
        cor, font, nivel = "#1976d2", "white", "INFORMATIVO"

    # Formatar com negrito
    texto_formatado = texto.replace("## 🎯 VEREDITO FINAL", "<h2>🎯 VEREDITO FINAL</h2>")
    texto_formatado = texto_formatado.replace("**CLASSIFICAÇÃO:", "<h3><strong>CLASSIFICAÇÃO:")
    texto_formatado = texto_formatado.replace("**", "</strong></h3>", 1)

    return f"""
    <div class="resultado-box" style="background-color: {cor}; color: {font}; padding: 1.5rem; 
                border-radius: 12px; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        {texto_formatado.replace(chr(10), '<br>')}
    </div>
    """, cor, nivel

def extrair_resumo(nivel):
    resumos = {
        "SEGURO": "Este conteúdo foi avaliado como legítimo, com forte indicação de autenticidade e ausência de sinais relevantes de fraude ou phishing.",
        "FRAUDE CONFIRMADA": "Foram identificados múltiplos sinais objetivos de fraude, configurando golpe confirmado. Não prossiga e adote medidas de segurança imediatas.",
        "POSSÍVEL FRAUDE": "Existem vários elementos suspeitos que indicam possível fraude. Trate esta comunicação com extrema cautela e busque validação independente.",
        "ATENÇÃO": "Foram observados alguns pontos de atenção que exigem verificação adicional antes de confiar totalmente neste conteúdo.",
        "INFORMATIVO": "Análise informativa concluída. Não foram identificados elementos suficientes para classificar como fraude ou como totalmente seguro."
    }
    return resumos.get(nivel, "Análise concluída.")

def obter_prompt_analise(tipo_arquivo):
    prompt_base = """
Você é um especialista em análise forense digital. Sua análise deve ser clara, objetiva e conclusiva.

ESTRUTURA OBRIGATÓRIA DA RESPOSTA:

## 🎯 VEREDITO FINAL
**CLASSIFICAÇÃO: [FRAUDE CONFIRMADA / POSSÍVEL FRAUDE / ATENÇÃO / SEGURO]**

[Explique em 2-3 linhas a conclusão]

## 📋 ANÁLISE TÉCNICA
[Principais pontos técnicos]

## ⚠️ RECOMENDAÇÕES
[Ações práticas]
"""

    if tipo_arquivo == "image":
        return prompt_base + "\nFoque em deepfake, manipulações digitais e incoerências visuais."
    elif tipo_arquivo == "email":
        return prompt_base + "\nFoque em phishing, autenticidade de domínio, links suspeitos e cabeçalhos de autenticação."
    elif tipo_arquivo == "pdf":
        return prompt_base + "\nFoque em autenticidade de documento, metadados e possíveis montagens."
    return prompt_base

def analisar_imagem(image, pergunta_usuario=""):
    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("image")
        if pergunta_usuario:
            prompt += f"\n\nPERGUNTA: {pergunta_usuario}"
        resposta = model.generate_content([prompt, img])
        return resposta.text
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def analisar_email(arquivo_email, pergunta_usuario=""):
    try:
        msg = BytesParser(policy=policy.default).parsebytes(arquivo_email.getvalue())
        remetente = msg.get("From", "?")
        assunto = msg.get("Subject", "?")

        corpo = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    corpo = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            corpo = msg.get_payload(decode=True).decode(errors="ignore")

        contexto = f"Remetente: {remetente}\nAssunto: {assunto}\n\nConteúdo:\n{corpo[:2000]}"

        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("email") + "\n\n" + contexto
        if pergunta_usuario:
            prompt += f"\n\nPERGUNTA: {pergunta_usuario}"
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def analisar_pdf(arquivo_pdf, pergunta_usuario=""):
    try:
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("pdf")
        if pergunta_usuario:
            prompt += f"\n\nPERGUNTA: {pergunta_usuario}"
        resposta = model.generate_content([prompt, arquivo_pdf.getvalue()])
        return resposta.text
    except Exception as e:
        return f"❌ Erro: {str(e)}"

# ==================== INTERFACE ====================

# Logo GRANDE (800px)
try:
    if os.path.exists("Logo_AI_1.png"):
        logo = Image.open("Logo_AI_1.png")
        st.image(logo, width=800)
except:
    pass

# Subtítulo apenas "Inteligência Forense Digital"
st.markdown('<p class="subtitle-custom">Inteligência Forense Digital</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📚 Guia Completo de Uso")
    with st.expander("🎯 O que é o AuditIA?"):
        st.write("Plataforma de Inteligência Forense Digital para análise de imagens, e-mails e documentos.")
    with st.expander("📤 Como Enviar Arquivos?"):
        st.write("Envie JPG, PNG, PDF, EML ou PST para análise.")
    with st.expander("🎨 Entenda as Cores"):
        st.write("🟢 Verde = Seguro | 🟠 Laranja = Possível Fraude | 🔴 Vermelho = Fraude Confirmada")
    with st.expander("🔍 Tipos de Análise"):
        st.write("Deepfake, phishing, autenticidade documental.")
    with st.expander("⚡ Perguntas Frequentes"):
        st.write("O AuditIA é uma ferramenta de apoio, não substitui perícia oficial.")
    st.info("💡 Quanto mais contexto, melhor a análise!")

# Upload
st.header("📂 Upload de Arquivos para Análise")

arquivos = st.file_uploader(
    "Selecione os arquivos",
    type=["jpg", "jpeg", "png", "pdf", "eml", "pst"],
    accept_multiple_files=True
)

pergunta = st.text_area(
    "💬 Pergunta Específica (Opcional)",
    placeholder="Ex: Este e-mail é legítimo?",
    key="campo_pergunta"
)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔍 Analisar", use_container_width=True):
        processar_pericia()
with col2:
    if st.button("🗑️ Limpar Caso", use_container_width=True):
        iniciar_novo_caso()
with col3:
    st.button("📥 Exportar PDF", use_container_width=True)

# Processamento
if st.session_state.pergunta_ativa and arquivos:
    with st.spinner("🔬 Analisando..."):
        for arquivo in arquivos:
            st.markdown(f"### 📄 Analisando: `{arquivo.name}`")

            if arquivo.type.startswith("image/"):
                img = Image.open(arquivo)
                img.thumbnail((300, 300))
                st.image(img, width=300)

            if arquivo.type in ["image/jpeg", "image/png", "image/jpg"]:
                resultado = analisar_imagem(arquivo, st.session_state.pergunta_ativa)
            elif arquivo.type == "message/rfc822" or arquivo.name.endswith(".eml"):
                resultado = analisar_email(arquivo, st.session_state.pergunta_ativa)
            elif arquivo.type == "application/pdf":
                resultado = analisar_pdf(arquivo, st.session_state.pergunta_ativa)
            else:
                resultado = "❌ Formato não suportado"

            html_resultado, cor, nivel = aplicar_estilo_pericial(resultado)
            st.markdown(html_resultado, unsafe_allow_html=True)

            resumo = extrair_resumo(nivel)
            st.markdown(f"""
            <div class="resumo-final">
                <strong>📊 RESUMO DO RESULTADO</strong><br><br>
                <strong>Classificação:</strong> {nivel}<br>
                <strong>Conclusão:</strong> {resumo}
            </div>
            """, unsafe_allow_html=True)

            st.session_state.historico_pericial.append({
                "arquivo": arquivo.name,
                "resultado": resultado,
                "nivel": nivel,
                "timestamp": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
            })

    st.session_state.pergunta_ativa = ""

# Histórico
if st.session_state.historico_pericial:
    st.markdown("---")
    st.header("📊 Histórico de Análises")
    for i, item in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"🔎 #{i} - {item['arquivo']} | {item['timestamp']} | {item['nivel']}"):
            html_hist, _, _ = aplicar_estilo_pericial(item['resultado'])
            st.markdown(html_hist, unsafe_allow_html=True)

# Termo no final
st.markdown("---")
with st.expander("⚖️ Termo de Consentimento e Uso Responsável"):
    st.markdown("""
    <div class="termo-consentimento">
    <h4>Uso Responsável do AuditIA</h4>
    <p>O AuditIA é uma ferramenta de apoio à análise forense digital. Os resultados são probabilísticos 
    e não substituem perícia oficial.</p>
    <ul>
        <li>Use como apoio, não como única prova</li>
        <li>Evite dados excessivamente sensíveis</li>
        <li>Respeite legislação e privacidade</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

st.caption("AuditIA v2.0 | Ferramenta de apoio - Não substitui perícia oficial")
