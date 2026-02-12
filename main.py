import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from email import policy
from email.parser import BytesParser
from datetime import datetime
import pytz
import re
import os
import time

st.set_page_config(
    page_title="AuditIA - Inteligencia Forense Digital",
    page_icon="👁️",
    layout="centered"
)

# ==================== CONFIGURAÇÃO API ====================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

    # TENTA CARREGAR MODELO - GARANTINDO REMOÇÃO DE "models/"
    modelo_nome = None
    try:
        # Tenta gemini-1.5-flash direto
        modelo_nome = 'gemini-1.5-flash'
        model = genai.GenerativeModel(modelo_nome)
        st.sidebar.success(f"Modelo: {modelo_nome}")
    except:
        try:
            # Lista modelos e REMOVE o prefixo "models/" se existir
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

            if modelos:
                # Pega o primeiro e REMOVE "models/" se tiver
                modelo_nome = modelos[0]
                if modelo_nome.startswith('models/'):
                    modelo_nome = modelo_nome.replace('models/', '')

                model = genai.GenerativeModel(modelo_nome)
                st.sidebar.success(f"Modelo: {modelo_nome}")
            else:
                st.error("Nenhum modelo disponivel")
                st.stop()
        except Exception as e:
            st.error(f"Erro ao carregar modelo: {str(e)}")
            st.error("DETALHES: Verifique se sua API KEY tem permissao para usar Gemini")
            st.stop()

except Exception as e:
    st.error(f"Erro ao configurar API: {str(e)}")
    st.stop()

# ==================== ESTILOS ====================
st.markdown('''
<style>
    :root {
        --verde-logo: #8BC34A;
        --cinza-claro: #f5f5f5;
        --cinza-texto: #424242;
    }
    .main { background-color: white; }
    [data-testid="stSidebar"] { background-color: var(--cinza-claro); }
    h1 { font-size: 1.4rem !important; color: var(--cinza-texto) !important; }
    .termo-consentimento {
        background-color: var(--cinza-claro); 
        border-left: 4px solid var(--verde-logo);
        padding: 1.5rem; border-radius: 8px; margin: 1rem 0;
    }
    .resumo-final {
        background-color: #e8f5e9; border-left: 4px solid #4caf50;
        padding: 1.5rem; border-radius: 8px;
    }
</style>
''', unsafe_allow_html=True)

# ==================== SESSION STATE ====================
if "historico" not in st.session_state:
    st.session_state.historico = []
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False

def aceitar():
    st.session_state.termo_aceito = True

def limpar():
    st.session_state.historico = []
    st.rerun()

# ==================== FUNÇÕES ====================
def aplicar_estilo(texto):
    texto_upper = texto.upper()
    if "SEGURO" in texto_upper:
        cor, nivel = "#388e3c", "SEGURO"
    elif "FRAUDE CONFIRMADA" in texto_upper or "PHISHING" in texto_upper:
        cor, nivel = "#d32f2f", "FRAUDE CONFIRMADA"
    elif "POSSÍVEL FRAUDE" in texto_upper or "POSSIVEL FRAUDE" in texto_upper:
        cor, nivel = "#f57c00", "POSSÍVEL FRAUDE"
    elif "ATENÇÃO" in texto_upper or "ATENCAO" in texto_upper:
        cor, nivel = "#fbc02d", "ATENÇÃO"
    else:
        cor, nivel = "#1976d2", "INFORMATIVO"

    html = f'<div style="background-color: {cor}; color: white; padding: 2rem; border-radius: 12px; margin: 1rem 0;">{texto.replace(chr(10), "<br>")}</div>'
    return html, nivel

def analisar_imagem(image, pergunta=""):
    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))

        prompt = '''Voce e PERITO FORENSE DIGITAL. Seja RIGOROSO.

## VEREDITO FINAL
**CLASSIFICACAO: [FRAUDE CONFIRMADA / POSSIVEL FRAUDE / ATENCAO / SEGURO]**
[Explique em 2-3 linhas]

## ANALISE TECNICA
[Liste 5 indicadores tecn icos]

## RECOMENDACOES
[2-3 acoes especificas]

Para imagens de pessoas: verifique sinais de IA/deepfake (pele artificial, olhos inconsistentes, iluminacao impossivel).'''

        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"

        time.sleep(2)
        resultado = model.generate_content([prompt, img], request_options={"timeout": 60})
        return resultado.text
    except Exception as e:
        return f"Erro: {str(e)}"

