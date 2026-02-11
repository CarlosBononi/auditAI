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

st.set_page_config(
    page_title="AuditIA - Inteligência Forense Digital",
    page_icon="👁️",
    layout="centered",
    initial_sidebar_state="expanded"
)

class RateLimiterUltra:
    def __init__(self, max_calls=100, period=60):
        self.max_calls = max_calls
        self.period = period
        if "rate_limiter_calls" not in st.session_state:
            st.session_state.rate_limiter_calls = []

    def wait_if_needed(self):
        now = datetime.now()
        st.session_state.rate_limiter_calls = [
            c for c in st.session_state.rate_limiter_calls 
            if now - c < timedelta(seconds=self.period)
        ]

        if len(st.session_state.rate_limiter_calls) >= self.max_calls:
            oldest_call = st.session_state.rate_limiter_calls[0]
            sleep_time = (oldest_call + timedelta(seconds=self.period) - now).total_seconds()

            if sleep_time > 0:
                st.warning(f"Aguardando {int(sleep_time)}s para respeitar limite...")
                time.sleep(sleep_time + 2)
                st.session_state.rate_limiter_calls = []

        if st.session_state.rate_limiter_calls:
            time.sleep(1.5)

        st.session_state.rate_limiter_calls.append(now)

        current_usage = len(st.session_state.rate_limiter_calls)
        if current_usage > 80:
            st.info(f"Uso API: {current_usage}/100")

rate_limiter = RateLimiterUltra()

def detectar_modelo_disponivel():
    if "modelo_detectado" in st.session_state:
        return st.session_state.modelo_detectado

    modelos_tentar = [
        'gemini-1.5-flash',
        'gemini-1.5-flash-latest',
        'gemini-1.5-pro',
        'gemini-1.5-pro-latest',
        'gemini-pro',
        'gemini-pro-vision'
    ]

    for modelo in modelos_tentar:
        try:
            test_model = genai.GenerativeModel(modelo)
            test_model.generate_content("test")
            st.session_state.modelo_detectado = modelo
            return modelo
        except:
            continue

    st.session_state.modelo_detectado = 'gemini-1.5-flash-latest'
    return 'gemini-1.5-flash-latest'

def inicializar_api():
    try:
        if "api_configurada" not in st.session_state:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            st.session_state.api_configurada = True
    except Exception as e:
        st.error(f"Erro ao configurar API: {str(e)}")
        return False
    return True

