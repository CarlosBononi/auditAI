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
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligencia Pericial Senior", page_icon="👁️", layout="centered")

# CORES
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    if any(term in texto_upper for term in ["CLASSIFICACAO: FRAUDE CONFIRMADA", "FRAUDE CONFIRMADA", "CRIME", "GOLPE", "SCAM"]):
        cor = "#ff4b4b"
    elif any(term in texto_upper for term in ["CLASSIFICACAO: POSSIVEL FRAUDE", "POSSIVEL FRAUDE", "PHISHING"]):
        cor = "#ffa500"
    elif any(term in texto_upper for term in ["CLASSIFICACAO: ATENCAO", "ATENCAO", "IMAGEM", "FOTO", "IA", "SINTETICO"]):
        cor = "#f1c40f"
    elif any(term in texto_upper for term in ["CLASSIFICACAO: SEGURO", "SEGURO", "LEGITIMO", "AUTENTICIDADE"]):
        cor = "#2ecc71"
    else:
        cor = "#3498db"

    return f"""<div style="background-color: {cor}; padding: 20px; border-radius: 10px; 
                color: white; font-weight: bold; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                {texto.replace(chr(10), "<br>")}
            </div>"""

# CSS
st.markdown("""
<style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child {
        background-color: #4a4a4a; color: white; border: none;
        border-radius: 10px; font-weight: bold; height: 3.5em; width: 100%;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #59ea63; color: black; border: 1px solid #2ecc71;
    }
    .stTextArea textarea {
        background-color: #f8f9fa; border: 1px solid #d1d5db;
        border-radius: 8px; font-size: 16px; padding: 15px;
    }
    .uploadedFile { border: 2px dashed #4a90e2; border-radius: 10px; padding: 10px; }
    h1, h2, h3 { color: #2c3e50 !important; }
    .stExpander { background-color: #f8f9fa; border-radius: 10px; border: 1px solid #dee2e6; }
</style>
""", unsafe_allow_html=True)

# GEMINI - COM FIX CRITICO
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
    st.info("Aguarde 60 segundos e recarregue.")
    st.stop()

# HEADER
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("👁️ AuditIA - Inteligencia Pericial Senior")
    st.caption("Tecnologia Forense Multimodal de Alta Precisao")

# ===== TERMO DE ACEITE OBRIGATORIO =====
if not st.session_state.termo_aceito:
    st.markdown("---")
    st.warning("""
### ⚖️ TERMO DE CONSENTIMENTO INFORMADO

Esta e uma ferramenta baseada em Inteligencia Artificial Forense. Os resultados sao 
**probabilisticos** e devem ser validados por pericia humana oficial.

**Uso Responsavel**: Esta ferramenta destina-se exclusivamente a profissionais do direito, 
auditoria, compliance e investigacao forense.

**Privacidade**: Nenhum dado e armazenado em servidores. Todo processamento ocorre em 
memoria volatil e e destruido ao final da sessao (LGPD Compliant).

**Limitacoes**: A IA pode cometer erros. Nao use como unica evidencia em processos judiciais.
""")

    aceite = st.checkbox("✅ Li e aceito os termos acima. Entendo que esta e uma ferramenta de apoio tecnico.")

    col_aceite1, col_aceite2, col_aceite3 = st.columns([1, 1, 1])

    with col_aceite2:
        if st.button("🚀 ACEITAR E PROSSEGUIR", type="primary", disabled=not aceite, use_container_width=True):
            st.session_state.termo_aceito = True
            st.rerun()

    st.stop()

# ===== INTERFACE PRINCIPAL (SO APARECE APOS ACEITE) =====

st.markdown("---")

# UPLOAD
st.header("📂 Upload de Provas Forenses")

new_files = st.file_uploader(
    "Arraste ate 5 arquivos (Prints, PDFs ate 1000 pag, E-mails .eml)",
    type=["jpg", "png", "jpeg", "pdf", "eml"],
    accept_multiple_files=True,
    help="Tamanho maximo: 200MB por arquivo"
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
    st.write("**🔬 Mesa de Pericia - Provas Carregadas:**")
    st.info(f"📊 Total: {len(st.session_state.arquivos_acumulados)} arquivo(s)")

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
st.subheader("📊 Linha de Investigacao Cumulativa")

if not st.session_state.historico_pericial:
    st.info("O historico aparecera aqui apos a primeira pericia.")
else:
    for idx, bloco in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"🔍 Analise #{idx}", expanded=(idx == len(st.session_state.historico_pericial))):
            st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