def analisar_email(arquivo, pergunta=""):
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

        contexto = f'''
=== E-MAIL ===
Remetente: {remetente}
Assunto: {assunto}

=== CONTEUDO ===
{corpo[:2000]}

Voce e PERITO FORENSE. Analise se e PHISHING ou FRAUDE.

## VEREDITO FINAL
**CLASSIFICACAO: [FRAUDE CONFIRMADA / POSSIVEL FRAUDE / ATENCAO / SEGURO]**

## ANALISE TECNICA
[5 indicadores]

## RECOMENDACOES
[2-3 acoes]'''

        if pergunta:
            contexto += f"\n\nPERGUNTA: {pergunta}"

        time.sleep(2)
        resultado = model.generate_content(contexto, request_options={"timeout": 60})
        return resultado.text
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
    texto_limpo = resultado.replace("**", "").replace("#", "")
    for linha in texto_limpo.split("\n"):
        if linha.strip():
            try:
                pdf.multi_cell(0, 5, linha.encode('latin-1', 'replace').decode('latin-1'))
            except:
                pdf.multi_cell(0, 5, linha)
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 5, "AuditIA - Vargem Grande do Sul - SP", ln=True, align="C")
    return pdf.output(dest='S').encode('latin-1')

# ==================== INTERFACE ====================
try:
    if os.path.exists("Logo_AI_1.png"):
        st.image(Image.open("Logo_AI_1.png"), use_column_width=True)
except:
    st.markdown("# AuditIA")

st.markdown("---")

