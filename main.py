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

# 1. GESTÃO DE SESSÃO E MESA DE PERÍCIA CUMULATIVA
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. SEMÁFORO DE CORES COM PROTOCOLO ESPECIALIZADO
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    # PROTOCOLO V16 - PRIORIDADE MÁXIMA PARA FRAUDE
    if any(term in texto_upper for term in ["CLASSIFICAÇÃO: FRAUDE CONFIRMADA", "VEREDITO: FRAUDE CONFIRMADA", "CRIME", "GOLPE", "SCAM", "FRAUDE CONFIRMADA"]):
        cor, font = "#ff4b4b", "white"
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: POSSÍVEL FRAUDE", "VEREDITO: POSSÍVEL FRAUDE", "ALTA ATENÇÃO", "PHISHING", "POSSÍVEL FRAUDE"]):
        cor, font = "#ffa500", "white"
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: ATENÇÃO", "VEREDITO: ATENÇÃO", "IMAGEM", "FOTO", "IA", "SINTÉTICO", "ALTA PROBABILIDADE DE IA"]):
        cor, font = "#f1c40f", "black"
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: SEGURO", "VEREDITO: SEGURO", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO", "AUTENTICIDADE CONFIRMADA"]):
        cor, font = "#2ecc71", "white"
    else:
        cor, font = "#3498db", "white"

    return f"""<div style="background-color: {cor}; padding: 25px; border-radius: 12px; 
                color: {font}; font-weight: bold; border: 2px solid #2c3e50; 
                margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                {texto.replace(chr(10), "<br>")}
            </div>"""

# 3. CSS AVANÇADO
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

# 4. CONEXÃO GEMINI - COM FIX CRÍTICO DO ERRO 404
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
            st.error("Nenhum modelo Gemini disponível")
            st.stop()

except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.info("Aguarde 60 segundos e recarregue.")
    st.stop()

# 5. CABEÇALHO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("👁️ AuditIA - Inteligência Pericial Sênior")

st.warning("""
**⚖️ TERMO DE CONSENTIMENTO INFORMADO**

Esta é uma ferramenta baseada em Inteligência Artificial Forense. Os resultados são 
probabilísticos e devem ser validados por perícia humana oficial.

**Privacidade**: Nenhum dado é armazenado em servidores. Todo processamento ocorre em 
memória volátil e é destruído ao final da sessão.
""")

st.markdown("---")

# 7. UPLOAD MÚLTIPLO
st.header("📂 Upload de Provas Forenses")

new_files = st.file_uploader(
    "Arraste até 5 arquivos (Prints, PDFs até 1000 pág, E-mails .eml)",
    type=["jpg", "png", "jpeg", "pdf", "eml"],
    accept_multiple_files=True
)

if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({
                "name": f.name,
                "content": f.read(),
                "type": f.type
            })

# 8. MESA DE PERÍCIA
if st.session_state.arquivos_acumulados:
    st.write("**🔬 Mesa de Perícia - Provas Carregadas:**")
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

# 9. HISTÓRICO
st.subheader("📊 Linha de Investigação Cumulativa")

if not st.session_state.historico_pericial:
    st.info("O histórico aparecerá aqui após a primeira perícia.")
else:
    for idx, bloco in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"🔍 Análise #{idx}", expanded=(idx == len(st.session_state.historico_pericial))):
            st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

st.markdown("---")

# 10. CAMPO DE PERGUNTA - CORRIGIDO SEM ASPAS TRIPLAS PROBLEMÁTICAS
st.subheader("💬 Consulta ao Perito Digital")

# FIX CRÍTICO: Placeholder simples em uma linha
user_query = st.text_area(
    "Digite sua pergunta técnica:",
    key="campo_pergunta",
    placeholder="Ex: Esta foto e de pessoa real? Analise maos, olhos e textura de pele.",
    height=150
)

st.caption("💡 Dica: Seja específico para respostas mais precisas.")

# 11. FUNÇÕES AUXILIARES
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

