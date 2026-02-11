import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from email.parser import BytesParser
from datetime import datetime, timedelta
import pytz
import re
import os
import time
import hashlib

# ==================== CONFIGURAÇÃO INICIAL ====================
st.set_page_config(
    page_title="AuditIA - Inteligência Forense Digital",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================== RATE LIMITER ====================
class RateLimiter:
    """Controla chamadas à API para respeitar limite de 200/min"""
    def __init__(self, max_calls=180, period=60):  # 180 = margem de segurança
        self.max_calls = max_calls
        self.period = period
        if "rate_limiter_calls" not in st.session_state:
            st.session_state.rate_limiter_calls = []

    def wait_if_needed(self):
        """Aguarda se necessário para não exceder o limite"""
        now = datetime.now()

        # Remove chamadas antigas (mais de 60s)
        st.session_state.rate_limiter_calls = [
            c for c in st.session_state.rate_limiter_calls 
            if now - c < timedelta(seconds=self.period)
        ]

        # Verifica se atingiu o limite
        if len(st.session_state.rate_limiter_calls) >= self.max_calls:
            oldest_call = st.session_state.rate_limiter_calls[0]
            sleep_time = (oldest_call + timedelta(seconds=self.period) - now).total_seconds()

            if sleep_time > 0:
                st.warning(f"⏳ Aguardando {int(sleep_time)}s para respeitar limite de {self.max_calls} requisições/minuto...")
                time.sleep(sleep_time + 1)
                st.session_state.rate_limiter_calls = []

        # Registra nova chamada
        st.session_state.rate_limiter_calls.append(now)

        # Mostra uso atual
        current_usage = len(st.session_state.rate_limiter_calls)
        if current_usage > self.max_calls * 0.8:  # 80% do limite
            st.info(f"📊 Uso da API: {current_usage}/{self.max_calls} chamadas por minuto")

# Instância global
rate_limiter = RateLimiter()

# ==================== RETRY HANDLER ====================
def call_gemini_with_retry(func, max_retries=3):
    """Chama API com retry automático em caso de erro de quota"""
    for tentativa in range(max_retries):
        try:
            rate_limiter.wait_if_needed()
            return func()
        except Exception as e:
            error_msg = str(e)

            # Erro de quota
            if "RATE_LIMIT_EXCEEDED" in error_msg or "429" in error_msg or "quota" in error_msg.lower():
                if tentativa < max_retries - 1:
                    wait_time = 60 * (tentativa + 1)  # 60s, 120s, 180s
                    st.warning(f"⚠️ Limite de requisições atingido. Aguardando {wait_time}s... (Tentativa {tentativa + 1}/{max_retries})")
                    time.sleep(wait_time)
                    st.session_state.rate_limiter_calls = []  # Reseta contador
                else:
                    st.error(f"❌ Limite de quota excedido após {max_retries} tentativas. Aguarde alguns minutos e tente novamente.")
                    return None
            else:
                st.error(f"❌ Erro: {error_msg}")
                return None

    return None

# Configurar API do Gemini
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disponiveis = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    MODELO_USAR = modelos_disponiveis[0] if modelos_disponiveis else 'gemini-1.5-flash'
except Exception as e:
    st.error(f"⚠️ Erro ao configurar API: {str(e)}")
    st.stop()

# ==================== ESTILO VISUAL ====================
st.markdown('''
<style>
    :root {
        --verde-logo: #8BC34A;
        --verde-escuro: #689F38;
        --cinza-claro: #f5f5f5;
        --cinza-medio: #e0e0e0;
        --cinza-texto: #424242;
    }

    .main { background-color: white; }

    [data-testid="stSidebar"] { background-color: var(--cinza-claro); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] li { color: var(--cinza-texto) !important; }

    .stImage img { max-width: 1000px !important; width: 100% !important; height: auto !important; }

    h1 { font-size: 1.4rem !important; font-weight: 600 !important; color: var(--cinza-texto) !important; }

    .subtitle-custom { font-size: 0.95rem; color: #64748b; font-weight: 400; text-align: center; margin-bottom: 1.5rem; }

    .stButton > button { width: 100%; padding: 0.6rem 1rem; border-radius: 8px; font-weight: 500; transition: all 0.3s; border: 2px solid transparent; }

    div[data-testid="column"]:first-child .stButton > button {
        background-color: var(--verde-logo); color: white; border-color: var(--verde-logo);
    }

    div[data-testid="column"]:first-child .stButton > button:hover {
        background-color: var(--verde-escuro); border-color: var(--verde-escuro);
        transform: translateY(-2px); box-shadow: 0 4px 12px rgba(139, 195, 74, 0.3);
    }

    div[data-testid="column"]:nth-child(2) .stButton > button {
        background-color: white; color: var(--cinza-texto); border: 2px solid var(--cinza-medio);
    }

    div[data-testid="column"]:nth-child(2) .stButton > button:hover {
        background-color: #d32f2f; border-color: #d32f2f; color: white;
    }

    .termo-consentimento {
        background-color: var(--cinza-claro); border-left: 4px solid var(--verde-logo);
        padding: 1.5rem; border-radius: 8px; margin: 1rem 0;
    }

    .termo-consentimento h4, .termo-consentimento h5, .termo-consentimento p,
    .termo-consentimento ul, .termo-consentimento li { color: var(--cinza-texto) !important; }

    .stCheckbox { padding: 1rem; background-color: var(--cinza-claro); border-radius: 8px; }
    .stCheckbox label { color: var(--cinza-texto) !important; font-weight: 500 !important; }

    [data-testid="stFileUploader"] {
        background-color: #fafafa; border: 2px dashed var(--verde-logo);
        border-radius: 8px; padding: 1.5rem;
    }

    [data-testid="stFileUploader"] label { color: var(--cinza-texto) !important; font-weight: 500 !important; }

    .stTextArea textarea {
        background-color: #fafafa !important; border: 2px solid var(--cinza-medio) !important;
        border-radius: 8px !important; color: var(--cinza-texto) !important;
    }

    .stTextArea textarea:focus { border-color: var(--verde-logo) !important; }

    .veredito-titulo { font-size: 1.8rem !important; font-weight: 800 !important; margin-bottom: 0.5rem; }
    .classificacao-texto { font-size: 1.4rem !important; font-weight: 800 !important; margin: 0.8rem 0; }

    .resumo-final {
        background-color: #e8f5e9; border-left: 4px solid #4caf50;
        padding: 1.5rem; border-radius: 8px; margin: 1rem 0; color: #1b5e20 !important;
    }

    .resumo-final strong { color: #2e7d32 !important; font-size: 1.1rem; }

    .stProgress > div > div > div { background-color: var(--verde-logo) !important; }
</style>
''', unsafe_allow_html=True)

# ==================== GESTÃO DE SESSÃO ====================
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False
if "caso_id" not in st.session_state:
    st.session_state.caso_id = datetime.now().strftime("%Y%m%d%H%M%S")
if "limpar_trigger" not in st.session_state:
    st.session_state.limpar_trigger = 0
if "cache_analises" not in st.session_state:
    st.session_state.cache_analises = {}

def limpar_caso_completo():
    st.session_state.historico_pericial = []
    st.session_state.caso_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.limpar_trigger += 1
    st.session_state.cache_analises = {}
    st.session_state.rate_limiter_calls = []
    st.rerun()

def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    if "CLASSIFICAÇÃO: SEGURO" in texto_upper or "VEREDITO: SEGURO" in texto_upper:
        cor, font, nivel = "#388e3c", "white", "SEGURO"
    elif any(t in texto_upper for t in ["CLASSIFICAÇÃO: FRAUDE CONFIRMADA", "VEREDITO: FRAUDE CONFIRMADA", "PHISHING CONFIRMADO"]):
        cor, font, nivel = "#d32f2f", "white", "FRAUDE CONFIRMADA"
    elif any(t in texto_upper for t in ["CLASSIFICAÇÃO: POSSÍVEL FRAUDE", "VEREDITO: POSSÍVEL FRAUDE"]):
        cor, font, nivel = "#f57c00", "white", "POSSÍVEL FRAUDE"
    elif any(t in texto_upper for t in ["CLASSIFICAÇÃO: ATENÇÃO", "VEREDITO: ATENÇÃO", "GERADA POR IA"]):
        cor, font, nivel = "#fbc02d", "black", "ATENÇÃO"
    else:
        cor, font, nivel = "#1976d2", "white", "INFORMATIVO"

    texto_fmt = texto.replace("## 🎯 VEREDITO FINAL", '<div class="veredito-titulo">🎯 VEREDITO FINAL</div>')
    texto_fmt = re.sub(r'\*\*CLASSIFICAÇÃO: ([^*]+)\*\*', r'<div class="classificacao-texto"><strong>CLASSIFICAÇÃO: \1</strong></div>', texto_fmt)

    html = f'<div style="background-color: {cor}; color: {font}; padding: 2rem; border-radius: 12px; margin: 1.5rem 0; box-shadow: 0 4px 16px rgba(0,0,0,0.15);">{texto_fmt.replace(chr(10), "<br>")}</div>'
    return html, cor, nivel

def extrair_resumo(nivel):
    resumos = {
        "SEGURO": "Este conteúdo foi avaliado como legítimo e autêntico, com forte indicação de integridade.",
        "FRAUDE CONFIRMADA": "Foram identificados múltiplos sinais inequívocos de fraude confirmada. NÃO prosseguir.",
        "POSSÍVEL FRAUDE": "Existem vários elementos suspeitos indicando possível fraude. Tratar com extrema cautela.",
        "ATENÇÃO": "Foram observados pontos de atenção que exigem verificação adicional.",
        "INFORMATIVO": "Análise informativa concluída."
    }
    return resumos.get(nivel, "Análise concluída.")

def obter_prompt_analise(tipo_arquivo):
    base = '''Você é PERITO FORENSE DIGITAL. Seja RIGOROSO e CONCLUSIVO.

ESTRUTURA OBRIGATÓRIA:
## 🎯 VEREDITO FINAL
**CLASSIFICAÇÃO: [FRAUDE CONFIRMADA / POSSÍVEL FRAUDE / ATENÇÃO / SEGURO]**
[Explique em 2-3 linhas]

## 📋 ANÁLISE TÉCNICA
[Indicadores numerados]

## ⚠️ RECOMENDAÇÕES
[Ações específicas]'''

    if tipo_arquivo in ["image/jpeg", "image/png", "image/jpg"]:
        return base + '''

ANÁLISE DE IMAGENS - ATENÇÃO para fotos de PESSOAS:
Verifique SINAIS DE IA/DEEPFAKE: pele artificial, cabelos irreais, olhos inconsistentes, iluminação impossível, mãos anormais.
SE DETECTAR IA EM FOTO REAL → CLASSIFICAÇÃO: ATENÇÃO ou POSSÍVEL FRAUDE'''

    elif tipo_arquivo == "message/rfc822" or "eml" in tipo_arquivo.lower():
        return base + '''

ANÁLISE DE E-MAILS - PRIORIDADE: PHISHING
Verifique: urgência artificial, ameaças, remetente genérico, anexos suspeitos.
CRITÉRIOS:
- Remetente genérico + urgência = FRAUDE CONFIRMADA
- Anexo sem nome + assunto vago = FRAUDE CONFIRMADA'''

    return base

def gerar_hash_arquivo(arquivo):
    """Gera hash único do arquivo para cache"""
    arquivo.seek(0)
    file_hash = hashlib.md5(arquivo.read()).hexdigest()
    arquivo.seek(0)
    return file_hash

def analisar_imagem(image, pergunta=""):
    # Verifica cache
    file_hash = gerar_hash_arquivo(image)
    cache_key = f"img_{file_hash}_{pergunta}"

    if cache_key in st.session_state.cache_analises:
        st.info("♻️ Usando resultado em cache (economiza chamada à API)")
        return st.session_state.cache_analises[cache_key]

    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("image/jpeg")
        if pergunta:
            prompt += f"\n\n**PERGUNTA:** {pergunta}"

        def api_call():
            return model.generate_content([prompt, img]).text

        resultado = call_gemini_with_retry(api_call)

        if resultado:
            st.session_state.cache_analises[cache_key] = resultado

        return resultado or "❌ Não foi possível completar a análise"
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def analisar_email(arquivo, pergunta=""):
    file_hash = gerar_hash_arquivo(arquivo)
    cache_key = f"eml_{file_hash}_{pergunta}"

    if cache_key in st.session_state.cache_analises:
        st.info("♻️ Usando resultado em cache")
        return st.session_state.cache_analises[cache_key]

    try:
        msg = BytesParser(policy=policy.default).parsebytes(arquivo.getvalue())
        remetente = msg.get("From", "?")
        assunto = msg.get("Subject", "?")
        data = msg.get("Date", "?")

        corpo = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    corpo = part.get_payload(decode=True).decode(errors="ignore")
                    break
        else:
            corpo = msg.get_payload(decode=True).decode(errors="ignore")

        anexos = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    anexos.append(part.get_filename() or "sem_nome")

        contexto = f'''
=== E-MAIL ===
Remetente: {remetente}
Assunto: {assunto}
Data: {data}
Anexos: {", ".join(anexos) if anexos else "Nenhum"}

=== CONTEÚDO ===
{corpo[:3000]}

IMPORTANTE: Analise TODO o conteúdo.'''

        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("message/rfc822") + contexto
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"

        def api_call():
            return model.generate_content(prompt).text

        resultado = call_gemini_with_retry(api_call)

        if resultado:
            st.session_state.cache_analises[cache_key] = resultado

        return resultado or "❌ Não foi possível completar a análise"
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def analisar_pdf(arquivo, pergunta=""):
    file_hash = gerar_hash_arquivo(arquivo)
    cache_key = f"pdf_{file_hash}_{pergunta}"

    if cache_key in st.session_state.cache_analises:
        st.info("♻️ Usando resultado em cache")
        return st.session_state.cache_analises[cache_key]

    try:
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("application/pdf")
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"

        def api_call():
            return model.generate_content([prompt, arquivo.getvalue()]).text

        resultado = call_gemini_with_retry(api_call)

        if resultado:
            st.session_state.cache_analises[cache_key] = resultado

        return resultado or "❌ Não foi possível completar a análise"
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def gerar_pdf(resultado, nome_arquivo, nivel):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "AuditIA - Relatorio Forense Digital", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Arquivo: {nome_arquivo}", ln=True)
    pdf.cell(0, 6, f"Data: {datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(0, 6, f"Classificacao: {nivel}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "", 9)
    texto_limpo = resultado.replace("**", "")
    texto_limpo = re.sub(r'#+\s', '', texto_limpo)

    for linha in texto_limpo.split("\n"):
        if linha.strip():
            try:
                pdf.multi_cell(0, 5, linha.encode('latin-1', 'replace').decode('latin-1'))
            except:
                pdf.multi_cell(0, 5, linha)

    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 5, "AuditIA v3.0 FREE TIER - Vargem Grande do Sul, SP", ln=True, align="C")
    pdf.cell(0, 5, "Ferramenta de apoio - Nao substitui pericia oficial", ln=True, align="C")

    return pdf.output(dest='S').encode('latin-1')