# TERMO
if not st.session_state.termo_aceito:
    st.markdown("## TERMO DE CONSENTIMENTO")
    st.markdown('''<div class="termo-consentimento">
    <h4>Aviso Legal Importante</h4>
    <p><strong>O AuditIA e ferramenta de apoio.</strong> NAO substitui pericia oficial.</p>
    <h5>Responsabilidades</h5>
    <ul>
        <li>Voce e responsavel pelo uso das analises</li>
        <li>Nao use como unica evidencia em processos legais</li>
        <li>Respeite privacidade e direitos autorais</li>
        <li>Use de forma etica e legal</li>
    </ul>
    <h5>Informacoes</h5>
    <p><strong>Desenvolvido em:</strong> Vargem Grande do Sul - SP<br>
    <strong>Versao:</strong> 3.1 FIX DEFINITIVO</p>
    </div>''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("LI E CONCORDO - ENTRAR", use_container_width=True, type="primary"):
            aceitar()
            st.rerun()
    st.stop()

# SIDEBAR
with st.sidebar:
    st.header("Dashboard")
    st.metric("Analises Realizadas", len(st.session_state.historico))
    st.info("Versao Simplificada - Estavel")

# UPLOAD
st.header("Upload de Arquivos")
st.info("Analise 1-2 arquivos por vez para melhor desempenho")

arquivos = st.file_uploader(
    "Selecione arquivos para analise",
    type=["jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True
)

if arquivos and len(arquivos) > 2:
    st.warning("Recomendamos maximo 2 arquivos por vez")
    arquivos = arquivos[:2]

pergunta = st.text_area(
    "Pergunta Adicional (Opcional)", 
    placeholder="Ex: Este e-mail e phishing?"
)

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("Analisar Arquivos", use_container_width=True, type="primary")
with col2:
    if st.button("Limpar Historico", use_container_width=True):
        limpar()

# PROCESSAR
if analisar and arquivos:
    st.info(f"Processando {len(arquivos)} arquivo(s)...")
    progress = st.progress(0)

    for idx, arq in enumerate(arquivos, 1):
        progress.progress(idx / len(arquivos))

        st.markdown(f"### {arq.name}")

        if arq.type.startswith("image/"):
            img = Image.open(arq)
            img.thumbnail((300, 300))
            st.image(img, width=300)

            with st.spinner(f"Analisando imagem {idx}/{len(arquivos)}..."):
                res = analisar_imagem(arq, pergunta)

        elif arq.type == "message/rfc822" or arq.name.endswith(".eml"):
            with st.spinner(f"Analisando e-mail {idx}/{len(arquivos)}..."):
                res = analisar_email(arq, pergunta)
        else:
            res = "Formato nao suportado. Use JPG, PNG ou EML."

        if res and "Erro" not in res:
            html, nivel = aplicar_estilo(res)
            st.markdown(html, unsafe_allow_html=True)

            st.markdown(f'''<div class="resumo-final">
                <strong>RESUMO DA ANALISE</strong><br><br>
                <strong>Classificacao:</strong> {nivel}<br>
                <strong>Arquivo:</strong> {arq.name}
            </div>''', unsafe_allow_html=True)

            pdf_bytes = gerar_pdf(res, arq.name, nivel)
            st.download_button(
                "Exportar Laudo em PDF",
                pdf_bytes,
                f"Laudo_{arq.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "application/pdf",
                key=f"pdf_{idx}"
            )

            st.session_state.historico.append({
                "arquivo": arq.name,
                "resultado": res,
                "nivel": nivel,
                "timestamp": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
            })
        else:
            st.error(f"Nao foi possivel analisar {arq.name}")
            if res:
                st.error(f"Detalhes: {res}")

        st.markdown("---")

    progress.progress(1.0)
    st.success(f"{len(arquivos)} arquivo(s) analisado(s) com sucesso!")

elif analisar:
    st.warning("Faca upload de pelo menos um arquivo")

# HISTORICO
if st.session_state.historico:
    st.header("Historico de Analises")
    for i, item in enumerate(st.session_state.historico, 1):
        with st.expander(f"#{i} - {item['arquivo']} | {item['nivel']} | {item['timestamp']}"):
            h, _ = aplicar_estilo(item['resultado'])
            st.markdown(h, unsafe_allow_html=True)

st.markdown("---")
st.caption("AuditIA v3.1 FIX DEFINITIVO | Vargem Grande do Sul - SP")
st.caption("Ferramenta de apoio - Nao substitui pericia oficial")
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
    page_title="AuditIA - Inteligencia Forense Digital",
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

rate_limiter = RateLimiterUltra()

def inicializar_api():
    try:
        if "api_configurada" not in st.session_state:
            genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            st.session_state.api_configurada = True
            return True
    except Exception as e:
        st.error(f"Erro ao configurar API: {str(e)}")
        return False
    return True

def obter_modelo():
    if "modelo_gemini" in st.session_state:
        return st.session_state.modelo_gemini

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        st.session_state.modelo_gemini = model
        st.session_state.modelo_nome = 'gemini-1.5-flash'
        return model
    except:
        try:
            modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            if modelos_disp:
                nome_modelo = modelos_disp[0]
                model = genai.GenerativeModel(nome_modelo)
                st.session_state.modelo_gemini = model
                st.session_state.modelo_nome = nome_modelo
                return model
            else:
                st.error("Nenhum modelo disponivel")
                return None
        except Exception as e:
            st.error(f"Erro ao obter modelo: {str(e)}")
            return None

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
                    st.error(f"LIMITE! Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    st.session_state.rate_limiter_calls = []
                else:
                    st.error("Quota excedida. AGUARDE 10 MINUTOS.")
                    return None
            else:
                st.error(f"Erro na API: {error_msg}")
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
    if "modelo_gemini" in st.session_state:
        del st.session_state.modelo_gemini
    if "modelo_nome" in st.session_state:
        del st.session_state.modelo_nome
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
        "SEGURO": "Conteudo legitimo e autentico.",
        "FRAUDE CONFIRMADA": "Sinais de fraude confirmada. NAO prosseguir.",
        "POSSÍVEL FRAUDE": "Elementos suspeitos. Extrema cautela.",
        "ATENÇÃO": "Pontos que exigem verificacao.",
        "INFORMATIVO": "Analise concluida."
    }
    return resumos.get(nivel, "Analise concluida.")

def obter_prompt_analise(tipo_arquivo):
    base = '''Voce e PERITO FORENSE DIGITAL. Seja RIGOROSO e CONCLUSIVO.

## VEREDITO FINAL
**CLASSIFICACAO: [FRAUDE CONFIRMADA / POSSIVEL FRAUDE / ATENCAO / SEGURO]**
[Explique em 2-3 linhas porque]

## ANALISE TECNICA
[Liste ate 5 indicadores tecnicos]

## RECOMENDACOES
[2-3 acoes especificas]'''

    if tipo_arquivo in ["image/jpeg", "image/png", "image/jpg"]:
        return base + '''

ANALISE DE IMAGENS - ATENCAO ESPECIAL:
Verifique sinais de IA/DEEPFAKE: pele artificial, cabelos irreais, olhos inconsistentes, iluminacao impossivel.
SE DETECTAR IA EM FOTO REAL -> CLASSIFICACAO: ATENCAO ou POSSIVEL FRAUDE'''

    elif tipo_arquivo == "message/rfc822" or "eml" in tipo_arquivo.lower():
        return base + '''

ANALISE DE E-MAILS - PRIORIDADE: PHISHING
Verifique: urgencia artificial, ameacas, remetente generico, anexos suspeitos.
CRITERIOS:
- Remetente generico + urgencia = FRAUDE CONFIRMADA
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
        st.success("Resultado em CACHE - 0 chamadas!")
        return st.session_state.cache_analises[cache_key]

    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))

        if not inicializar_api():
            return "Erro na API"

        model = obter_modelo()
        if not model:
            return "Erro ao obter modelo"

        prompt = obter_prompt_analise("image/jpeg")
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"

        resultado = call_gemini_with_retry(lambda: model.generate_content([prompt, img]).text)

        if resultado:
            st.session_state.cache_analises[cache_key] = resultado

        return resultado or "Nao foi possivel analisar"
    except Exception as e:
        return f"Erro: {str(e)}"

