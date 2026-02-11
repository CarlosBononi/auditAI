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

# Configurar API do Gemini com detecção automática de modelos
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    MODELO_USAR = modelos_disponiveis[0] if modelos_disponiveis else 'gemini-1.5-flash'
except Exception as e:
    st.error(f"⚠️ Erro ao configurar API do Gemini: {str(e)}")
    st.info("💡 Verifique se a API Key está configurada corretamente em .streamlit/secrets.toml")
    st.stop()

# ==================== ESTILO CUSTOMIZADO ====================
st.markdown('''
<style>
    /* Cores baseadas na logo */
    :root {
        --verde-logo: #8BC34A;
        --cinza-escuro: #424242;
        --cinza-claro: #e0e0e0;
    }

    /* Fundo BRANCO mantido */
    .main {
        background-color: white;
    }

    /* Sidebar com fundo cinza escuro e texto verde */
    [data-testid="stSidebar"] {
        background-color: var(--cinza-escuro);
    }

    [data-testid="stSidebar"] * {
        color: var(--verde-logo) !important;
    }

    [data-testid="stSidebar"] .stMarkdown {
        color: var(--verde-logo) !important;
    }

    /* Botões harmonizados */
    .stButton > button {
        width: 100%;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
        margin: 0.25rem 0;
    }

    /* Botão Analisar - verde destacado */
    div[data-testid="column"]:first-child .stButton > button {
        background-color: var(--verde-logo);
        color: white;
        border: 2px solid var(--verde-logo);
    }

    div[data-testid="column"]:first-child .stButton > button:hover {
        background-color: #7CB342;
        border-color: #7CB342;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(139, 195, 74, 0.3);
    }

    /* Botão Limpar - cinza claro */
    div[data-testid="column"]:nth-child(2) .stButton > button {
        background-color: var(--cinza-claro);
        color: #424242;
        border: 2px solid #bdbdbd;
    }

    div[data-testid="column"]:nth-child(2) .stButton > button:hover {
        background-color: #d32f2f;
        border-color: #d32f2f;
        color: white;
    }

    /* Botão Exportar - cinza claro */
    div[data-testid="column"]:nth-child(3) .stButton > button {
        background-color: var(--cinza-claro);
        color: #424242;
        border: 2px solid #bdbdbd;
    }

    div[data-testid="column"]:nth-child(3) .stButton > button:hover {
        background-color: #1976d2;
        border-color: #1976d2;
        color: white;
    }

    /* Redimensionar imagens anexadas */
    .stImage img {
        max-width: 300px !important;
        max-height: 300px !important;
        object-fit: contain;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }

    /* Termo de consentimento - cinza escuro com texto verde */
    .termo-consentimento {
        background-color: var(--cinza-escuro);
        color: var(--verde-logo);
        border-left: 4px solid var(--verde-logo);
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .termo-consentimento h4,
    .termo-consentimento h5,
    .termo-consentimento p,
    .termo-consentimento ul,
    .termo-consentimento li {
        color: var(--verde-logo) !important;
    }

    /* Checkbox do termo - cinza escuro */
    .stCheckbox {
        padding: 1rem;
        background-color: var(--cinza-escuro);
        border-radius: 8px;
        margin: 1rem 0;
    }

    .stCheckbox label {
        color: var(--verde-logo) !important;
    }

    /* Caixas de texto - cinza escuro com texto verde */
    .stTextArea textarea {
        background-color: var(--cinza-escuro) !important;
        color: var(--verde-logo) !important;
        border: 2px solid var(--verde-logo) !important;
    }

    .stTextArea label {
        color: #424242 !important;
    }

    /* Área de upload - cinza escuro com borda verde */
    [data-testid="stFileUploader"] {
        background-color: var(--cinza-escuro);
        border: 2px solid var(--verde-logo);
        border-radius: 8px;
        padding: 1rem;
    }

    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] span {
        color: var(--verde-logo) !important;
    }

    /* Subtítulo pequeno */
    .subtitle-custom {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 400;
        margin-top: -0.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }

    /* Título "Upload de Arquivos" = tamanho "Analisando" */
    h1 {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
    }

    /* VEREDITO FINAL e CLASSIFICAÇÃO maiores e em NEGRITO */
    .veredito-destaque {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        line-height: 1.3;
    }

    .classificacao-destaque {
        font-size: 1.3rem !important;
        font-weight: 800 !important;
    }

    /* Resumo final - cinza escuro com texto verde */
    .resumo-final {
        background-color: var(--cinza-escuro);
        border-left: 4px solid var(--verde-logo);
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1.5rem 0;
        color: var(--verde-logo);
    }

    .resumo-final strong {
        color: #7CB342;
        font-size: 1.1rem;
    }

    /* Info/Dica em cinza claro */
    .stAlert {
        background-color: var(--cinza-claro) !important;
        color: #424242 !important;
        border-left: 4px solid #9e9e9e !important;
    }

    .stAlert [data-testid="stMarkdownContainer"] {
        color: #424242 !important;
    }
</style>
''', unsafe_allow_html=True)

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
    '''Limpa completamente o caso e inicia um novo'''
    st.session_state.historico_pericial = []
    st.session_state.arquivos_acumulados = []
    st.session_state.pergunta_ativa = ""
    st.session_state.caso_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.rerun()