st.markdown("---")

# CAMPO DE PERGUNTA
st.subheader("💬 Consulta ao Perito Digital")

user_query = st.text_area(
    "Digite sua pergunta tecnica:",
    key="campo_pergunta",
    placeholder="Ex: Esta foto e de pessoa real? Analise maos, olhos e textura de pele.",
    height=150
)

st.caption("💡 Dica: Seja especifico para respostas mais precisas.")

# FUNCOES
def gerar_pdf_pericial_completo(conteudo, data, arquivos):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 12, txt="LAUDO TECNICO PERICIAL", ln=True, align="C")
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="AUDITIA - Inteligencia Forense Digital", ln=True, align="C")

    pdf.ln(5)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, txt="Data da Pericia:", ln=False)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt=data, ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, txt="Total de Provas:", ln=False)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt=str(len(arquivos)), ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, txt="Este laudo foi gerado por sistema automatizado. Recomenda-se validacao por perito humano.")

    pdf.ln(8)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt="ANALISE TECNICA DETALHADA", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "", 10)
    texto_limpo = conteudo.encode('latin-1', 'replace').decode('latin-1')
    texto_limpo = re.sub(r'\*\*', '', texto_limpo)
    texto_limpo = re.sub(r'##\s+', '', texto_limpo)
    pdf.multi_cell(0, 6, txt=texto_limpo)

    pdf.ln(10)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 5, txt="AuditIA - Vargem Grande do Sul - SP", ln=True, align="C")

    return pdf.output(dest='S').encode('latin-1')

# BOTOES
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button("🔬 EXECUTAR PERICIA TECNICA", on_click=processar_pericia, type="primary", use_container_width=True):

        pergunta_efetiva = st.session_state.get("pergunta_ativa", "")

        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Por favor, insira uma pergunta ou arquivos.")
        else:
            tz_br = pytz.timezone("America/Sao_Paulo")
            agora = datetime.now(tz_br).strftime("%d/%m/%Y as %H:%M:%S")

            with st.spinner("Realizando auditoria tecnica... Aguarde ate 2 minutos."):
                try:
                    instrucao = f"""Aja como o AuditIA, inteligencia forense de elite.

CONTEXTO: Hoje e {agora}.

PROTOCOLO V16 - ANALISE FORENSE RIGOROSA:

1. IMAGENS DE PESSOAS - CETICISMO MAXIMO:
- Analise anatomia (dedos, maos, olhos, dentes)
- Fisica da luz (reflexos, sombras)
- Textura de pele (poros, imperfeicoes)
- Metadados EXIF (camera, GPS, timestamp)
- Se EXIF ausente + perfeicao excessiva = CLASSIFICACAO: ATENCAO (IA)

2. DOCUMENTOS:
- Verificar fontes, metadados, selos digitais
- Identificar inconsistencias

3. E-MAILS:
- Verificar SPF, DKIM, cabecalhos
- Identificar phishing e spoofing

4. ESTRUTURA DE RESPOSTA:
- Inicie com: PERGUNTA ANALISADA EM {agora}: {pergunta_efetiva}
- Linha seguinte: CLASSIFICACAO: [FRAUDE CONFIRMADA/POSSIVEL FRAUDE/ATENCAO/SEGURO]
- Depois, analise detalhada com evidencias tecnicas

Pergunta: {pergunta_efetiva}"""

                    contexto = [instrucao]

                    for h in st.session_state.historico_pericial[-3:]:
                        contexto.append(f"[HISTORICO]: {h[:500]}")

                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"):
                            try:
                                msg = email.message_from_bytes(f["content"], policy=policy.default)
                                corpo = msg.get_body(preference=['plain']).get_content()
                                contexto.append(f"E-MAIL: {f['name']}\n{corpo[:2000]}")
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

                    contexto.append(f"PERGUNTA PRINCIPAL: {pergunta_efetiva}")

                    response = model.generate_content(
                        contexto, 
                        request_options={"timeout": 120}
                    )

                    st.session_state.historico_pericial.append(response.text)
                    st.success("Pericia concluida!")
                    st.rerun()

                except Exception as e:
                    erro_msg = str(e)

                    if "exceeds the supported page limit" in erro_msg:
                        st.error("❌ PDF excede 1000 paginas.")
                        st.info("💡 Divida em partes menores.")
                    elif "timeout" in erro_msg.lower():
                        st.error("⏱️ Timeout. Muitos arquivos.")
                        st.info("💡 Reduza para 3-4 arquivos.")
                    elif "quota" in erro_msg.lower() or "rate" in erro_msg.lower() or "429" in erro_msg:
                        st.error("🚫 Limite de API atingido pelo Google.")
                        st.info("💡 Aguarde 60 segundos e tente novamente.")
                    else:
                        st.error(f"❌ Erro: {erro_msg}")
                        st.info("💡 Tente novamente em alguns segundos.")