def analisar_email(arquivo, pergunta=""):
    file_hash = gerar_hash_arquivo(arquivo)
    cache_key = f"eml_{file_hash}_{pergunta}"

    if cache_key in st.session_state.cache_analises:
        st.success("Resultado em CACHE - 0 chamadas!")
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

=== CONTEUDO ===
{corpo[:2000]}

IMPORTANTE: Analise TODO o conteudo do e-mail acima.'''

        if not inicializar_api():
            return "Erro na API"

        model = obter_modelo()
        if not model:
            return "Erro ao obter modelo"

        prompt = obter_prompt_analise("message/rfc822") + contexto
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"

        resultado = call_gemini_with_retry(lambda: model.generate_content(prompt).text)

        if resultado:
            st.session_state.cache_analises[cache_key] = resultado

        return resultado or "Nao foi possivel"
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
    pdf.cell(0, 5, "AuditIA v3.0 PRODUCTION", ln=True, align="C")
    pdf.cell(0, 5, "Vargem Grande do Sul - SP", ln=True, align="C")
    return pdf.output(dest='S').encode('latin-1')

try:
    if os.path.exists("Logo_AI_1.png"):
        st.image(Image.open("Logo_AI_1.png"), use_column_width=True)
except:
    st.markdown("# AuditIA")

st.markdown('<p class="subtitle-custom">MODO PRODUCTION: Otimizado para Vendas | 100 req/min</p>', unsafe_allow_html=True)

if not st.session_state.termo_aceito:
    st.markdown("## TERMO DE CONSENTIMENTO")
    st.markdown('''<div class="termo-consentimento">
    <h4>Aviso Legal Importante</h4>
    <p><strong>O AuditIA e uma ferramenta de apoio</strong> e <strong>NAO substitui pericia oficial</strong>.</p>
    <h5>Responsabilidades do Usuario</h5>
    <ul>
        <li>Voce e <strong>totalmente responsavel</strong> pelo uso das analises geradas</li>
        <li>Os resultados <strong>nao devem ser usados como unica evidencia</strong> em processos legais</li>
        <li>Respeite a <strong>privacidade</strong> e os <strong>direitos autorais</strong></li>
        <li>Use a ferramenta de forma <strong>etica e legal</strong></li>
    </ul>
    <h5>Politica de Privacidade</h5>
    <ul>
        <li>Os arquivos sao processados temporariamente</li>
        <li>Nao armazenamos dados permanentemente</li>
        <li>Utiliza Google Gemini AI</li>
    </ul>
    <h5>Informacoes</h5>
    <p><strong>Desenvolvido em:</strong> Vargem Grande do Sul - SP<br>
    <strong>Versao:</strong> 3.0 PRODUCTION READY - Fevereiro 2026<br>
    <strong>Limite:</strong> 100 requisicoes/minuto (OTIMIZADO)</p>
    </div>''', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("LI E CONCORDO - ENTRAR", key="aceitar", use_container_width=True, type="primary"):
            aceitar_termo()
            st.rerun()
    st.stop()

with st.sidebar:
    st.header("Dashboard")

    if "modelo_nome" in st.session_state:
        st.success(f"Modelo: {st.session_state.modelo_nome}")

    st.info("MODO PRODUCTION - Estavel e confiavel - Otimizado para vendas - Cache inteligente - Rate limiter 100/min")

    st.markdown("---")
    st.subheader("Estatisticas")
    st.metric("Analises Realizadas", len(st.session_state.historico_pericial))
    st.metric("Resultados em Cache", len(st.session_state.cache_analises))

    if st.session_state.rate_limiter_calls:
        uso = len(st.session_state.rate_limiter_calls)
        st.metric("Uso API (ultimo minuto)", f"{uso}/100")

        if uso > 80:
            st.warning("Proximo do limite")
        elif uso > 50:
            st.info("Uso moderado")

st.header("Upload de Arquivos")
st.info("DICA: Analise 1-2 arquivos por vez para melhor desempenho.")

arquivos = st.file_uploader(
    "Selecione os arquivos para analise forense",
    type=["jpg", "jpeg", "png", "pdf", "eml"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.limpar_trigger}"
)

if arquivos and len(arquivos) > 2:
    st.warning("Recomendamos maximo 2 arquivos por vez para analise otimizada.")
    arquivos = arquivos[:2]

pergunta = st.text_area(
    "Pergunta Adicional (Opcional)", 
    placeholder="Ex: Este e-mail e phishing? Analise os indicadores de fraude.", 
    key="pergunta"
)

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("Analisar Arquivos", use_container_width=True, type="primary")
with col2:
    if st.button("Limpar Tudo", use_container_width=True):
        limpar_caso_completo()

if analisar and arquivos:
    total = len(arquivos)
    st.info(f"Processando {total} arquivo(s)...")

    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, arq in enumerate(arquivos, 1):
        progresso = idx / total
        progress_bar.progress(progresso)
        status_text.text(f"Analisando {idx}/{total}: {arq.name}")

        st.markdown(f"### {arq.name}")

        if arq.type.startswith("image/"):
            img = Image.open(arq)
            img.thumbnail((300, 300))
            st.image(img, width=300)

        with st.spinner(f"Analise forense em andamento ({idx}/{total})..."):
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
                    <strong>RESUMO DA ANALISE</strong><br><br>
                    <strong>Classificacao:</strong> {nivel}<br><br>
                    <strong>Conclusao:</strong> {extrair_resumo(nivel)}
                </div>''', unsafe_allow_html=True)

                pdf_bytes = gerar_pdf(res, arq.name, nivel)
                st.download_button(
                    "Exportar Laudo em PDF",
                    pdf_bytes,
                    f"Laudo_AuditIA_{arq.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
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
                st.error(f"Nao foi possivel analisar {arq.name}")
                if res:
                    st.error(f"Detalhes: {res}")

            st.markdown("---")

    progress_bar.progress(1.0)
    status_text.text("Processamento concluido!")
    st.success(f"{total} arquivo(s) analisado(s) com sucesso!")
    st.info("Pronto para venda: Analise completa disponivel para download em PDF.")

elif analisar:
    st.warning("Por favor, faca upload de pelo menos um arquivo.")

if st.session_state.historico_pericial:
    st.header("Historico de Analises")
    for i, item in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"#{i} - {item['arquivo']} | {item['nivel']} | {item['timestamp']}"):
            h, _, _ = aplicar_estilo_pericial(item['resultado'])
            st.markdown(h, unsafe_allow_html=True)

st.markdown("---")
st.caption("AuditIA v3.0 PRODUCTION READY | Vargem Grande do Sul - SP")
st.caption("Ferramenta de apoio a decisao - Nao substitui pericia oficial certificada")
st.caption("Versao otimizada para vendas B2B e B2C")

