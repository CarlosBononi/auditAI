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

# ==================== CONFIGURAÇÃO INICIAL ====================
st.set_page_config(
    page_title="AuditIA - Inteligência Forense Digital",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Configurar API do Gemini
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    MODELO_USAR = modelos_disponiveis[0] if modelos_disponiveis else 'gemini-1.5-flash'
except Exception as e:
    st.error(f"⚠️ Erro ao configurar API do Gemini: {str(e)}")
    st.stop()

# ==================== ESTILO CUSTOMIZADO ====================
st.markdown("""
<style>
    :root {
        --verde-logo: #8BC34A;
        --cinza-fundo: #121212;
        --cinza-claro: #2c2c2c;
        --cinza-medio: #9e9e9e;
    }

    body {
        background-color: var(--cinza-fundo);
        color: #f5f5f5;
    }

    .main {
        background-color: var(--cinza-fundo);
    }

    /* Sidebar com cinza escuro e texto verde */
    [data-testid="stSidebar"] {
        background-color: #1d1d1d;
    }

    [data-testid="stSidebar"] * {
        color: var(--verde-logo) !important;
    }

    /* Botões cinza claro */
    .stButton > button {
        width: 100%;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
        margin: 0.25rem 0;
        background-color: #424242;
        color: #f5f5f5;
        border: 2px solid #616161;
    }

    .stButton > button:hover {
        background-color: #616161;
        border-color: #9e9e9e;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    }

    /* Botão Analisar levemente destacado */
    div[data-testid="column"]:first-child .stButton > button {
        background-color: #76ff03;
        color: #000000;
        border-color: #76ff03;
    }

    /* Inputs e caixas de texto com fundo cinza escuro e borda verde */
    .stTextArea textarea,
    .stTextInput input {
        background-color: #1e1e1e !important;
        color: #f5f5f5 !important;
        border: 1px solid var(--verde-logo) !important;
    }

    [data-testid="stFileUploader"] {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid var(--verde-logo);
    }

    /* Termo de consentimento agora cinza escuro com texto verde, no rodapé */
    .termo-consentimento {
        background-color: #1e1e1e;
        border-left: 4px solid var(--verde-logo);
        padding: 1.2rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #e0e0e0;
    }

    .subtitle-custom {
        font-size: 0.9rem;
        color: var(--verde-logo);
        font-weight: 400;
        margin-top: -0.3rem;
        margin-bottom: 1.2rem;
    }

    /* Diminuir título Upload ao tamanho do 'Analisando' */
    h1 {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }

    /* Veredito em destaque */
    .veredito-titulo {
        font-size: 1.4rem;
        font-weight: 800;
    }

    .classificacao-titulo {
        font-size: 1.2rem;
        font-weight: 800;
    }

    /* Resumo final */
    .resumo-final {
        background-color: #1e1e1e;
        border-left: 4px solid var(--verde-logo);
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin: 1.2rem 0;
        font-size: 0.95rem;
        color: #e0e0e0;
    }

    .resumo-final strong {
        color: var(--verde-logo);
    }

    /* Dica em cinza claro */
    .stAlert {
        background-color: #2c2c2c !important;
        color: #e0e0e0 !important;
        border-radius: 8px;
    }

    .stAlert * {
        color: #e0e0e0 !important;
    }

</style>
""", unsafe_allow_html=True)

# ==================== GESTÃO DE SESSÃO ====================
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False
if "caso_id" not in st.session_state:
    st.session_state.caso_id = None

def iniciar_novo_caso():
    st.session_state.historico_pericial = []
    st.session_state.arquivos_acumulados = []
    st.session_state.pergunta_ativa = ""
    st.session_state.caso_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.rerun()

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

# ==================== SISTEMA DE CORES ====================

def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    if any(term in texto_upper for term in [
        "CLASSIFICAÇÃO: FRAUDE CONFIRMADA", "VEREDITO: FRAUDE CONFIRMADA",
        "GOLPE CONFIRMADO", "SCAM CONFIRMADO"]):
        cor, font = "#d32f2f", "white"
        nivel = "FRAUDE CONFIRMADA"
    elif any(term in texto_upper for term in [
        "CLASSIFICAÇÃO: POSSÍVEL FRAUDE", "VEREDITO: POSSÍVEL FRAUDE",
        "POSSÍVEL FRAUDE", "ALTA ATENÇÃO", "PHISHING"]):
        cor, font = "#f57c00", "white"
        nivel = "POSSÍVEL FRAUDE"
    elif any(term in texto_upper for term in [
        "CLASSIFICAÇÃO: ATENÇÃO", "VEREDITO: ATENÇÃO",
        "ATENÇÃO", "INCONSISTÊNCIAS"]):
        cor, font = "#fbc02d", "black"
        nivel = "ATENÇÃO"
    elif any(term in texto_upper for term in [
        "CLASSIFICAÇÃO: SEGURO", "VEREDITO: SEGURO",
        "SEGURO", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO"]):
        cor, font = "#388e3c", "white"
        nivel = "SEGURO"
    else:
        cor, font = "#1976d2", "white"
        nivel = "INFORMATIVO"

    # Negrito adicional para veredito e classificação
    texto_html = texto.replace("## 🎯 VEREDITO FINAL", "<span class='veredito-titulo'>🎯 VEREDITO FINAL</span>")
    texto_html = re.sub(r"\*\*CLASSIFICAÇÃO:(.*?)\*\*",
                        r"<span class='classificacao-titulo'><strong>CLASSIFICAÇÃO:</strong></span>",
                        texto_html)

    return f"""
    <div style="background-color: {cor}; color: {font}; padding: 1.5rem; 
                border-radius: 12px; margin: 1rem 0; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
        {texto_html.replace(chr(10), '<br>')}
    </div>
    """, cor, nivel


def extrair_resumo(texto, nivel):
    # Resumo coerente com a classificação; não inferimos do texto para evitar conflito
    if nivel == "SEGURO":
        return "Este conteúdo foi avaliado como legítimo, com forte indicação de autenticidade e ausência de sinais relevantes de fraude ou phishing."
    if nivel == "FRAUDE CONFIRMADA":
        return "Foram identificados múltiplos sinais objetivos de fraude, configurando golpe confirmado. Recomenda-se não prosseguir e adotar medidas de segurança imediatas."
    if nivel == "POSSÍVEL FRAUDE":
        return "Existem vários elementos suspeitos que indicam possível fraude. É recomendável tratar esta comunicação com extrema cautela e buscar validação independente."
    if nivel == "ATENÇÃO":
        return "Foram observados alguns pontos de atenção que exigem verificação adicional antes de confiar totalmente neste conteúdo."
    return "Análise informativa concluída. Não foram identificados elementos suficientes para classificar como fraude ou como totalmente seguro."

# ==================== PROMPTS ====================

def obter_prompt_analise(tipo_arquivo):
    prompt_base = """
    Você é um especialista em análise forense digital. Sua análise deve ser clara, objetiva e conclusiva.

    ESTRUTURA OBRIGATÓRIA DA RESPOSTA:

    ## 🎯 VEREDITO FINAL
    **CLASSIFICAÇÃO: [FRAUDE CONFIRMADA / POSSÍVEL FRAUDE / ATENÇÃO / SEGURO]**

    [Explique em 2-3 linhas a conclusão de forma direta]

    ## 📋 ANÁLISE TÉCNICA
    [Explique os principais pontos técnicos que sustentam o veredito]

    ## ⚠️ RECOMENDAÇÕES
    [Liste ações práticas para o usuário]
    """

    if tipo_arquivo == "image":
        return prompt_base + """

        Foque em detecção de deepfake, manipulações digitais e incoerências visuais.
        """
    if tipo_arquivo == "email":
        return prompt_base + """

        Foque em linguagem de phishing, autenticidade de domínio, links, cabeçalhos SPF/DKIM e coerência do contexto com remetente legítimo.
        """
    if tipo_arquivo == "pdf":
        return prompt_base + """

        Foque em autenticidade de documento, metadados, fontes, assinaturas e possíveis montagens.
        """
    return prompt_base

# ==================== FUNÇÕES DE ANÁLISE ====================

def analisar_imagem(image, pergunta_usuario=""):
    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("image")
        if pergunta_usuario:
            prompt += f"

PERGUNTA DO USUÁRIO: {pergunta_usuario}"
        resposta = model.generate_content([prompt, img])
        return resposta.text
    except Exception as e:
        return f"❌ Erro na análise de imagem: {str(e)}"


def analisar_email(arquivo_email, pergunta_usuario=""):
    try:
        msg = BytesParser(policy=policy.default).parsebytes(arquivo_email.getvalue())
        remetente = msg.get("From", "Não identificado")
        destinatario = msg.get("To", "Não identificado")
        assunto = msg.get("Subject", "Sem assunto")
        data = msg.get("Date", "Sem data")

        corpo = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    corpo = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            corpo = msg.get_payload(decode=True).decode(errors="ignore")

        spf = msg.get("Received-SPF", "Não disponível")
        dkim = msg.get("DKIM-Signature", "Não disponível")

        contexto = f"""DADOS DO E-MAIL
Remetente: {remetente}
Destinatário: {destinatario}
Assunto: {assunto}
Data: {data}

CONTEÚDO DA MENSAGEM (trecho):
{corpo[:2000]}

AUTENTICAÇÃO TÉCNICA:
SPF: {spf}
DKIM: {'Presente' if 'não disponível' not in dkim.lower() else 'Ausente'}
"""

        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("email") + "

" + contexto
        if pergunta_usuario:
            prompt += f"

PERGUNTA DO USUÁRIO: {pergunta_usuario}"
        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro na análise de e-mail: {str(e)}"


def analisar_pdf(arquivo_pdf, pergunta_usuario=""):
    try:
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("pdf")
        if pergunta_usuario:
            prompt += f"

PERGUNTA DO USUÁRIO: {pergunta_usuario}"
        resposta = model.generate_content([prompt, arquivo_pdf.getvalue()])
        return resposta.text
    except Exception as e:
        return f"❌ Erro na análise de PDF: {str(e)}"

# ==================== INTERFACE PRINCIPAL ====================

# Logo maior (dobrado em relação à anterior). Para remover sobras, o fundo do app é cinza igual ao fundo da logo.
try:
    if os.path.exists("Logo_AI_1.png"):
        logo = Image.open("Logo_AI_1.png")
        st.image(logo, width=800)  # se a anterior era ~400, aqui dobramos
except:
    pass

# Subtítulo: apenas "Inteligência Forense Digital"
st.markdown('<p class="subtitle-custom">Inteligência Forense Digital</p>', unsafe_allow_html=True)

# ==================== GUIA (SIDEBAR) ====================
with st.sidebar:
    st.header("📚 Guia Completo de Uso")
    st.expander("🎯 O que é o AuditIA?").markdown("O AuditIA é uma plataforma de Inteligência Forense Digital para análise de imagens, e-mails e documentos.")
    st.expander("📤 Como Enviar Arquivos?").markdown("Envie JPG, PNG, PDF, EML ou PST para análise pericial automatizada.")
    st.expander("🎨 Entenda as Cores").markdown("Verde = seguro, Laranja = possível fraude, Vermelho = fraude confirmada, Amarelo = atenção, Azul = informativo.")
    st.expander("🔍 Tipos de Análise").markdown("Deepfake, phishing, autenticidade documental e mais.")
    st.expander("⚡ Perguntas Frequentes").markdown("O AuditIA não substitui perícia oficial, é uma ferramenta de apoio.")
    st.info("💡 Quanto mais contexto você fornecer, melhor será a análise!", icon="ℹ️")

# ==================== ÁREA DE UPLOAD ====================
st.header("📂 Upload de Arquivos para Análise")

arquivos = st.file_uploader(
    "Selecione os arquivos para análise forense",
    type=["jpg", "jpeg", "png", "pdf", "eml", "pst"],
    accept_multiple_files=True,
)

pergunta = st.text_area(
    "💬 Pergunta Específica (Opcional)",
    placeholder="Ex: Este e-mail é legítimo? Esta imagem foi manipulada? Este documento é autêntico?",
    key="campo_pergunta",
)

col1, col2, col3 = st.columns(3)
with col1:
    analisar_btn = st.button("🔍 Analisar", use_container_width=True, on_click=processar_pericia)
with col2:
    limpar_btn = st.button("🗑️ Limpar Caso", use_container_width=True, on_click=iniciar_novo_caso)
with col3:
    exportar_btn = st.button("📥 Exportar PDF", use_container_width=True)

# ==================== PROCESSAMENTO ====================
if analisar_btn and arquivos:
    with st.spinner("🔬 Realizando análise forense detalhada..."):
        for arquivo in arquivos:
            st.markdown(f"### 📄 Analisando: `{arquivo.name}`")

            if arquivo.type.startswith("image/"):
                img = Image.open(arquivo)
                img.thumbnail((300, 300))
                st.image(img, caption=arquivo.name, width=300)

            if arquivo.type in ["image/jpeg", "image/png", "image/jpg"]:
                resultado = analisar_imagem(arquivo, st.session_state.pergunta_ativa)
            elif arquivo.type == "message/rfc822" or arquivo.name.endswith(".eml"):
                resultado = analisar_email(arquivo, st.session_state.pergunta_ativa)
            elif arquivo.type == "application/pdf":
                resultado = analisar_pdf(arquivo, st.session_state.pergunta_ativa)
            else:
                resultado = "❌ Formato de arquivo não suportado"

            html_resultado, cor, nivel = aplicar_estilo_pericial(resultado)
            st.markdown(html_resultado, unsafe_allow_html=True)

            resumo = extrair_resumo(resultado, nivel)
            st.markdown(f"""
            <div class="resumo-final">
                <strong>📊 RESUMO DO RESULTADO</strong><br>
                <strong>Classificação:</strong> {nivel}<br>
                <strong>Conclusão:</strong> {resumo}
            </div>
            """, unsafe_allow_html=True)

            st.session_state.historico_pericial.append({
                "arquivo": arquivo.name,
                "resultado": resultado,
                "cor": cor,
                "nivel": nivel,
                "timestamp": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")
            })

elif analisar_btn and not arquivos:
    st.warning("⚠️ Por favor, envie pelo menos um arquivo para análise.")

# ==================== HISTÓRICO ====================
if st.session_state.historico_pericial:
    st.markdown("---")
    st.header("📊 Histórico de Análises do Caso Atual")
    for i, item in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"🔎 Análise #{i} - {item['arquivo']} | {item['timestamp']} | {item['nivel']}"):
            html_hist, _, _ = aplicar_estilo_pericial(item['resultado'])
            st.markdown(html_hist, unsafe_allow_html=True)

# ==================== TERMO DE CONSENTIMENTO NO FINAL ====================

with st.expander("⚖️ Termo de Consentimento e Uso Responsável", expanded=not st.session_state.termo_aceito):
    st.markdown("""
    <div class="termo-consentimento">
    <h4>Uso Responsável do AuditIA</h4>
    <p>O AuditIA é uma ferramenta de apoio à análise forense digital. Os resultados são probabilísticos e não substituem perícia oficial ou julgamento humano especializado.</p>
    <ul>
        <li>Use os laudos como apoio, não como única prova.</li>
        <li>Evite enviar dados excessivamente sensíveis.</li>
        <li>Respeite a legislação e a privacidade de terceiros.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
    aceite = st.checkbox("Li e concordo com o uso responsável do AuditIA.", value=st.session_state.termo_aceito)
    if aceite and not st.session_state.termo_aceito:
        st.session_state.termo_aceito = True
        st.rerun()

if not st.session_state.termo_aceito:
    st.warning("⚠️ Para utilizar o AuditIA, leia e aceite o Termo de Consumo Responsável no final da página.")

st.markdown("---")
st.caption("AuditIA v2.0 | Ferramenta de apoio - Não substitui perícia oficial")