# ==================== INTERFACE ====================

try:
    if os.path.exists("Logo_AI_1.png"):
        st.image(Image.open("Logo_AI_1.png"), use_column_width=True)
except:
    st.markdown("# 👁️ AuditIA")

st.markdown('<p class="subtitle-custom">Inteligência Forense Digital - Otimizado para FREE TIER (200 req/min)</p>', unsafe_allow_html=True)

with st.expander("⚖️ TERMO DE CONSENTIMENTO - LEIA ANTES DE USAR", expanded=not st.session_state.termo_aceito):
    st.markdown('''<div class="termo-consentimento">
    <h4>📜 Aviso Importante</h4>
    <p><strong>O AuditIA é ferramenta de apoio</strong>, não substitui perícia oficial.</p>
    <h5>⚠️ Responsabilidades</h5>
    <ul>
        <li>Você é responsável pelo uso dos resultados</li>
        <li>Não use como única evidência legal</li>
        <li>Respeite privacidade e direitos</li>
    </ul>
    <p><strong>Vargem Grande do Sul - SP | v3.0 FREE TIER - Fev 2026</strong></p>
    </div>''', unsafe_allow_html=True)

    if st.checkbox("✅ Li e concordo", value=st.session_state.termo_aceito, key="termo"):
        st.session_state.termo_aceito = True
        st.success("✅ Termo aceito!")
        st.rerun()