def processar_pericia():
    '''Captura a pergunta antes do rerun'''
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

# ==================== SISTEMA DE CORES INTELIGENTE ====================
def aplicar_estilo_pericial(texto):
    '''Sistema de classificação visual com hierarquia clara'''
    texto_upper = texto.upper()

    # Detecção com prioridade para SEGURO primeiro
    if "CLASSIFICAÇÃO: SEGURO" in texto_upper or "VEREDITO: SEGURO" in texto_upper:
        cor, font = "#388e3c", "white"  # 🟢 VERDE
        nivel = "SEGURO"
    elif any(term in texto_upper for term in [
        "CLASSIFICAÇÃO: FRAUDE CONFIRMADA", "VEREDITO: FRAUDE CONFIRMADA",
        "GOLPE CONFIRMADO", "SCAM CONFIRMADO", "FRAUDE CONFIRMADA"
    ]):
        cor, font = "#d32f2f", "white"  # 🔴 VERMELHO
        nivel = "FRAUDE CONFIRMADA"
    elif any(term in texto_upper for term in [
        "CLASSIFICAÇÃO: POSSÍVEL FRAUDE", "VEREDITO: POSSÍVEL FRAUDE",
        "ALTA ATENÇÃO", "MUITO SUSPEITO", "PHISHING", "POSSÍVEL FRAUDE"
    ]):
        cor, font = "#f57c00", "white"  # 🟠 LARANJA
        nivel = "POSSÍVEL FRAUDE"
    elif any(term in texto_upper for term in [
        "CLASSIFICAÇÃO: ATENÇÃO", "VEREDITO: ATENÇÃO",
        "SUSPEITO", "ANÁLISE NECESSÁRIA", "INCONSISTÊNCIAS"
    ]):
        cor, font = "#fbc02d", "black"  # 🟡 AMARELO
        nivel = "ATENÇÃO"
    else:
        cor, font = "#1976d2", "white"  # 🔵 AZUL
        nivel = "INFORMATIVO"

    # Aplicar negrito e tamanho maior para VEREDITO e CLASSIFICAÇÃO
    texto_formatado = texto
    texto_formatado = texto_formatado.replace(
        "## 🎯 VEREDITO FINAL", 
        '<div class="veredito-destaque">🎯 VEREDITO FINAL</div>'
    )
    texto_formatado = texto_formatado.replace(
        "**CLASSIFICAÇÃO:", 
        '<div class="classificacao-destaque"><strong>CLASSIFICAÇÃO:'
    )
    if '<div class="classificacao-destaque">' in texto_formatado:
        texto_formatado = texto_formatado.replace("**", "</strong></div>", 1)

    return f'''
    <div style="background-color: {cor}; color: {font}; padding: 1.5rem; 
                border-radius: 12px; margin: 1rem 0; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
        {texto_formatado.replace(chr(10), '<br>')}
    </div>
    ''', cor, nivel