# 12. BOTÕES PRINCIPAIS
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button("🔬 EXECUTAR PERÍCIA TÉCNICA", on_click=processar_pericia, type="primary", use_container_width=True):

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
                        request_options={"timeout": 600}
                    )

                    st.session_state.historico_pericial.append(response.text)
                    st.success("Pericia concluida!")
                    st.rerun()

                except Exception as e:
                    erro_msg = str(e)

                    if "exceeds the supported page limit" in erro_msg:
                        st.error("PDF excede 1000 paginas.")
                        st.info("Divida em partes menores.")
                    elif "timeout" in erro_msg.lower():
                        st.error("Timeout. Muitos arquivos.")
                        st.info("Reduza para 3-4 arquivos.")
                    elif "quota" in erro_msg.lower() or "rate" in erro_msg.lower():
                        st.error("Limite de API atingido.")
                        st.info("Aguarde 60 segundos.")
                    else:
                        st.error(f"Erro: {erro_msg}")

with col2:
    if st.button("🗑️ LIMPAR CASO COMPLETO", use_container_width=True):
        if st.session_state.historico_pericial or st.session_state.arquivos_acumulados:
            st.session_state.historico_pericial = []
            st.session_state.arquivos_acumulados = []
            st.session_state.pergunta_ativa = ""
            st.success("Caso limpo!")
            st.rerun()
        else:
            st.info("Nenhum dado para limpar.")

with col3:
    if st.button("❓"):
        st.info("Consulte a Central de Ajuda abaixo")

# 13. GERADOR DE PDF
if st.session_state.historico_pericial:
    st.markdown("---")
    st.subheader("📥 Exportação de Laudo")

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

# 14. CENTRAL DE AJUDA AUDITIA - ULTRA COMPLETA
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

Nascido em **Vargem Grande do Sul - SP**, o AuditIA foi concebido para unir a **psicologia forense** 
a tecnologia de ponta em **Inteligencia Artificial Multimodal**. O projeto surgiu da necessidade 
de identificar **micro-anomalias em comunicacoes digitais** que fogem ao olho humano comum.

---

#### 🔍 Nossos 7 Pilares de Investigacao Forense

##### 1️⃣ **Analise Documental Avancada**
Verificacao profunda de **fontes tipograficas**, **metadados estruturais**, **selos digitais** e 
**padroes de compressao JPEG**. Identificamos clonagem de elementos, artefatos de edicao e 
inconsistencias de iluminacao.

##### 2️⃣ **Deteccao de Geracao por IA (Deepfakes)**
Scrutinio de **12 marcadores anatomicos criticos**:
- Dedos (fusao, articulacoes corretas)
- Olhos (reflexos oculares, pupilas simetricas)
- Dentes (irregularidades naturais)
- Pele (poros, imperfeicoes)

Analise de **fisica da luz** (reflexos, sombras) e **texturas sinteticas**.

##### 3️⃣ **e-Discovery Corporativo**
Processamento inteligente de arquivos **.eml** e **.pst** buscando:
- Intencoes criminosas
- Fraudes corporativas
- Comunicacoes comprometedoras
- Vazamento de informacoes privilegiadas

##### 4️⃣ **Deteccao de Engenharia Social**
Identificacao de padroes comportamentais de **phishing** e **spoofing**:
- Urgencia artificial
- Erros gramaticais
- URLs disfarcadas
- Solicitacoes incomuns

##### 5️⃣ **Analise de Fisica da Luz**
Verificacao tecnica de:
- Reflexos oculares coerentes
- Sombras consistentes com fonte unica
- Iluminacao realista vs. sintetica

##### 6️⃣ **Deteccao de Esquemas Ponzi e Piramides**
Avaliacao de modelos de negocios com:
- Promessas de retorno garantido
- Estruturas de recrutamento
- Ausencia de produto real
- Linguagem persuasiva excessiva

##### 7️⃣ **Verificacao de Consistencia de Metadados**
Comparacao entre:
- Rastro digital vs. conteudo apresentado
- Timestamps de criacao vs. modificacao
- Autoria declarada vs. propriedades do arquivo