if not st.session_state.termo_aceito:
    st.warning("⚠️ Aceite o termo acima.")
    st.stop()

with st.sidebar:
    st.header("📚 Guia")

    with st.expander("🎯 O que é?"):
        st.write("Detecta deepfakes, phishing e fraudes")

    with st.expander("⚡ FREE TIER"):
        st.write('''
        **Otimizações:**
        - Rate limiting: 180 req/min
        - Cache de resultados
        - Retry automático
        - Processamento sequencial
        ''')

    with st.expander("🎨 Cores"):
        st.write("🔴 Fraude | 🟠 Possível | 🟡 Atenção | 🟢 Seguro")

    # Estatísticas
    st.markdown("---")
    st.subheader("📊 Estatísticas")
    total_analises = len(st.session_state.historico_pericial)
    cache_hits = len(st.session_state.cache_analises)
    st.metric("Análises Realizadas", total_analises)
    st.metric("Resultados em Cache", cache_hits)

    if st.session_state.rate_limiter_calls:
        uso_atual = len(st.session_state.rate_limiter_calls)
        st.metric("Uso API (último minuto)", f"{uso_atual}/180")

st.header("📂 Upload de Arquivos")

arquivos = st.file_uploader(
    "Selecione os arquivos (processados sequencialmente)",
    type=["jpg", "jpeg", "png", "pdf", "eml", "pst"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.limpar_trigger}"
)