def extrair_resumo(nivel):
    '''Extrai resumo COERENTE baseado apenas no nível'''
    resumos = {
        "SEGURO": "Este conteúdo foi avaliado como legítimo, com forte indicação de autenticidade e ausência de sinais relevantes de fraude ou phishing.",
        "FRAUDE CONFIRMADA": "Foram identificados múltiplos sinais objetivos de fraude, configurando golpe confirmado. Recomenda-se não prosseguir e adotar medidas de segurança imediatas.",
        "POSSÍVEL FRAUDE": "Existem vários elementos suspeitos que indicam possível fraude. É recomendável tratar esta comunicação com extrema cautela e buscar validação independente.",
        "ATENÇÃO": "Foram observados alguns pontos de atenção que exigem verificação adicional antes de confiar totalmente neste conteúdo.",
        "INFORMATIVO": "Análise informativa concluída. Não foram identificados elementos suficientes para classificar como fraude ou como totalmente seguro."
    }
    return resumos.get(nivel, "Análise concluída. Veja detalhes acima.")

# ==================== PROMPTS OTIMIZADOS ====================
def obter_prompt_analise(tipo_arquivo):
    '''Retorna prompts equilibrados entre técnico e acessível'''

    prompt_base = """
    Você é um especialista em análise forense digital. Sua análise deve ser:
    - Clara e objetiva (acessível para público geral)
    - Tecnicamente fundamentada (útil para auditores)
    - Conclusiva (veredito claro e direto)

    ESTRUTURA OBRIGATÓRIA DA RESPOSTA:

    ## 🎯 VEREDITO FINAL
    **CLASSIFICAÇÃO: [FRAUDE CONFIRMADA / POSSÍVEL FRAUDE / ATENÇÃO / SEGURO]**

    [Em 2-3 linhas, explique de forma clara e direta sua conclusão]

    ## 📋 ANÁLISE TÉCNICA
    [Apresente os indicadores técnicos encontrados de forma objetiva]

    ## ⚠️ RECOMENDAÇÕES
    [Liste as ações recomendadas]

    ---

    REGRAS CRÍTICAS:
    1. SEMPRE comece com o VEREDITO FINAL em destaque
    2. Seja CONCLUSIVO - evite "pode ser", "talvez", "possivelmente" no veredito
    3. Se for fraude, diga FRAUDE CONFIRMADA
    4. Se houver dúvidas sérias, diga POSSÍVEL FRAUDE ou ATENÇÃO
    5. Analise TODO o conteúdo fornecido, não apenas metadados
    """

    if tipo_arquivo in ["image/jpeg", "image/png", "image/jpg"]:
        return prompt_base + """

        ANÁLISE ESPECÍFICA PARA IMAGENS:

        Verifique rigorosamente:
        1. **Artefatos de IA/Deepfake**: Texturas irreais, anatomia incorreta, iluminação inconsistente
        2. **Manipulações digitais**: Clonagem, edição, montagem
        3. **Contexto visual**: Coerência da cena, reflexos, sombras
        4. **Metadados**: EXIF, software de edição usado

        Se detectar sinais de IA ou manipulação significativos: CLASSIFICAÇÃO: ATENÇÃO ou POSSÍVEL FRAUDE
        Se for claramente manipulado para enganar: CLASSIFICAÇÃO: FRAUDE CONFIRMADA
        """

    elif tipo_arquivo == "message/rfc822" or "eml" in tipo_arquivo.lower():
        return prompt_base + """

        ANÁLISE ESPECÍFICA PARA E-MAILS:

        Verifique rigorosamente:
        1. **Conteúdo da mensagem**: Linguagem de urgência, ameaças, promessas irreais
        2. **Remetente**: Domínio genérico, nome suspeito, inconsistências
        3. **Técnicas de phishing**: Links suspeitos, anexos maliciosos, spoofing
        4. **Autenticação**: SPF, DKIM, DMARC (se disponíveis)
        5. **Contexto psicológico**: Manipulação emocional, engenharia social

        IMPORTANTE: Analise SEMPRE o conteúdo completo do e-mail, não apenas cabeçalhos!

        Se for phishing claro: CLASSIFICAÇÃO: FRAUDE CONFIRMADA
        Se houver múltiplos indicadores suspeitos: CLASSIFICAÇÃO: POSSÍVEL FRAUDE
        Se houver alguns sinais de alerta: CLASSIFICAÇÃO: ATENÇÃO
        """

    elif tipo_arquivo == "application/pdf":
        return prompt_base + """

        ANÁLISE ESPECÍFICA PARA PDFs:

        Verifique:
        1. **Conteúdo**: Autenticidade de documentos, consistência de informações
        2. **Formatação**: Fontes inconsistentes, alinhamento suspeito
        3. **Metadados**: Autor, software criador, histórico de edições
        4. **Elementos visuais**: Logos, assinaturas, carimbos (verificar autenticidade)
        """

    return prompt_base