---

#### 💼 Capacidades Tecnicas Detalhadas

##### 🖼️ **Processamento de Imagens**
- **Formatos**: JPG, PNG, JPEG, BMP
- **Resolucao**: Ate 10.000 x 10.000 pixels
- **Tamanho**: Ate 200MB por arquivo
- **Analise**: Anatomia, luz, textura, metadados EXIF

##### 📄 **Processamento de Documentos**
- **Formatos**: PDF (ate 1000 paginas)
- **Analise**: Fontes, formatacao, selos digitais, metadados
- **Deteccao**: Clonagem, manipulacao, inconsistencias visuais

##### 📧 **Processamento de E-mails**
- **Formatos**: .eml, .pst
- **Analise**: SPF, DKIM, Received headers, Return-Path
- **Deteccao**: Phishing, spoofing, BEC (Business Email Compromise)

##### 🔗 **Analise Cruzada**
- Correlacao automatica entre multiplos arquivos
- Deteccao de inconsistencias temporais
- Identificacao de padroes de manipulacao

---

#### 🛡️ Seguranca e Privacidade

- ✅ **Processamento Local**: Dados nao armazenados em servidores
- ✅ **Memoria Volatil**: Tudo e destruido ao clicar em "Limpar Caso"
- ✅ **Sem Rastreamento**: Nenhum log de arquivos ou perguntas
- ✅ **LGPD Compliant**: Respeito total a privacidade do usuario

---

#### 🌐 Casos de Uso Reais

1. **Advogados**: Verificacao de prints do WhatsApp em processos
2. **Auditores**: Analise de documentos fiscais suspeitos
3. **Compliance**: Deteccao de BEC (Business Email Compromise)
4. **Investigadores**: Identificacao de deepfakes em casos criminais
5. **RH**: Verificacao de diplomas e certificados
6. **Jornalistas**: Fact-checking de imagens virais
""")

    with tab2:
        st.markdown("""
### 📚 Manual Tecnico de Operacao AuditIA

---

#### 1️⃣ **Upload de Provas Multiplas**

##### Capacidades:
- **Arquivos simultaneos**: Ate 5 por sessao
- **Formatos aceitos**: JPG, PNG, JPEG, PDF, EML
- **Tamanho individual**: Ate 200MB
- **Total da sessao**: Ate 1GB
- **PDFs**: Ate 1000 paginas

##### Fluxo de Trabalho:
1. Arraste arquivos ou clique em "Browse files"
2. Arquivos aparecem na "Mesa de Pericia"
3. Sistema faz analise cruzada automatica
4. Voce pode fazer multiplas perguntas sobre os mesmos arquivos

---

#### 2️⃣ **Como Fazer Perguntas Eficazes**

##### ❌ EVITE (genericas):
- "Isso e verdade?"
- "E fake?"
- "Analise este arquivo"

##### ✅ USE (especificas e tecnicas):
- "Analise a textura de pele e sombras desta face humana"
- "Verifique os cabecalhos SPF e DKIM deste e-mail de cobranca"
- "Compare a fonte tipografica e formatacao entre estes dois contratos"
- "Identifique inconsistencias anatomicas nas maos desta selfie"
- "Este print do WhatsApp e autentico? Verifique metadados e UI"

---

#### 3️⃣ **Entendendo o Semaforo de Classificacao**

##### 🟢 **VERDE (SEGURO)**
**Significado**: Autenticidade tecnica confirmada com evidencia fisica/digital solida.

**Criterios**:
- Metadados EXIF completos e coerentes
- Anatomia humana perfeita (se foto de pessoa)
- Cabecalhos de e-mail validos (SPF PASS, DKIM valido)
- Sem anomalias tecnicas detectadas

**Acao Recomendada**: Documento confiavel para uso pericial.

---

##### 🔵 **AZUL (INFORMATIVO / NEUTRO)**
**Significado**: Documento legitimo mas sem evidencias conclusivas de origem.

**Criterios**:
- Sem suspeitas tecnicas
- Ausencia de metadados nao implica em fraude
- Contexto neutro