pergunta = st.text_area("💬 Pergunta (Opcional)", placeholder="Ex: Este e-mail é phishing?", key="pergunta")

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("🔍 Analisar", use_container_width=True)
with col2:
    if st.button("🗑️ Limpar Tudo", use_container_width=True):
        limpar_caso_completo()

if analisar and arquivos:
    total_arquivos = len(arquivos)
    st.info(f"📦 Processando {total_arquivos} arquivo(s) sequencialmente...")

    # Barra de progresso
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, arq in enumerate(arquivos, 1):
        # Atualiza progresso
        progresso = idx / total_arquivos
        progress_bar.progress(progresso)
        status_text.text(f"Analisando {idx}/{total_arquivos}: {arq.name}")

        st.markdown(f"### 📄 {arq.name}")

        if arq.type.startswith("image/"):
            img = Image.open(arq)
            img.thumbnail((300, 300))
            st.image(img, width=300)

        with st.spinner(f"🔬 Analisando {idx}/{total_arquivos}..."):
            # Pequeno delay entre análises
            if idx > 1:
                time.sleep(0.5)

            if arq.type in ["image/jpeg", "image/png", "image/jpg"]:
                res = analisar_imagem(arq, pergunta)
            elif arq.type == "message/rfc822" or arq.name.endswith(".eml"):
                res = analisar_email(arq, pergunta)
            elif arq.type == "application/pdf":
                res = analisar_pdf(arq, pergunta)
            else:
                res = "❌ Formato não suportado"

            if res and res != "❌ Não foi possível completar a análise":
                html_res, cor, nivel = aplicar_estilo_pericial(res)
                st.markdown(html_res, unsafe_allow_html=True)

                st.markdown(f'''<div class="resumo-final">
                    <strong>📊 RESUMO</strong><br><br>
                    <strong>Classificação:</strong> {nivel}<br><br>
                    <strong>Conclusão:</strong> {extrair_resumo(nivel)}
                </div>''', unsafe_allow_html=True)

                pdf_bytes = gerar_pdf(res, arq.name, nivel)
                st.download_button(
                    "📥 Exportar PDF",
                    pdf_bytes,
                    f"Laudo_{arq.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    "application/pdf",
                    key=f"pdf_{arq.name}_{st.session_state.caso_id}_{idx}"
                )

                st.session_state.historico_pericial.append({
                    "arquivo": arq.name,
                    "resultado": res,
                    "nivel": nivel,
                    "timestamp": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
                })
            else:
                st.error(f"Não foi possível analisar {arq.name}")

            st.markdown("---")

    progress_bar.progress(1.0)
    status_text.text("✅ Processamento concluído!")
    st.success(f"🎉 {total_arquivos} arquivo(s) analisado(s) com sucesso!")

elif analisar:
    st.warning("⚠️ Envie pelo menos um arquivo.")

if st.session_state.historico_pericial:
    st.header("📊 Histórico de Análises")
    for i, item in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"#{i} - {item['arquivo']} | {item['nivel']}"):
            h, _, _ = aplicar_estilo_pericial(item['resultado'])
            st.markdown(h, unsafe_allow_html=True)

st.markdown("---")
st.caption("👁️ AuditIA v3.0 FREE TIER OPTIMIZED | Vargem Grande do Sul - SP")
st.caption("⚠️ Ferramenta de apoio - Não substitui perícia oficial")
st.caption("🆓 Otimizado para limite gratuito de 200 requisições/minuto")