# ==================== FUNÇÕES DE ANÁLISE ====================
def analisar_imagem(image, pergunta_usuario=""):
    '''Análise de imagem com prompt otimizado'''
    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))

        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("image/jpeg")

        if pergunta_usuario:
            prompt += f"\n\nPERGUNTA DO USUÁRIO: {pergunta_usuario}"

        resposta = model.generate_content([prompt, img])
        return resposta.text
    except Exception as e:
        return f"❌ Erro na análise de imagem: {str(e)}"

def analisar_email(arquivo_email, pergunta_usuario=""):
    '''Análise de e-mail com foco em conteúdo e contexto'''
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

        contexto = f"""
        === DADOS DO E-MAIL ===
        Remetente: {remetente}
        Destinatário: {destinatario}
        Assunto: {assunto}
        Data: {data}

        === CONTEÚDO DA MENSAGEM ===
        {corpo[:2000]}

        === AUTENTICAÇÃO ===
        SPF: {spf}
        DKIM: {'Presente' if 'não disponível' not in dkim.lower() else 'Ausente'}
        """

        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("message/rfc822") + f"\n\n{contexto}"

        if pergunta_usuario:
            prompt += f"\n\nPERGUNTA DO USUÁRIO: {pergunta_usuario}"

        resposta = model.generate_content(prompt)
        return resposta.text
    except Exception as e:
        return f"❌ Erro na análise de e-mail: {str(e)}"

def analisar_pdf(arquivo_pdf, pergunta_usuario=""):
    '''Análise de PDF'''
    try:
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("application/pdf")

        if pergunta_usuario:
            prompt += f"\n\nPERGUNTA DO USUÁRIO: {pergunta_usuario}"

        resposta = model.generate_content([prompt, arquivo_pdf.getvalue()])
        return resposta.text
    except Exception as e:
        return f"❌ Erro na análise de PDF: {str(e)}"

# ==================== INTERFACE PRINCIPAL ====================

# Logo GRANDE (800px) - DOBRO DO TAMANHO
try:
    if os.path.exists("Logo_AI_1.png"):
        logo = Image.open("Logo_AI_1.png")
        st.image(logo, width=800)
except:
    st.markdown("# 👁️ AuditIA")

# Subtítulo APENAS "Inteligência Forense Digital"
st.markdown('<p class="subtitle-custom">Inteligência Forense Digital</p>', unsafe_allow_html=True)