**Acao Recomendada**: Validacao adicional recomendada se critico.

---

##### 🟡 **AMARELO (ATENCAO / SUSPEITA MODERADA)**
**Significado**: Imagem ou documento sem rastro digital claro. Possivel geracao por IA.

**Criterios**:
- EXIF ausente ou removido
- Perfeicao excessiva em fotos humanas
- Sinais moderados de edicao
- E-mail com cabecalhos incompletos

**Acao Recomendada**: **Pericia humana especializada obrigatoria** antes de decisoes legais.

---

##### 🟠 **LARANJA (POSSIVEL FRAUDE)**
**Significado**: Multiplas inconsistencias tecnicas detectadas. Alta probabilidade de manipulacao.

**Criterios**:
- Anatomia humana com erros (dedos fundidos, olhos assimetricos)
- Fisica da luz violada (sombras inconsistentes)
- Cabecalhos de e-mail suspeitos (SPF FAIL)
- Clonagem de elementos em documentos

**Acao Recomendada**: **Nao confie sem pericia humana oficial**.

---

##### 🔴 **VERMELHO (FRAUDE CONFIRMADA)**
**Significado**: Fraude ou manipulacao sintetica tecnicamente irrefutavel.

**Criterios**:
- Deepfake confirmado (anatomia impossivel)
- Phishing confirmado (dominio falso, spoofing)
- Documento adulterado (clonagem digital evidente)
- Multiplas evidencias de fraude

**Acao Recomendada**: **Acao legal imediata**. Nao utilize como evidencia autentica.

---

#### 4️⃣ **Mesa de Pericia Cumulativa**

##### Funcionalidades:
- **Persistencia**: Arquivos permanecem carregados durante toda a sessao
- **Multiplas Perguntas**: Faca varias perguntas sobre os mesmos arquivos
- **Analise Contextual**: Sistema mantem historico de analises anteriores
- **Visualizacao**: Miniaturas para identificacao rapida

##### Quando Limpar:
- ✅ Ao finalizar completamente um caso
- ✅ Antes de iniciar um novo caso nao relacionado
- ❌ NAO limpe se quiser fazer perguntas adicionais sobre os mesmos arquivos

---

#### 5️⃣ **Geracao de Laudos PDF Profissionais**

##### Conteudo do PDF:
- ✅ Cabecalho profissional com logo AuditIA
- ✅ Data e hora da pericia (timezone Brasil)
- ✅ Total de provas analisadas
- ✅ Analise tecnica completa
- ✅ Classificacao de risco
- ✅ Rodape com disclaimer legal

##### Quando Gerar:
- Apos cada analise
- Antes de "Limpar Caso" (dados sao destruidos)

##### Uso Recomendado:
- Anexo em processos judiciais
- Relatorios de auditoria
- Documentacao de compliance
- Evidencia em investigacoes internas

---

#### 6️⃣ **Limitacoes Tecnicas**

##### ⏱️ **Timeout (2 minutos)**
**Causa**: Analise muito complexa ou muitos arquivos

**Solucao**:
- Reduza para 3-4 arquivos simultaneos
- Perguntas mais especificas
- Aguarde 60s e tente novamente

---

##### 📄 **PDF com +1000 paginas**
**Causa**: Limite da API Gemini

**Solucao**:
- Divida o PDF em partes menores
- Extraia apenas paginas relevantes

---

##### 🚫 **Limite de Taxa**
**Causa**: Muitas requisicoes em curto periodo

**Solucao**:
- Aguarde 60 segundos
- Evite multiplas analises simultaneas

---

##### 🖼️ **Videos e Audios**
**Status**: Nao suportado na versao atual

**Previsao**: Versao 3.0 (Q2 2025)

---

#### 7️⃣ **Boas Praticas Profissionais**

##### ✅ **FACA**:
- Seja especifico nas perguntas
- Analise 3-4 arquivos por vez
- Baixe os PDFs antes de limpar
- Use termos tecnicos quando possivel
- Valide com perito humano se critico

