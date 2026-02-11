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
    st.error(f"⚠️ Erro ao configurar API: {str(e)}")
    st.stop()

# ==================== ESTILO VISUAL PROFISSIONAL ====================
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

    .stAlert { background-color: #fff3cd !important; border-left: 4px solid #ffc107 !important; color: #856404 !important; }
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

def limpar_caso_completo():
    st.session_state.historico_pericial = []
    st.session_state.caso_id = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.limpar_trigger += 1
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
        "SEGURO": "Este conteúdo foi avaliado como legítimo e autêntico, com forte indicação de integridade e ausência de sinais de fraude.",
        "FRAUDE CONFIRMADA": "Foram identificados múltiplos sinais inequívocos de fraude confirmada. NÃO prosseguir e reportar às autoridades.",
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

ANÁLISE DE IMAGENS - ATENÇÃO MÁXIMA para fotos de PESSOAS:

Verifique SINAIS DE IA/DEEPFAKE:
- Pele artificial, cabelos irreais, olhos inconsistentes
- Iluminação impossível, fundos distorcidos
- Mãos/dedos anormais, artefatos de rede neural

SE DETECTAR IA EM FOTO REAL → CLASSIFICAÇÃO: ATENÇÃO ou POSSÍVEL FRAUDE'''

    elif tipo_arquivo == "message/rfc822" or "eml" in tipo_arquivo.lower():
        return base + '''

ANÁLISE DE E-MAILS - PRIORIDADE: PHISHING

Verifique OBRIGATORIAMENTE:
1. CONTEÚDO: Urgência, ameaças, promessas irreais, pedidos de dados
2. REMETENTE: Domínio genérico, nome suspeito
3. ANEXOS: Sem nome, extensões suspeitas
4. AUTENTICAÇÃO: SPF, DKIM

CRITÉRIOS DE PHISHING:
- Remetente genérico + urgência = FRAUDE CONFIRMADA
- Anexo sem nome + assunto vago = FRAUDE CONFIRMADA'''

    return base

def analisar_imagem(image, pergunta=""):
    try:
        img = Image.open(image)
        img.thumbnail((1024, 1024))
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("image/jpeg")
        if pergunta:
            prompt += f"\n\n**PERGUNTA:** {pergunta}"
        return model.generate_content([prompt, img]).text
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def analisar_email(arquivo, pergunta=""):
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

IMPORTANTE: Analise TODO o conteúdo acima.'''

        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("message/rfc822") + contexto
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"
        return model.generate_content(prompt).text
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def analisar_pdf(arquivo, pergunta=""):
    try:
        model = genai.GenerativeModel(MODELO_USAR)
        prompt = obter_prompt_analise("application/pdf")
        if pergunta:
            prompt += f"\n\nPERGUNTA: {pergunta}"
        return model.generate_content([prompt, arquivo.getvalue()]).text
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
    pdf.cell(0, 5, "AuditIA v3.0 - Vargem Grande do Sul, SP", ln=True, align="C")
    pdf.cell(0, 5, "Ferramenta de apoio - Nao substitui pericia oficial", ln=True, align="C")

    return pdf.output(dest='S').encode('latin-1')

# ==================== INTERFACE ====================

try:
    if os.path.exists("Logo_AI_1.png"):
        st.image(Image.open("Logo_AI_1.png"), use_column_width=True)
except:
    st.markdown("# 👁️ AuditIA")

st.markdown('<p class="subtitle-custom">Inteligência Forense Digital</p>', unsafe_allow_html=True)

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
    <p><strong>Vargem Grande do Sul - SP | v3.0 - Fev 2026</strong></p>
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
    with st.expander("🎨 Cores"):
        st.write("🔴 Fraude | 🟠 Possível | 🟡 Atenção | 🟢 Seguro")

st.header("📂 Upload de Arquivos")

arquivos = st.file_uploader(
    "Selecione os arquivos",
    type=["jpg", "jpeg", "png", "pdf", "eml", "pst"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.limpar_trigger}"
)

pergunta = st.text_area("💬 Pergunta (Opcional)", placeholder="Ex: Este e-mail é phishing?", key="pergunta")

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("🔍 Analisar", use_container_width=True)
with col2:
    if st.button("🗑️ Limpar", use_container_width=True):
        limpar_caso_completo()

if analisar and arquivos:
    for arq in arquivos:
        st.markdown(f"### 📄 {arq.name}")

        if arq.type.startswith("image/"):
            img = Image.open(arq)
            img.thumbnail((300, 300))
            st.image(img, width=300)

        with st.spinner("🔬 Analisando..."):
            if arq.type in ["image/jpeg", "image/png", "image/jpg"]:
                res = analisar_imagem(arq, pergunta)
            elif arq.type == "message/rfc822" or arq.name.endswith(".eml"):
                res = analisar_email(arq, pergunta)
            elif arq.type == "application/pdf":
                res = analisar_pdf(arq, pergunta)
            else:
                res = "❌ Formato não suportado"

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
                key=f"pdf_{arq.name}_{st.session_state.caso_id}"
            )

            st.session_state.historico_pericial.append({
                "arquivo": arq.name,
                "resultado": res,
                "nivel": nivel,
                "timestamp": datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M")
            })

            st.markdown("---")

elif analisar:
    st.warning("⚠️ Envie arquivos.")

if st.session_state.historico_pericial:
    st.header("📊 Histórico")
    for i, item in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"#{i} - {item['arquivo']} | {item['nivel']}"):
            h, _, _ = aplicar_estilo_pericial(item['resultado'])
            st.markdown(h, unsafe_allow_html=True)

st.markdown("---")
st.caption("👁️ AuditIA v3.0 | Vargem Grande do Sul - SP")
st.caption("⚠️ Ferramenta de apoio - Não substitui perícia oficial")