# ==================== TERMO DE CONSENTIMENTO (TOPO - OBRIGATÓRIO) ====================
with st.expander("⚖️ TERMO DE CONSENTIMENTO E USO RESPONSÁVEL - LEIA ANTES DE USAR", expanded=not st.session_state.termo_aceito):
    st.markdown("""
    <div class="termo-consentimento">
    <h4>📜 Aviso Importante sobre o Uso do AuditIA</h4>

    <p><strong>O AuditIA é uma ferramenta de apoio à análise forense digital</strong>, desenvolvida para auxiliar na identificação de fraudes, deepfakes, phishing e outras ameaças digitais. No entanto, é fundamental entender as seguintes condições:</p>

    <h5>🎯 Propósito e Limitações</h5>
    <ul>
        <li><strong>Ferramenta de Apoio:</strong> O AuditIA fornece análises probabilísticas baseadas em inteligência artificial. Não substitui perícia oficial, análise humana especializada ou decisão judicial.</li>
        <li><strong>Não é Infalível:</strong> Como qualquer sistema de IA, pode apresentar falsos positivos ou falsos negativos. Sempre busque confirmação adicional para decisões críticas.</li>
        <li><strong>Uso Ético:</strong> Esta ferramenta deve ser usada exclusivamente para fins legítimos de segurança, auditoria e proteção contra fraudes.</li>
    </ul>

    <h5>⚠️ Responsabilidades do Usuário</h5>
    <ul>
        <li>Você é responsável pela interpretação e uso dos resultados fornecidos</li>
        <li>Não use os laudos como única evidência em processos legais sem validação adicional</li>
        <li>Respeite a privacidade e os direitos autorais ao analisar conteúdos</li>
        <li>Não submeta dados sensíveis ou confidenciais sem autorização adequada</li>
    </ul>

    <h5>🔒 Privacidade e Dados</h5>
    <ul>
        <li>Arquivos analisados são processados temporariamente e não são armazenados permanentemente</li>
        <li>Os resultados são gerados em tempo real e mantidos apenas durante sua sessão</li>
        <li>Recomendamos não enviar informações pessoais sensíveis desnecessariamente</li>
    </ul>

    <h5>📞 Suporte e Desenvolvimento</h5>
    <p>O AuditIA está em constante evolução. Para dúvidas, sugestões ou reportar problemas, entre em contato com a equipe de desenvolvimento.</p>

    <p><strong>Desenvolvido em Vargem Grande do Sul - SP | Versão 2.0 - Fevereiro 2026</strong></p>
    </div>
    """, unsafe_allow_html=True)

    aceite = st.checkbox(
        "✅ Li e concordo com os termos acima. Estou ciente de que o AuditIA é uma ferramenta de apoio e não substitui análise especializada profissional.",
        value=st.session_state.termo_aceito,
        key="checkbox_termo"
    )

    if aceite and not st.session_state.termo_aceito:
        st.session_state.termo_aceito = True
        st.success("✅ Termo aceito! Você já pode usar o AuditIA.")
        st.rerun()

# Bloquear uso se termo não foi aceito
if not st.session_state.termo_aceito:
    st.warning("⚠️ Por favor, leia e aceite o Termo de Consentimento acima para utilizar o AuditIA.")
    st.stop()

# ==================== GUIA DO USUÁRIO (SIDEBAR) ====================
with st.sidebar:
    st.header("📚 Guia Completo de Uso")

    with st.expander("🎯 O que é o AuditIA?"):
        st.markdown("""
        O **AuditIA** é uma plataforma de **Inteligência Forense Digital** que combina:

        - 🤖 **IA Avançada** (Gemini)
        - 🔍 **Análise Multimodal** (imagens, e-mails, PDFs)
        - 🎭 **Psicologia Forense** (detecção de manipulação)
        - 🔐 **Verificação Técnica** (metadados, autenticação)

        **Desenvolvido para:**
        - ✅ Auditores e peritos
        - ✅ Profissionais de segurança
        - ✅ Pessoas comuns que precisam verificar conteúdos suspeitos
        """)

    with st.expander("📤 Como Enviar Arquivos?"):
        st.markdown("""
        ### Formatos Suportados:

        **Imagens:**
        - 📸 JPG, JPEG, PNG
        - Ideal para: prints de conversas, fotos, documentos digitalizados

        **E-mails:**
        - 📧 EML (e-mail individual)
        - 📦 PST (arquivo Outlook)
        - Ideal para: investigar phishing, verificar autenticidade

        **Documentos:**
        - 📄 PDF
        - Ideal para: contratos, boletos, recibos

        ### Dicas:
        - 💡 Envie arquivos de alta qualidade
        - 💡 Múltiplos arquivos podem ser analisados juntos
        - 💡 Faça perguntas específicas para análises mais direcionadas
        """)

    with st.expander("🎨 Entenda as Cores"):
        st.markdown("""
        O AuditIA usa um **sistema de semáforo** para classificar riscos:

        🔴 **VERMELHO - Fraude Confirmada**
        - Golpe detectado com alta certeza
        - Não prossiga com a transação
        - Reporte às autoridades

        🟠 **LARANJA - Possível Fraude**
        - Múltiplos indicadores suspeitos
        - Exercite extrema cautela
        - Busque segunda opinião

        🟡 **AMARELO - Atenção**
        - Algumas inconsistências detectadas
        - Análise adicional necessária
        - Não confie cegamente

        🟢 **VERDE - Seguro**
        - Integridade confirmada
        - Autenticidade provável
        - Baixo risco de fraude

        🔵 **AZUL - Informativo**
        - Análise neutra
        - Sem sinais claros de fraude
        """)

    with st.expander("🔍 Tipos de Análise"):
        st.markdown("""
        ### 1. Detecção de Deepfake/IA
        - Identifica imagens geradas por IA
        - Verifica anatomia, iluminação, texturas
        - Detecta artefatos de processamento

        ### 2. Análise de Phishing
        - Examina linguagem manipulativa
        - Verifica autenticidade do remetente
        - Identifica técnicas de engenharia social

        ### 3. Validação Documental
        - Detecta edições e montagens
        - Verifica consistência de fontes
        - Analisa metadados ocultos

        ### 4. Investigação de E-mails
        - Verifica SPF, DKIM, DMARC
        - Analisa cabeçalhos técnicos
        - Examina conteúdo e contexto

        ### 5. Análise de Esquemas Ponzi
        - Identifica promessas irreais
        - Detecta linguagem típica de pirâmides
        - Avalia sustentabilidade de modelos de negócio
        """)

    with st.expander("⚡ Perguntas Frequentes"):
        st.markdown("""
        **Q: O AuditIA substitui um perito oficial?**
        A: Não. É uma ferramenta de apoio para análise inicial.

        **Q: Os resultados podem ser usados em processos legais?**
        A: Recomendamos validação com perícia oficial para uso judicial.

        **Q: Meus arquivos ficam armazenados?**
        A: Não. Processamento é temporário e os dados não são salvos.

        **Q: Qual a precisão das análises?**
        A: Alta, mas não 100%. Sempre use julgamento crítico.

        **Q: Posso analisar múltiplos arquivos?**
        A: Sim! Envie vários arquivos relacionados ao mesmo caso.

        **Q: Como reportar um problema?**
        A: Entre em contato com a equipe de desenvolvimento.
        """)

    st.info("💡 **Dica:** Quanto mais contexto você fornecer, melhor será a análise!")