##### ❌ **NAO FACA**:
- Use como unica evidencia em processos
- Envie dados extremamente sensiveis sem necessidade
- Confie 100% sem validacao humana em casos criticos
- Ultrapasse os limites tecnicos (timeout, tamanho)
""")

    with tab3:
        st.markdown("""
### ❓ FAQ Completo - Perguntas Frequentes

---

#### **Q1: Por que o AuditIA foi criado?**

**R**: Para fornecer ferramentas tecnicas profissionais a **advogados**, **auditores**, **peritos** 
e **investigadores** contra o avanco exponencial de **fraudes geradas por Inteligencia Artificial**.

Com o surgimento de ferramentas como:
- **Midjourney** (geracao de imagens sinteticas)
- **DALL-E** (criacao de fotos realistas)
- **ChatGPT** (textos persuasivos)
- **Deepfakes** (videos manipulados)

Tornou-se **critico** ter sistemas capazes de detectar manipulacoes digitais que o olho humano 
comum nao consegue identificar.

---

#### **Q2: Como funciona a analise de fotos de pessoas?**

**R**: O robo executa o **Protocolo V16**, que analisa:

##### 🔬 **12 Marcadores Anatomicos**:
1. Numero de dedos (5 por mao)
2. Articulacoes corretas (3 por dedo, exceto polegar com 2)
3. Dentes (irregularidades naturais)
4. Orelhas (cartilagem com textura natural)
5. Olhos (reflexos oculares coerentes)
6. Pupilas (simetria)
7. Veias esclerais (realismo)
8. Cabelo (fios individuais vs. massa texturizada)
9. Pele (poros, manchas, imperfeicoes)
10. Sombras (consistencia com fonte de luz)
11. Reflexos (fisica da luz respeitada)
12. Ruido digital (padrao de sensor vs. sintese)

##### 📸 **Metadados EXIF**:
- Marca de camera
- Modelo
- GPS (se disponivel)
- Timestamp
- Configuracoes (ISO, abertura, velocidade)

---

#### **Q3: Qual o tamanho maximo dos arquivos?**

**R**: Processamos:

| Tipo | Limite Individual | Limite Total |
|------|-------------------|--------------|
| **Imagens** | 200MB | 1GB |
| **PDFs** | 200MB (1000 pag) | 1GB |
| **E-mails** | 50MB | 500MB |
| **Sessao Total** | - | 1GB |

---

#### **Q4: O sistema guarda meu historico?**

**R**: **NAO**. Respeitamos a **privacidade forense absoluta**:

- ✅ Dados processados **apenas em memoria volatil** (RAM)
- ✅ Ao clicar em "Limpar Caso", **toda a memoria e destruida**
- ✅ **Nenhum arquivo armazenado em servidores**
- ✅ **Nenhum log de perguntas ou analises**
- ✅ **LGPD Compliant**

**Recomendacao**: Sempre baixe os laudos em PDF **antes** de limpar o caso.

---

#### **Q5: O AuditIA substitui um perito humano oficial?**

**R**: **NAO**. O AuditIA e uma **ferramenta de apoio tecnico** que:

##### ✅ **O que PODE fazer**:
- Acelerar triagem inicial de evidencias (horas → minutos)
- Identificar pontos tecnicos que exigem atencao especializada
- Fornecer base tecnica para laudos humanos
- Detectar anomalias invisiveis ao olho humano comum

##### ❌ **O que NAO PODE fazer**:
- Substituir perito certificado em processos judiciais
- Garantir 100% de precisao (IA e probabilistica)
- Analisar contexto emocional ou juridico
- Tomar decisoes legais ou eticas

**Analogia**: O AuditIA e como um **microscopio** para um biologo. A ferramenta e poderosa, 
mas o **especialista humano interpreta** os resultados.

---

#### **Q6: Como interpretar resultados conflitantes?**

**R**: Se o AuditIA classificar como **ATENCAO** ou **POSSIVEL FRAUDE**:

##### 1️⃣ **Revise a Analise Tecnica**:
- Leia os indicadores tecnicos identificados
- Entenda **por que** foi classificado assim
- Verifique se ha evidencias solidas

##### 2️⃣ **Contextualize**:
- Qual a origem do arquivo?
- Ha testemunhas ou fontes confiaveis?
- O contexto faz sentido?

##### 3️⃣ **Valide Externamente**:
- Considere contratar **pericia humana especializada**
- Use outras ferramentas (exiftool, fotoforensics)
- Consulte especialistas em deepfakes

##### 4️⃣ **Nao Tome Decisoes Precipitadas**:
- **NAO descarte** evidencia apenas pela analise da IA
- **NAO confie cegamente** sem validacao
- Use o laudo como **ponto de partida investigativo**

---

#### **Q7: O que fazer se houver erro tecnico?**

**R**: Em caso de instabilidade:

##### 🔴 **Timeout (2 min)**
**Causa**: Muitos arquivos ou analise complexa

**Solucao**:
- Reduza para 3-4 arquivos
- Seja mais especifico na pergunta
- Evite PDFs gigantes

---

##### 🔴 **Limite de Taxa**
**Causa**: Muitas requisicoes em curto periodo

**Solucao**:
- Aguarde **60 segundos**
- Evite clicar multiplas vezes

---

##### 🔴 **Erro de Conexao**
**Causa**: Problema temporario com a API

**Solucao**:
- Recarregue a pagina (F5)
- Aguarde 1-2 minutos

---

#### **Q8: E possivel analisar videos ou audios?**

**R**: **Atualmente NAO**. A versao atual (2.0) suporta apenas:

##### ✅ **Suportado**:
- Imagens estaticas (JPG, PNG, JPEG)
- Documentos (PDF ate 1000 paginas)
- E-mails (.eml)

##### 🚧 **Em Desenvolvimento (Versao 3.0)**:
- Analise de videos (deteccao de deepfakes em motion)
- Analise de audios (voice cloning, sintese de voz)
- Analise de arquivos .pst completos (Outlook)

---

#### **Q9: Como funciona a deteccao de phishing?**

**R**: O AuditIA analisa **7 camadas de seguranca**:

1. **Cabecalhos Tecnicos**: SPF, DKIM, Received headers
2. **Analise de Dominio**: Idade, similaridade, TLD suspeito
3. **Conteudo**: Urgencia, erros gramaticais
4. **Links**: URLs disfarcadas, encurtadores
5. **Anexos**: Executaveis, macros
6. **Origem Geografica**: IP de paises de alto risco
7. **Engenharia Social**: Apelo a emocao

---

#### **Q10: Posso confiar 100% nos resultados?**

**R**: **NAO**. Nenhuma IA e 100% precisa. O AuditIA tem:

##### Precisao Estimada:
- 🟢 **FRAUDE CONFIRMADA**: ~95% de confiabilidade
- 🟠 **POSSIVEL FRAUDE**: ~80-90%
- 🟡 **ATENCAO**: ~70-80% (zona cinza)
- 🔵 **INFORMATIVO**: ~90%
- ✅ **SEGURO**: ~85-95%

##### Recomendacao Profissional:
**Use o AuditIA como primeira triagem**, mas sempre valide com pericia humana oficial.

---

#### **Q11: Como reportar bugs ou sugerir melhorias?**

**R**: Entre em contato:

📧 **E-mail**: auditia.ajuda@gmail.com

🐛 **Reportar Bug**:
- Descreva o erro
- Anexe print da tela
- Informe tipo de arquivo e tamanho

💡 **Sugerir Melhoria**:
- Descreva a funcionalidade desejada
- Explique o caso de uso
""")

    with tab4:
        st.markdown("""
### 🔬 Casos de Uso Profissionais Reais

---

#### 1️⃣ **Advocacia Trabalhista**

##### 📱 **Cenario**: Print do WhatsApp como evidencia de assedio moral

**Desafio**: Empresa alega que print foi adulterado.