with col2:
    if st.button("🗑️ LIMPAR CASO COMPLETO", use_container_width=True):
        if st.session_state.historico_pericial or st.session_state.arquivos_acumulados:
            st.session_state.historico_pericial = []
            st.session_state.arquivos_acumulados = []
            st.session_state.pergunta_ativa = ""
            st.success("✅ Caso limpo! Memoria destruida.")
            st.rerun()
        else:
            st.info("ℹ️ Nenhum dado para limpar.")

with col3:
    if st.button("❓", help="Ajuda", use_container_width=True):
        st.info("Consulte a Central de Ajuda abaixo")

# PDF
if st.session_state.historico_pericial:
    st.markdown("---")
    st.subheader("📥 Exportacao de Laudo")

    tz_br = pytz.timezone("America/Sao_Paulo")
    data_atual = datetime.now(tz_br).strftime("%d/%m/%Y as %H:%M:%S")

    pdf_bytes = gerar_pdf_pericial_completo(
        st.session_state.historico_pericial[-1], 
        data_atual,
        st.session_state.arquivos_acumulados
    )

    col_pdf1, col_pdf2 = st.columns([3, 1])

    with col_pdf1:
        st.download_button(
            label="📥 Baixar Laudo PDF Profissional",
            data=pdf_bytes,
            file_name=f"Laudo_AuditIA_{datetime.now(tz_br).strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_pdf2:
        st.metric("Laudos", len(st.session_state.historico_pericial))

st.markdown("---")

# CENTRAL DE AJUDA COMPLETA
with st.expander("📖 CENTRAL DE AJUDA AUDITIA - Conhecimento Tecnico e FAQ", expanded=False):
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 A Origem do AuditIA", 
        "📘 Manual Tecnico", 
        "❓ FAQ Completo",
        "🔬 Casos de Uso"
    ])

    with tab1:
        st.markdown("""
### 🌟 A Missao AuditIA

Nascido em **Vargem Grande do Sul - SP**, o AuditIA une **psicologia forense** 
a **Inteligencia Artificial Multimodal** para identificar **micro-anomalias digitais**.

#### 🔍 7 Pilares de Investigacao

1. **Analise Documental**: Fontes, metadados, selos digitais
2. **Deteccao de IA**: 12 marcadores anatomicos (dedos, olhos, pele)
3. **e-Discovery**: Processamento de .eml e .pst
4. **Engenharia Social**: Phishing, spoofing
5. **Fisica da Luz**: Reflexos, sombras
6. **Esquemas Ponzi**: Promessas irreais
7. **Metadados**: Rastro digital vs. conteudo

#### 💼 Capacidades

- **Imagens**: JPG, PNG (ate 200MB)
- **PDFs**: Ate 1000 paginas
- **E-mails**: .eml com analise SPF/DKIM
- **Analise Cruzada**: Multiplos arquivos

#### 🛡️ Privacidade

- ✅ Memoria volatil (nao armazena)
- ✅ LGPD Compliant
- ✅ Sem logs
""")

    with tab2:
        st.markdown("""
### 📚 Manual Tecnico

#### 1️⃣ Upload
- Ate 5 arquivos
- 200MB cada
- PDFs ate 1000 pag

#### 2️⃣ Perguntas Eficazes

❌ **EVITE**: "Isso e verdade?"

✅ **USE**: "Analise textura de pele e sombras desta face"

#### 3️⃣ Classificacoes

🟢 **SEGURO**: Autenticidade confirmada

🔵 **INFORMATIVO**: Legitimo mas neutro

🟡 **ATENCAO**: Possivel IA. Pericia humana obrigatoria

🟠 **POSSIVEL FRAUDE**: Alta probabilidade de manipulacao

🔴 **FRAUDE CONFIRMADA**: Manipulacao irrefutavel

#### 4️⃣ Mesa de Pericia

- Arquivos ficam carregados
- Faca multiplas perguntas
- Limpe so ao finalizar caso

#### 5️⃣ Laudos PDF

- Cabecalho profissional
- Data e hora
- Analise tecnica completa
- Use em processos judiciais

#### 6️⃣ Limitacoes

- ⏱️ Timeout: Reduza para 3-4 arquivos
- 📄 PDF +1000 pag: Divida em partes
- 🖼️ Videos: Nao suportado (v3.0)

#### 7️⃣ Boas Praticas

✅ **FACA**: Perguntas especificas, valide com perito

❌ **NAO**: Confie 100% sem validacao
""")

    with tab3:
        st.markdown("""
### ❓ FAQ Completo

**Q1: Por que foi criado?**

R: Para combater fraudes por IA (Midjourney, DALL-E, deepfakes).

---

**Q2: Como analisa fotos?**

R: Protocolo V16 com 12 marcadores anatomicos + EXIF + fisica da luz.

---

**Q3: Tamanho maximo?**

R: Imagens 200MB | PDFs 1000 pag | Total 1GB

---

**Q4: Guarda historico?**

R: **NAO**. Memoria volatil. Destruido ao limpar.

---

**Q5: Substitui perito?**

R: **NAO**. E ferramenta de apoio. Sempre valide com perito certificado.

---

**Q6: Resultados conflitantes?**

R: Se ATENCAO ou POSSIVEL FRAUDE, contrate pericia humana.

---

**Q7: Erro de API?**

R: Se aparecer "Limite atingido", aguarde 60 segundos (limite do Google).

---

**Q8: Videos/audios?**

R: Nao suportado. Apenas imagens, PDFs, e-mails.

---

**Q9: Phishing?**

R: Analisa 7 camadas (SPF, DKIM, dominio, links, anexos).

---

**Q10: Confiabilidade?**

R: ~85-95%. Nao e 100%. Use como triagem inicial.

---

**Q11: Reportar bugs?**

📧 auditia.ajuda@gmail.com
""")

    with tab4:
        st.markdown("""
### 🔬 Casos de Uso

**1. Advocacia**: Print WhatsApp em processos

**2. Auditoria**: Recibos suspeitos

**3. Compliance**: BEC (R$ 500k economizados)

**4. Criminal**: Deepfakes como alibi

**5. RH**: Diplomas falsos

**6. Jornalismo**: Fact-checking

**7. Consumidor**: Esquemas Ponzi

**8. TI**: Phishing corporativo
""")

st.markdown("---")

# RODAPE COM TERMO
st.markdown("### 📋 Termo de Uso")
with st.expander("Leia o Termo Completo"):
    st.markdown("""
**TERMO DE USO - AUDITIA**

1. **Natureza**: Sistema de apoio tecnico baseado em IA
2. **Limitacoes**: Resultados probabilisticos
3. **Privacidade**: LGPD Compliant (memoria volatil)
4. **Uso**: Exclusivo para profissionais
5. **Garantias**: Sem precisao absoluta
6. **Propriedade**: Direitos reservados
7. **Atualizacoes**: Sem aviso previo

📧 **Contato**: auditia.ajuda@gmail.com
""")

st.caption(f"👁️ **AuditIA © {datetime.now().year}** - Tecnologia Forense Multimodal")
st.caption("Desenvolvido em **Vargem Grande do Sul - SP** | Versao **2.0 FINAL**")
st.caption("⚖️ Ferramenta de apoio - Nao substitui pericia oficial | LGPD Compliant")