# ==================== ÁREA DE UPLOAD ====================
st.header("📂 Upload de Arquivos para Análise")

arquivos = st.file_uploader(
    "Selecione os arquivos para análise forense",
    type=["jpg", "jpeg", "png", "pdf", "eml", "pst"],
    accept_multiple_files=True,
    help="Suporte para imagens, PDFs e e-mails (.eml, .pst)"
)

# Campo de pergunta
pergunta = st.text_area(
    "💬 Pergunta Específica (Opcional)",
    placeholder="Ex: Este e-mail é legítimo? Esta imagem foi manipulada? Este documento é autêntico?",
    key="campo_pergunta",
    help="Faça perguntas específicas para direcionar a análise"
)

# Botões de ação organizados
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

            # Miniatura da imagem (se for imagem)
            if arquivo.type.startswith("image/"):
                img = Image.open(arquivo)
                img.thumbnail((300, 300))
                st.image(img, caption=arquivo.name, width=300)

            # Processar análise
            if arquivo.type in ["image/jpeg", "image/png", "image/jpg"]:
                resultado = analisar_imagem(arquivo, st.session_state.pergunta_ativa)
            elif arquivo.type == "message/rfc822" or arquivo.name.endswith(".eml"):
                resultado = analisar_email(arquivo, st.session_state.pergunta_ativa)
            elif arquivo.type == "application/pdf":
                resultado = analisar_pdf(arquivo, st.session_state.pergunta_ativa)
            else:
                resultado = "❌ Formato de arquivo não suportado"

            # Exibir resultado com estilo
            html_resultado, cor, nivel = aplicar_estilo_pericial(resultado)
            st.markdown(html_resultado, unsafe_allow_html=True)

            # RESUMO DO RESULTADO - COERENTE E COMPLETO
            resumo = extrair_resumo(nivel)
            st.markdown(f'''
            <div class="resumo-final">
                <strong>📊 RESUMO DO RESULTADO</strong><br><br>
                <strong>Classificação:</strong> {nivel}<br><br>
                <strong>Conclusão:</strong> {resumo}
            </div>
            ''', unsafe_allow_html=True)

            # Adicionar ao histórico
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

# ==================== RODAPÉ ====================
st.markdown("---")
st.caption("👁️ AuditIA v2.0 | Desenvolvido em Vargem Grande do Sul - SP | © 2026")
st.caption("⚠️ Ferramenta de apoio - Não substitui perícia oficial")