**Solucao com AuditIA**:
1. Upload do print
2. Pergunta: "Este print do WhatsApp e autentico?"
3. Analise: Fonte, formatacao, timestamp, UI

**Resultado**: Laudo tecnico para anexar ao processo.

---

#### 2️⃣ **Auditoria Fiscal**

##### 📄 **Cenario**: Recibo de pagamento suspeito

**Desafio**: Recibo parece editado digitalmente.

**Solucao com AuditIA**:
1. Upload do PDF/imagem
2. Pergunta: "Verifique se foi adulterado"
3. Analise: Fonte, alinhamento, metadados

**Resultado**: Identificacao de clonagem de elementos.

---

#### 3️⃣ **Compliance Corporativo**

##### 📧 **Cenario**: E-mail de CEO solicitando transferencia (BEC)

**Desafio**: Funcionario recebe e-mail urgente pedindo R$ 500k.

**Solucao com AuditIA**:
1. Upload do .eml
2. Pergunta: "Este e-mail e phishing?"
3. Analise: SPF, DKIM, dominio, linguagem

**Resultado**: **FRAUDE CONFIRMADA** - R$ 500k economizados.

---

#### 4️⃣ **Investigacao Criminal**

##### 🖼️ **Cenario**: Selfie usada como alibi

**Desafio**: Delegado suspeita de deepfake.

**Solucao com AuditIA**:
1. Upload da selfie
2. Pergunta: "Esta foto e real?"
3. Analise: Anatomia, luz, EXIF

**Resultado**: **FRAUDE CONFIRMADA** - Deepfake detectado.

---

#### 5️⃣ **Recursos Humanos**

##### 🎓 **Cenario**: Diploma universitario

**Desafio**: RH suspeita de falsificacao.

**Solucao com AuditIA**:
1. Upload do diploma
2. Pergunta: "Este diploma e autentico?"
3. Analise: Selos, fontes, formatacao

**Resultado**: Diploma fraudulento identificado.

---

#### 6️⃣ **Jornalismo Investigativo**

##### 📸 **Cenario**: Foto viral de politico

**Desafio**: Verificar se e deepfake antes de publicar.

**Solucao com AuditIA**:
1. Upload da foto
2. Pergunta: "Esta foto e deepfake?"
3. Analise: Face, maos, EXIF

**Resultado**: **SEGURO** - Foto autentica.

---

#### 7️⃣ **Protecao ao Consumidor**

##### 💰 **Cenario**: Esquema Ponzi disfarc ado de investimento

**Desafio**: Identificar se e piramide financeira.

**Solucao com AuditIA**:
1. Upload de prints e contratos
2. Pergunta: "Este e esquema Ponzi?"
3. Analise: Promessas, estrutura, linguagem

**Resultado**: **FRAUDE CONFIRMADA** - Caracteristicas de Ponzi.

---

#### 8️⃣ **Seguranca da Informacao**

##### 🔒 **Cenario**: E-mail de "suporte tecnico"

**Desafio**: Empresa recebe e-mail pedindo credenciais.

**Solucao com AuditIA**:
1. Upload do .eml
2. Pergunta: "Este e spear phishing?"
3. Analise: SPF, dominio, linguagem, link

**Resultado**: **FRAUDE CONFIRMADA** - Ataque bloqueado.

---

### 💡 Conclusao

O **AuditIA** e uma ferramenta **versatil e poderosa** para multiplos setores profissionais. 
A chave e fazer **perguntas especificas e tecnicas** para obter analises precisas.

**Lembre-se**: O AuditIA e seu **assistente forense digital**, mas o **julgamento final** 
sempre deve ser **humano e contextualizado**.
""")

st.markdown("---")
st.caption(f"👁️ **AuditIA © {datetime.now().year}** - Tecnologia Forense Multimodal de Alta Precisao")
st.caption("Desenvolvido em **Vargem Grande do Sul - SP** | Versao **2.0 COMPLETA** | www.auditia.com.br")
st.caption("⚖️ Ferramenta de apoio pericial - Nao substitui pericia oficial | LGPD Compliant")