def call_gemini_with_retry(func, max_retries=3):
    for tentativa in range(max_retries):
        try:
            rate_limiter.wait_if_needed()
            return func()
        except Exception as e:
            error_msg = str(e)
            if "RATE_LIMIT_EXCEEDED" in error_msg or "429" in error_msg or "quota" in error_msg.lower():
                if tentativa < max_retries - 1:
                    wait_time = 120 * (tentativa + 1)
                    st.error(f"LIMITE! Aguardando {wait_time}s... (Tentativa {tentativa + 1}/{max_retries})")
                    time.sleep(wait_time)
                    st.session_state.rate_limiter_calls = []
                else:
                    st.error("Quota excedida. AGUARDE 10 MINUTOS.")
                    return None
            else:
                st.error(f"Erro: {error_msg}")
                return None
    return None

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
    .stImage img { max-width: 1000px !important; width: 100% !important; }
    h1 { font-size: 1.4rem !important; font-weight: 600 !important; color: var(--cinza-texto) !important; }
    .subtitle-custom { 
        font-size: 0.95rem; color: #d32f2f; font-weight: 600; 
        text-align: center; margin-bottom: 1.5rem;
        background-color: #ffebee; padding: 0.5rem; border-radius: 4px;
    }
    .termo-consentimento {
        background-color: var(--cinza-claro); 
        border-left: 4px solid var(--verde-logo);
        padding: 1.5rem; border-radius: 8px; margin: 1rem 0;
    }
    .termo-consentimento h4, .termo-consentimento h5,
    .termo-consentimento p, .termo-consentimento ul, 
    .termo-consentimento li { color: var(--cinza-texto) !important; }
    .termo-consentimento ul { margin-left: 1.5rem; }
    .termo-consentimento li { margin-bottom: 0.5rem; }
    .veredito-titulo { font-size: 1.8rem !important; font-weight: 800 !important; }
    .classificacao-texto { font-size: 1.4rem !important; font-weight: 800 !important; }
    .resumo-final {
        background-color: #e8f5e9; border-left: 4px solid #4caf50;
        padding: 1.5rem; border-radius: 8px; color: #1b5e20 !important;
    }
    .resumo-final strong { color: #2e7d32 !important; font-size: 1.1rem; }
</style>
''', unsafe_allow_html=True)

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

def aceitar_termo():
    st.session_state.termo_aceito = True

def limpar_caso_completo():
    st.session_state.historico_pericial = []
    st.session_state.caso_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.limpar_trigger += 1
    st.session_state.cache_analises = {}
    st.session_state.rate_limiter_calls = []
    st.rerun()

def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    if "SEGURO" in texto_upper:
        cor, font, nivel = "#388e3c", "white", "SEGURO"
    elif "FRAUDE CONFIRMADA" in texto_upper or "PHISHING" in texto_upper:
        cor, font, nivel = "#d32f2f", "white", "FRAUDE CONFIRMADA"
    elif "POSSÍVEL FRAUDE" in texto_upper or "POSSIVEL FRAUDE" in texto_upper:
        cor, font, nivel = "#f57c00", "white", "POSSÍVEL FRAUDE"
    elif "ATENÇÃO" in texto_upper or "ATENCAO" in texto_upper or "IA" in texto_upper:
        cor, font, nivel = "#fbc02d", "black", "ATENÇÃO"
    else:
        cor, font, nivel = "#1976d2", "white", "INFORMATIVO"
    html = f'<div style="background-color: {cor}; color: {font}; padding: 2rem; border-radius: 12px; margin: 1.5rem 0;">{texto.replace(chr(10), "<br>")}</div>'
    return html, cor, nivel

def extrair_resumo(nivel):
    resumos = {
        "SEGURO": "Conteúdo legítimo e autêntico.",
        "FRAUDE CONFIRMADA": "Sinais de fraude confirmada. NÃO prosseguir.",
        "POSSÍVEL FRAUDE": "Elementos suspeitos. Extrema cautela.",
        "ATENÇÃO": "Pontos que exigem verificação.",
        "INFORMATIVO": "Análise concluída."
    }
    return resumos.get(nivel, "Análise concluída.")

def obter_prompt_analise(tipo_arquivo):
    base = '''Você é PERITO FORENSE DIGITAL. Seja RIGOROSO e CONCLUSIVO.

## 🎯 VEREDITO FINAL
**CLASSIFICAÇÃO: [FRAUDE CONFIRMADA / POSSÍVEL FRAUDE / ATENÇÃO / SEGURO]**
[Explique em 2-3 linhas porque]

## 📋 ANÁLISE TÉCNICA
[Liste até 5 indicadores técnicos]

## ⚠️ RECOMENDAÇÕES
[2-3 ações específicas]'''

    if tipo_arquivo in ["image/jpeg", "image/png", "image/jpg"]:
        return base + '''

ANÁLISE DE IMAGENS - ATENÇÃO ESPECIAL:
Verifique sinais de IA/DEEPFAKE: pele artificial, cabelos irreais, olhos inconsistentes, iluminação impossível.
SE DETECTAR IA EM FOTO REAL -> CLASSIFICAÇÃO: ATENÇÃO ou POSSÍVEL FRAUDE'''

    elif tipo_arquivo == "message/rfc822" or "eml" in tipo_arquivo.lower():
        return base + '''

ANÁLISE DE E-MAILS - PRIORIDADE: PHISHING
Verifique: urgência artificial, ameaças, remetente genérico, anexos suspeitos.
CRITÉRIOS:
- Remetente genérico + urgência = FRAUDE CONFIRMADA
- Anexo sem nome + assunto vago = FRAUDE CONFIRMADA
- Solicita dados pessoais/senha = FRAUDE CONFIRMADA'''

    return base

def gerar_hash_arquivo(arquivo):
    arquivo.seek(0)
    file_hash = hashlib.md5(arquivo.read()).hexdigest()
    arquivo.seek(0)
    return file_hash

def analisar_imagem(image, pergunta=""):
    file_hash = gerar_hash_arquivo(image)
    cache_key = f"img_{file_hash}_{pergunta}"
    if cache_key in st.session_state.cache_analises:
        st.success("♻️ Resultado em CACHE - 0 chamadas!")
        return st.session_state.cache_analises[cache_key]
    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))
        if not inicializar_api():
            return "Erro na API"

        modelo = detectar_modelo_disponivel()
        model = genai.GenerativeModel(modelo)

        prompt = obter_prompt_analise("image/jpeg")
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"

        resultado = call_gemini_with_retry(lambda: model.generate_content([prompt, img]).text)

        if resultado:
            st.session_state.cache_analises[cache_key] = resultado

        return resultado or "Não foi possível analisar"
    except Exception as e:
        return f"Erro: {str(e)}"

def analisar_email(arquivo, pergunta=""):
    file_hash = gerar_hash_arquivo(arquivo)
    cache_key = f"eml_{file_hash}_{pergunta}"
    if cache_key in st.session_state.cache_analises:
        st.success("♻️ Resultado em CACHE - 0 chamadas!")
        return st.session_state.cache_analises[cache_key]
    try:
        msg = BytesParser(policy=policy.default).parsebytes(arquivo.getvalue())
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
        anexos = []
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_disposition() == "attachment":
                    anexos.append(part.get_filename() or "sem_nome")
        contexto = f'''
=== E-MAIL ===
Remetente: {remetente}
Assunto: {assunto}
Anexos: {", ".join(anexos) if anexos else "Nenhum"}

=== CONTEÚDO ===
{corpo[:2000]}

IMPORTANTE: Analise TODO o conteúdo do e-mail acima.'''
        if not inicializar_api():
            return "Erro na API"

        modelo = detectar_modelo_disponivel()
        model = genai.GenerativeModel(modelo)

        prompt = obter_prompt_analise("message/rfc822") + contexto
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"

        resultado = call_gemini_with_retry(lambda: model.generate_content(prompt).text)

        if resultado:
            st.session_state.cache_analises[cache_key] = resultado

        return resultado or "Não foi possível"
    except Exception as e:
        return f"Erro: {str(e)}"

def gerar_pdf(resultado, nome_arquivo, nivel):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "AuditIA - Relatorio Forense", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Arquivo: {nome_arquivo}", ln=True)
    pdf.cell(0, 6, f"Classificacao: {nivel}", ln=True)
    pdf.cell(0, 6, f"Data: {datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d/%m/%Y %H:%M')}", ln=True)
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
    pdf.cell(0, 5, "AuditIA v3.0 AUTO-DETECT", ln=True, align="C")
    pdf.cell(0, 5, "Vargem Grande do Sul - SP", ln=True, align="C")
    return pdf.output(dest='S').encode('latin-1')

try:
    if os.path.exists("Logo_AI_1.png"):
        st.image(Image.open("Logo_AI_1.png"), use_column_width=True)
except:
    st.markdown("# 👁️ AuditIA")

st.markdown('<p class="subtitle-custom">MODO ULTRA-ECONOMICO: 100 req/min | Auto-detecção de modelo</p>', unsafe_allow_html=True)

if not st.session_state.termo_aceito:
    st.markdown("## TERMO DE CONSENTIMENTO")
    st.markdown('''<div class="termo-consentimento">
    <h4>Aviso Legal Importante</h4>
    <p><strong>O AuditIA é uma ferramenta de apoio</strong> e <strong>NÃO substitui perícia oficial</strong>.</p>
    <h5>Responsabilidades do Usuário</h5>
    <ul>
        <li>Você é <strong>totalmente responsável</strong> pelo uso das análises geradas</li>
        <li>Os resultados <strong>não devem ser usados como única evidência</strong> em processos legais</li>
        <li>Respeite a <strong>privacidade</strong> e os <strong>direitos autorais</strong></li>
        <li>Use a ferramenta de forma <strong>ética e legal</strong></li>
    </ul>
    <h5>Política de Privacidade</h5>
    <ul>
        <li>Os arquivos são processados temporariamente</li>
        <li>Não armazenamos dados permanentemente</li>
        <li>Utiliza Google Gemini AI</li>
    </ul>
    <h5>Informações</h5>
    <p><strong>Desenvolvido em:</strong> Vargem Grande do Sul - SP<br>
    <strong>Versão:</strong> 3.0 AUTO-DETECT - Fevereiro 2026<br>
    <strong>Limite:</strong> 100 requisições/minuto (ULTRA CONSERVADOR)</p>
    </div>''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("LI E CONCORDO - ENTRAR", key="aceitar", use_container_width=True, type="primary"):
            aceitar_termo()
            st.rerun()
    st.stop()

with st.sidebar:
    st.header("Informacoes")

    if "modelo_detectado" in st.session_state:
        st.success(f"Modelo: {st.session_state.modelo_detectado}")

    st.warning("""
MODO ULTRA-ECONOMICO

- Maximo 2 arquivos por vez
- Delay de 1.5s entre chamadas
- Limite: 100 req/min
- Cache agressivo
- Auto-detecção de modelo

Use com CALMA!
""")
    st.markdown("---")
    st.subheader("Estatisticas")
    st.metric("Analises", len(st.session_state.historico_pericial))
    st.metric("Cache", len(st.session_state.cache_analises))
    if st.session_state.rate_limiter_calls:
        st.metric("Uso API", f"{len(st.session_state.rate_limiter_calls)}/100")

st.header("Upload de Arquivos")
st.info("DICA: Analise 1-2 arquivos por vez. Aguarde completar antes de enviar mais.")

arquivos = st.file_uploader(
    "Selecione os arquivos (maximo 2 recomendado)",
    type=["jpg", "jpeg", "png", "pdf", "eml"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.limpar_trigger}"
)

if arquivos and len(arquivos) > 2:
    st.error("MODO ECONOMICO: Maximo 2 arquivos por vez!")
    arquivos = arquivos[:2]

pergunta = st.text_area("Pergunta Adicional (Opcional)", placeholder="Ex: Este e-mail e phishing?", key="pergunta")

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("Analisar Arquivos", use_container_width=True, type="primary")
with col2:
    if st.button("Limpar Tudo", use_container_width=True):
        limpar_caso_completo()

if analisar and arquivos:
    total = len(arquivos)
    st.warning(f"Processando {total} arquivo(s) LENTAMENTE para evitar erro de quota...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    for idx, arq in enumerate(arquivos, 1):
        progresso = idx / total
        progress_bar.progress(progresso)
        status_text.text(f"Analisando {idx}/{total}: {arq.name} (AGUARDE...)")
        st.markdown(f"### {arq.name}")
        if arq.type.startswith("image/"):
            img = Image.open(arq)
            img.thumbnail((300, 300))
            st.image(img, width=300)
        with st.spinner(f"Analise {idx}/{total} em andamento (modo LENTO)..."):
            if idx > 1:
                st.info("Pausa de seguranca (3s)...")
                time.sleep(3)
            if arq.type in ["image/jpeg", "image/png", "image/jpg"]:
                res = analisar_imagem(arq, pergunta)
            elif arq.type == "message/rfc822" or arq.name.endswith(".eml"):
                res = analisar_email(arq, pergunta)
            else:
                res = "Formato nao suportado"
            if res and "Erro" not in res:
                html_res, cor, nivel = aplicar_estilo_pericial(res)
                st.markdown(html_res, unsafe_allow_html=True)
                st.markdown(f'''<div class="resumo-final">
                    <strong>RESUMO</strong><br><br>
                    <strong>Classificacao:</strong> {nivel}<br><br>
                    <strong>Conclusao:</strong> {extrair_resumo(nivel)}
                </div>''', unsafe_allow_html=True)
                pdf_bytes = gerar_pdf(res, arq.name, nivel)
                st.download_button(
                    "Exportar Laudo em PDF",
                    pdf_bytes,
                    f"Laudo_{arq.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    "application/pdf",
                    key=f"pdf_{idx}"
                )
                st.session_state.historico_pericial.append({
                    "arquivo": arq.name,
                    "resultado": res,
                    "nivel": nivel,
                    "timestamp": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
                })
            else:
                st.error(f"Nao foi possivel analisar {arq.name}: {res}")
            st.markdown("---")
    progress_bar.progress(1.0)
    status_text.text("Processamento concluido!")
    st.success(f"{total} arquivo(s) analisado(s) com sucesso!")
    st.info("AGUARDE 3-5 MINUTOS antes de analisar mais arquivos.")
elif analisar:
    st.warning("Envie pelo menos um arquivo.")

if st.session_state.historico_pericial:
    st.header("Historico de Analises")
    for i, item in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"#{i} - {item['arquivo']} | {item['nivel']} | {item['timestamp']}"):
            h, _, _ = aplicar_estilo_pericial(item['resultado'])
            st.markdown(h, unsafe_allow_html=True)

st.markdown("---")
st.caption("AuditIA v3.0 AUTO-DETECT | Vargem Grande do Sul - SP")
st.caption("Ferramenta de apoio - Nao substitui pericia oficial")
st.caption("Detecta automaticamente o modelo Gemini disponivel")
