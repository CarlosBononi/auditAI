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

    modelo_nome = None
    try:
        modelo_nome = 'gemini-1.5-flash'
        model = genai.GenerativeModel(modelo_nome)
    except:
        try:
            modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

            if modelos:
                modelo_nome = modelos[0]
                if modelo_nome.startswith('models/'):
                    modelo_nome = modelo_nome.replace('models/', '')

                model = genai.GenerativeModel(modelo_nome)
            else:
                st.error("Nenhum modelo disponivel")
                st.stop()
        except Exception as e:
            st.error(f"Erro ao carregar modelo: {str(e)}")
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
if "contador" not in st.session_state:
    st.session_state.contador = 0

def aceitar():
    st.session_state.termo_aceito = True

def limpar():
    st.session_state.historico = []
    st.session_state.contador += 1
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
[Liste 5 indicadores tecnicos]

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

if modelo_nome:
    st.sidebar.success(f"Modelo: {modelo_nome}")

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
    <strong>Versao:</strong> 3.2 CORRIGIDO</p>
    </div>''', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("LI E CONCORDO - ENTRAR", on_click=aceitar, use_container_width=True, type="primary", key="btn_aceitar")
    st.stop()

# SIDEBAR
with st.sidebar:
    st.header("Dashboard")
    st.metric("Analises Realizadas", len(st.session_state.historico))
    st.info("Versao Estavel e Corrigida")

# UPLOAD
st.header("Upload de Arquivos")
st.info("Analise 1-2 arquivos por vez para melhor desempenho")

# Upload com key única
arquivos = st.file_uploader(
    "Selecione arquivos para analise",
    type=["jpg", "jpeg", "png", "eml"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state.contador}"
)

if arquivos and len(arquivos) > 2:
    st.warning("Recomendamos maximo 2 arquivos por vez")
    arquivos = arquivos[:2]

# Campo de pergunta com key única
pergunta = st.text_area(
    "Pergunta Adicional (Opcional)", 
    placeholder="Ex: Este e-mail e phishing?",
    key=f"pergunta_{st.session_state.contador}"
)

col1, col2 = st.columns(2)
with col1:
    # Botão analisar com key única
    analisar = st.button(
        "Analisar Arquivos", 
        use_container_width=True, 
        type="primary",
        key=f"btn_analisar_{st.session_state.contador}"
    )
with col2:
    # Botão limpar com key única
    st.button(
        "Limpar Historico", 
        on_click=limpar,
        use_container_width=True,
        key=f"btn_limpar_{st.session_state.contador}"
    )

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
            # Download button com key única
            st.download_button(
                "Exportar Laudo em PDF",
                pdf_bytes,
                f"Laudo_{arq.name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "application/pdf",
                key=f"pdf_{st.session_state.contador}_{idx}"
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
    st.info("Analise concluida! Voce pode baixar os laudos em PDF acima.")

elif analisar:
    st.warning("Faca upload de pelo menos um arquivo")

# HISTORICO
if st.session_state.historico:
    st.header("Historico de Analises")
    for i, item in enumerate(st.session_state.historico, 1):
        # Expander com key única
        with st.expander(
            f"#{i} - {item['arquivo']} | {item['nivel']} | {item['timestamp']}",
            expanded=False
        ):
            h, _ = aplicar_estilo(item['resultado'])
            st.markdown(h, unsafe_allow_html=True)

st.markdown("---")
st.caption("AuditIA v3.2 CORRIGIDO | Vargem Grande do Sul - SP")
st.caption("Ferramenta de apoio - Nao substitui pericia oficial")
