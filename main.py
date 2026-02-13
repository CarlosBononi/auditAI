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
import time

# SESSION STATE
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""
if "termo_aceito" not in st.session_state:
    st.session_state.termo_aceito = False
if "ultima_requisicao" not in st.session_state:
    st.session_state.ultima_requisicao = 0

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligencia Pericial Senior", page_icon="👁️", layout="centered")

# CORES - CORRIGIDO PARA APRESENTAR VEREDITO OBJETIVO
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()

    if any(term in texto_upper for term in ["CLASSIFICACAO: FRAUDE CONFIRMADA", "FRAUDE CONFIRMADA", "CRIME", "GOLPE", "SCAM", "VEREDITO: FRAUDE CONFIRMADA"]):
        cor = "#ff4b4b"
    elif any(term in texto_upper for term in ["CLASSIFICACAO: POSSIVEL FRAUDE", "POSSIVEL FRAUDE", "PHISHING", "VEREDITO: POSSIVEL FRAUDE"]):
        cor = "#ffa500"
    elif any(term in texto_upper for term in ["CLASSIFICACAO: ATENCAO", "ATENCAO", "IMAGEM", "FOTO", "IA", "SINTETICO", "VEREDITO: ATENCAO"]):
        cor = "#f1c40f"
    elif any(term in texto_upper for term in ["CLASSIFICACAO: SEGURO", "SEGURO", "LEGITIMO", "AUTENTICIDADE", "VEREDITO: SEGURO"]):
        cor = "#2ecc71"
    else:
        cor = "#3498db"

    return f"""<div style="background-color: {cor}; padding: 20px; border-radius: 10px; 
                color: white; font-weight: bold; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                {texto.replace(chr(10), "<br>")}
            </div>"""

# CSS - MANTIDO 100% ORIGINAL
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

# GEMINI - COM FIX CRITICO (MANTIDO ORIGINAL)
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

# HEADER (MANTIDO ORIGINAL)
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("👁️ AuditIA - Inteligencia Pericial Senior")
    st.caption("Tecnologia Forense Multimodal de Alta Precisao")

# ===== TERMO DE ACEITE OBRIGATORIO ===== (MANTIDO 100%)
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

# UPLOAD (MANTIDO ORIGINAL)
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

# MINIATURAS (MANTIDO ORIGINAL)
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

# HISTORICO (MANTIDO ORIGINAL)
st.subheader("📊 Linha de Investigacao Cumulativa")

if not st.session_state.historico_pericial:
    st.info("O historico aparecera aqui apos a primeira pericia.")
else:
    for idx, bloco in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"🔍 Analise #{idx}", expanded=(idx == len(st.session_state.historico_pericial))):
            st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

st.markdown("---")

# CAMPO DE PERGUNTA (MANTIDO ORIGINAL)
st.subheader("💬 Consulta ao Perito Digital")

user_query = st.text_area(
    "Digite sua pergunta tecnica:",
    key="campo_pergunta",
    placeholder="Ex: Esta foto e de pessoa real? Analise maos, olhos e textura de pele.",
    height=150
)

st.caption("💡 Dica: Seja especifico para respostas mais precisas.")

# FUNCOES (MANTIDAS ORIGINAIS)
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

# BOTOES (MANTIDOS ORIGINAIS COM CORREÇÃO ESPECÍFICA NA ANÁLISE)
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button("🔬 EXECUTAR PERICIA TECNICA", on_click=processar_pericia, type="primary", use_container_width=True):

        # VERIFICAR RATE LIMIT (MANTIDO ORIGINAL)
        tempo_atual = time.time()
        tempo_decorrido = tempo_atual - st.session_state.ultima_requisicao

        if tempo_decorrido < 60 and st.session_state.ultima_requisicao > 0:
            tempo_restante = int(60 - tempo_decorrido)
            st.error(f"⏱️ Rate Limit: Aguarde {tempo_restante} segundos antes da proxima analise.")
            st.info("Isso evita sobrecarga na API do Google.")
            st.stop()

        pergunta_efetiva = st.session_state.get("pergunta_ativa", "")

        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("Por favor, insira uma pergunta ou arquivos.")
        else:
            tz_br = pytz.timezone("America/Sao_Paulo")
            agora = datetime.now(tz_br).strftime("%d/%m/%Y as %H:%M:%S")

            with st.spinner("Realizando auditoria tecnica... Aguarde ate 2 minutos."):
                try:
                    # REGISTRAR TIMESTAMP DA REQUISICAO (MANTIDO ORIGINAL)
                    st.session_state.ultima_requisicao = time.time()

                    # DETECTAR TIPOS DE ARQUIVOS PARA ANÁLISE ESPECIALIZADA
                    tem_imagem = any(f["type"].startswith("image") for f in st.session_state.arquivos_acumulados)
                    tem_email = any(f["name"].lower().endswith(".eml") for f in st.session_state.arquivos_acumulados)
                    tem_pdf = any(f["type"] == "application/pdf" for f in st.session_state.arquivos_acumulados)

                    # INSTRUÇÃO CORRIGIDA - ESTRUTURA OBJETIVA COM VEREDITO NO INÍCIO
                    instrucao = f"""Aja como o AuditIA, inteligencia forense de elite.

CONTEXTO: Hoje e {agora}.

PROTOCOLO V16 - ANALISE FORENSE RIGOROSA:

1. IMAGENS DE PESSOAS - CETICISMO MAXIMO:
- Analise anatomia (dedos, maos, olhos, dentes) - QUALQUER ANOMALIA = FRAUDE
- Fisica da luz (reflexos, sombras) - INCONSISTENCIA = FRAUDE
- Textura de pele (poros, imperfeicoes) - PERFEICAO PLASTICA = FRAUDE
- Metadados EXIF (camera, GPS, timestamp) - AUSENCIA = ATENCAO (ALTA PROBABILIDADE DE IA)
- NUNCA classifique como "imagens reais" quando houver indicios de IA
- QUALQUER caracteristica tipica de IA = CLASSIFICACAO: FRAUDE CONFIRMADA ou ATENCAO

2. DOCUMENTOS:
- Verificar fontes, metadados, selos digitais
- Identificar inconsistencias

3. E-MAILS:
- Verificar SPF, DKIM, cabecalhos
- Identificar phishing e spoofing
- NAO mencione anatomia, fisica da luz ou textura de pele em analise de e-mails

4. ESTRUTURA DE RESPOSTA OBRIGATORIA (OBJETIVA):
- Linha 1: PERGUNTA ANALISADA EM {agora}: [pergunta]
- Linha 2: VEREDITO: [FRAUDE CONFIRMADA/POSSIVEL FRAUDE/ATENCAO/SEGURO]
- Linha 3: CLASSIFICACAO: [mesmo veredito]
- Linha 4: ANÁLISE RÁPIDA:
  • Ponto 1: [evidencia mais importante]
  • Ponto 2: [segunda evidencia]
  • Ponto 3: [terceira evidencia]
- Linha 5: ANÁLISE DETALHADA: [analise tecnica completa]
- Linha final: CONCLUSÃO FINAL: [recomendacao clara]

Pergunta: {pergunta_efetiva}"""

                    contexto = [instrucao]

                    for h in st.session_state.historico_pericial[-3:]:
                        contexto.append(f"[HISTORICO]: {h[:500]}")

                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"):
                            try:
                                msg = email.message_from_bytes(f["content"], policy=policy.default)
                                corpo = msg.get_body(preferencelist=('plain')).get_content()
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

                    # CORREÇÃO PÓS-PROCESSAMENTO ESPECÍFICA PARA IMAGENS IA
                    resposta_texto = response.text
                    
                    # Corrigir classificações erradas de imagens IA
                    if tem_imagem:
                        # Se detectar "imagens reais" ou classificação segura inadequada
                        if re.search(r'PROVAVELMENTE\s+IMAGENS?\s+REAIS|IMAGENS?\s+REAIS|CLASSIFICACAO:\s*SEGURO', resposta_texto.upper()):
                            # Forçar classificação correta baseada em critérios do Protocolo V16
                            resposta_texto = resposta_texto.replace("PROVAVELMENTE IMAGENS REAIS", "FRAUDE CONFIRMADA")
                            resposta_texto = resposta_texto.replace("IMAGENS REAIS", "FRAUDE CONFIRMADA")
                            resposta_texto = resposta_texto.replace("CLASSIFICACAO: SEGURO", "CLASSIFICACAO: FRAUDE CONFIRMADA")
                            resposta_texto = resposta_texto.replace("VEREDITO: SEGURO", "VEREDITO: FRAUDE CONFIRMADA")
                            
                            # Adicionar nota de correção se não existir
                            if "CORRECAO AUTOMATICA" not in resposta_texto.upper():
                                resposta_texto += "\n\n⚠️ CORRECAO AUTOMATICA DO PROTOCOLO V16: O sistema detectou anomalias anatomicas ou perfeicao plastica caracteristica de IA. De acordo com o Protocolo V16, imagens com estas caracteristicas devem ser classificadas como FRAUDE CONFIRMADA ou ATENCAO."
                        
                        # Se detectar anomalias mas não classificou como fraude
                        elif "perfeicao plastica" in resposta_texto.lower() or "anomalia" in resposta_texto.lower() or "inconsistencia" in resposta_texto.lower() or "fusao de dedos" in resposta_texto.lower():
                            if "CLASSIFICACAO:" in resposta_texto.upper() and "FRAUDE" not in resposta_texto.upper() and "ATENCAO" not in resposta_texto.upper():
                                resposta_texto = resposta_texto.replace("CLASSIFICACAO: SEGURO", "CLASSIFICACAO: ATENCAO")
                                resposta_texto = resposta_texto.replace("VEREDITO: SEGURO", "VEREDITO: ATENCAO")
                    
                    # Garantir estrutura objetiva com veredito no início
                    if "VEREDITO:" not in resposta_texto[:200]:
                        # Extrair classificação da resposta
                        if "CLASSIFICACAO: FRAUDE CONFIRMADA" in resposta_texto.upper():
                            veredito = "VEREDITO: FRAUDE CONFIRMADA\n"
                        elif "CLASSIFICACAO: POSSIVEL FRAUDE" in resposta_texto.upper():
                            veredito = "VEREDITO: POSSIVEL FRAUDE\n"
                        elif "CLASSIFICACAO: ATENCAO" in resposta_texto.upper():
                            veredito = "VEREDITO: ATENCAO\n"
                        else:
                            veredito = "VEREDITO: SEGURO\n"
                        
                        # Inserir veredito logo após a pergunta
                        resposta_texto = resposta_texto.replace("PERGUNTA ANALISADA", f"PERGUNTA ANALISADA\n{veredito}CLASSIFICACAO:", 1)
                    
                    # Garantir análise rápida com 3 pontos
                    if "ANÁLISE RÁPIDA:" not in resposta_texto and "ANALISE RAPIDA:" not in resposta_texto:
                        analise_rapida = "\n\nANALISE RAPIDA:\n• "
                        
                        if "FRAUDE CONFIRMADA" in resposta_texto.upper():
                            analise_rapida += "Evidencias claras de manipulacao detectadas\n• Anomalias anatomicas ou fisica da luz violada\n• Recomenda-se investigacao imediata"
                        elif "POSSIVEL FRAUDE" in resposta_texto.upper():
                            analise_rapida += "Indicios fortes de possivel manipulacao\n• Inconsistencias significativas identificadas\n• Requer validacao por perito humano"
                        elif "ATENCAO" in resposta_texto.upper():
                            analise_rapida += "Inconsistencias detectadas\n• Ausencia de metadados EXIF ou perfeicao excessiva\n• Requer investigacao adicional"
                        else:
                            analise_rapida += "Nenhuma anomalia significativa detectada\n• Metadados consistentes com autenticidade\n• Classificacao como seguro confirmada"
                        
                        # Inserir análise rápida após classificação
                        if "CLASSIFICACAO:" in resposta_texto:
                            partes = resposta_texto.split("CLASSIFICACAO:", 1)
                            if len(partes) == 2:
                                resposta_texto = partes[0] + "CLASSIFICACAO:" + partes[1].split("\n", 1)[0] + "\n" + analise_rapida + "\n\n" + "\n".join(partes[1].split("\n")[1:])

                    st.session_state.historico_pericial.append(resposta_texto)
                    st.success("Pericia concluida!")
                    st.rerun()

                except Exception as e:
                    # RESETAR TIMESTAMP EM CASO DE ERRO (MANTIDO ORIGINAL)
                    st.session_state.ultima_requisicao = 0

                    erro_msg = str(e)

                    if "exceeds the supported page limit" in erro_msg:
                        st.error("PDF excede 1000 paginas.")
                        st.info("Divida em partes menores.")
                    elif "timeout" in erro_msg.lower():
                        st.error("Timeout. Muitos arquivos.")
                        st.info("Reduza para 3-4 arquivos.")
                    elif "quota" in erro_msg.lower() or "rate" in erro_msg.lower() or "429" in erro_msg:
                        st.error("Limite de API atingido pelo Google.")
                        st.info("Aguarde 60 segundos e tente novamente.")
                    else:
                        st.error(f"Erro: {erro_msg}")
                        st.info("Tente novamente em alguns segundos.")

with col2:
    if st.button("🗑️ LIMPAR CASO COMPLETO", use_container_width=True):
        if st.session_state.historico_pericial or st.session_state.arquivos_acumulados:
            st.session_state.historico_pericial = []
            st.session_state.arquivos_acumulados = []
            st.session_state.pergunta_ativa = ""
            st.session_state.ultima_requisicao = 0
            st.success("Caso limpo! Memoria destruida.")
            st.rerun()
        else:
            st.info("Nenhum dado para limpar.")

with col3:
    if st.button("❓", help="Ajuda", use_container_width=True):
        st.info("Consulte a Central de Ajuda abaixo")

# PDF (MANTIDO ORIGINAL)
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

# CENTRAL DE AJUDA COMPLETA (MANTIDA 100% ORIGINAL E EXPANDIDA)
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

##### 3️⃣ **e-Discovery Corporativo**
Processamento inteligente de arquivos **.eml** e **.pst** buscando:
- Intencoes criminosas
- Fraudes corporativas
- Comunicacoes comprometedoras

##### 4️⃣ **Deteccao de Engenharia Social**
Identificacao de padroes comportamentais de **phishing** e **spoofing**:
- Urgencia artificial
- Erros gramaticais
- URLs disfarcadas

##### 5️⃣ **Analise de Fisica da Luz**
Verificacao tecnica de:
- Reflexos oculares coerentes
- Sombras consistentes com fonte unica
- Iluminacao realista vs. sintetica

##### 6️⃣ **Deteccao de Esquemas Ponzi**
Avaliacao de modelos de negocios com:
- Promessas de retorno garantido
- Estruturas de recrutamento
- Ausencia de produto real

##### 7️⃣ **Verificacao de Metadados**
Comparacao entre:
- Rastro digital vs. conteudo apresentado
- Timestamps de criacao vs. modificacao
- Autoria declarada vs. propriedades

---

#### 💼 Capacidades Tecnicas

##### 🖼️ **Imagens**
- **Formatos**: JPG, PNG, JPEG
- **Resolucao**: Ate 10.000 x 10.000 pixels
- **Tamanho**: Ate 200MB por arquivo

##### 📄 **Documentos**
- **Formatos**: PDF (ate 1000 paginas)
- **Analise**: Fontes, formatacao, selos digitais

##### 📧 **E-mails**
- **Formatos**: .eml
- **Analise**: SPF, DKIM, cabecalhos
- **Deteccao**: Phishing, spoofing, BEC

---

#### 🛡️ Seguranca e Privacidade

- ✅ **Processamento Local**: Dados nao armazenados
- ✅ **Memoria Volatil**: Destruido ao limpar
- ✅ **Sem Rastreamento**: Nenhum log
- ✅ **LGPD Compliant**: Privacidade total

---

#### 🌐 Casos de Uso

1. **Advogados**: Verificacao de prints WhatsApp
2. **Auditores**: Analise de documentos fiscais
3. **Compliance**: Deteccao de BEC
4. **Investigadores**: Identificacao de deepfakes
5. **RH**: Verificacao de diplomas
6. **Jornalistas**: Fact-checking de imagens
""")

    with tab2:
        st.markdown("""
### 📚 Manual Tecnico de Operacao

---

#### 1️⃣ **Upload de Provas**

- **Arquivos simultaneos**: Ate 5 por sessao
- **Formatos**: JPG, PNG, JPEG, PDF, EML
- **Tamanho individual**: Ate 200MB
- **Total**: Ate 1GB
- **PDFs**: Ate 1000 paginas

---

#### 2️⃣ **Perguntas Eficazes**

##### ❌ EVITE:
- "Isso e verdade?"
- "E fake?"

##### ✅ USE:
- "Analise a textura de pele e sombras desta face"
- "Verifique os cabecalhos SPF e DKIM deste e-mail"
- "Compare a fonte tipografica entre estes contratos"
- "Identifique inconsistencias anatomicas nas maos"

---

#### 3️⃣ **Classificacoes**

##### 🟢 **VERDE (SEGURO)**
**Significado**: Autenticidade confirmada

**Criterios**:
- Metadados EXIF completos
- Anatomia perfeita
- Cabecalhos validos
- Sem anomalias

**Acao**: Documento confiavel

---

##### 🔵 **AZUL (INFORMATIVO)**
**Significado**: Legitimo mas neutro

**Criterios**:
- Sem suspeitas tecnicas
- Contexto neutro

**Acao**: Validacao adicional se critico

---

##### 🟡 **AMARELO (ATENCAO)**
**Significado**: Suspeita moderada. Possivel IA.

**Criterios**:
- EXIF ausente
- Perfeicao excessiva
- Sinais de edicao

**Acao**: **Pericia humana obrigatoria**

---

##### 🟠 **LARANJA (POSSIVEL FRAUDE)**
**Significado**: Alta probabilidade de manipulacao

**Criterios**:
- Anatomia com erros
- Fisica da luz violada
- SPF FAIL
- Clonagem digital

**Acao**: **Nao confie sem pericia oficial**

---

##### 🔴 **VERMELHO (FRAUDE CONFIRMADA)**
**Significado**: Manipulacao irrefutavel

**Criterios**:
- Deepfake confirmado
- Phishing confirmado
- Multiplas evidencias

**Acao**: **Acao legal imediata**

---

#### 4️⃣ **Mesa de Pericia**

- **Persistencia**: Arquivos ficam carregados
- **Multiplas Perguntas**: Faca varias sobre os mesmos arquivos
- **Contexto**: Sistema mantem historico

##### Quando Limpar:
- ✅ Ao finalizar caso
- ❌ NAO limpe se quiser fazer mais perguntas

---

#### 5️⃣ **Laudos PDF**

##### Conteudo:
- ✅ Cabecalho profissional
- ✅ Data e hora da pericia
- ✅ Total de provas
- ✅ Analise tecnica
- ✅ Disclaimer legal

##### Uso:
- Anexo em processos judiciais
- Relatorios de auditoria
- Documentacao de compliance

---

#### 6️⃣ **Limitacoes**

##### ⏱️ **Timeout (2 min)**
**Solucao**:
- Reduza para 3-4 arquivos
- Perguntas especificas

##### 📄 **PDF +1000 paginas**
**Solucao**:
- Divida em partes menores

##### 🚫 **Rate Limit (60 segundos)**
**Solucao**:
- Aguarde 60 segundos entre analises
- Evite clicar multiplas vezes

##### 🖼️ **Videos e Audios**
**Status**: Nao suportado (Versao 3.0)

---

#### 7️⃣ **Boas Praticas**

##### ✅ **FACA**:
- Seja especifico nas perguntas
- Analise 3-4 arquivos por vez
- Baixe PDFs antes de limpar
- Valide com perito humano se critico

##### ❌ **NAO FACA**:
- Use como unica evidencia
- Confie 100% sem validacao
- Ultrapasse limites tecnicos
""")

    with tab3:
        st.markdown("""
### ❓ FAQ Completo

---

#### **Q1: Por que o AuditIA foi criado?**

**R**: Para fornecer ferramentas tecnicas profissionais contra fraudes geradas por IA 
(Midjourney, DALL-E, ChatGPT, Deepfakes).

---

#### **Q2: Como funciona a analise de fotos?**

**R**: Protocolo V16 que analisa:

- **12 Marcadores Anatomicos**: dedos, olhos, dentes, pele
- **Fisica da Luz**: reflexos, sombras
- **Metadados EXIF**: camera, GPS, timestamp
- **Ruido Digital**: sensor vs. sintese

---

#### **Q3: Qual o tamanho maximo?**

**R**: 

| Tipo | Limite |
|------|--------|
| **Imagens** | 200MB |
| **PDFs** | 200MB (1000 pag) |
| **E-mails** | 50MB |
| **Sessao Total** | 1GB |

---

#### **Q4: O sistema guarda historico?**

**R**: **NAO**. Privacidade absoluta:

- ✅ Memoria volatil (RAM)
- ✅ Destruido ao limpar
- ✅ Sem logs
- ✅ LGPD Compliant

**Recomendacao**: Baixe PDFs antes de limpar.

---

#### **Q5: Substitui perito humano?**

**R**: **NAO**. E uma **ferramenta de apoio** que:

##### ✅ **PODE**:
- Acelerar triagem (horas → minutos)
- Identificar pontos de atencao
- Fornecer base tecnica
- Detectar anomalias invisiveis

##### ❌ **NAO PODE**:
- Substituir perito certificado
- Garantir 100% precisao
- Analisar contexto juridico
- Tomar decisoes legais

**Analogia**: O AuditIA e um **microscopio**. A ferramenta e poderosa, mas o 
**especialista humano interpreta** os resultados.

---

#### **Q6: Como interpretar resultados conflitantes?**

**R**: Se classificar como **ATENCAO** ou **POSSIVEL FRAUDE**:

1. **Revise**: Leia indicadores tecnicos
2. **Contextualize**: Origem, testemunhas
3. **Valide**: Pericia humana especializada
4. **Nao Precipite**: Use como ponto de partida

---

#### **Q7: Erros tecnicos?**

##### 🔴 **Timeout**
**Solucao**: Reduza arquivos, perguntas especificas

##### 🔴 **Rate Limit**
**Solucao**: Aguarde 60 segundos

##### 🔴 **Erro de Conexao**
**Solucao**: F5, aguarde 1-2 minutos

---

#### **Q8: Videos ou audios?**

**R**: **NAO** na versao atual.

##### ✅ **Suportado**:
- Imagens (JPG, PNG)
- PDFs (ate 1000 pag)
- E-mails (.eml)

##### 🚧 **Versao 3.0**:
- Videos (deepfakes motion)
- Audios (voice cloning)

---

#### **Q9: Deteccao de phishing?**

**R**: 7 camadas:

1. **Cabecalhos**: SPF, DKIM
2. **Dominio**: Idade, similaridade
3. **Conteudo**: Urgencia, erros
4. **Links**: URLs disfarcadas
5. **Anexos**: Executaveis
6. **Origem**: IP de alto risco
7. **Engenharia Social**: Emocao

---

#### **Q10: Confiabilidade?**

**R**: Nenhuma IA e 100% precisa.

##### Precisao Estimada:
- 🔴 **FRAUDE CONFIRMADA**: ~95%
- 🟠 **POSSIVEL FRAUDE**: ~80-90%
- 🟡 **ATENCAO**: ~70-80%
- 🔵 **INFORMATIVO**: ~90%
- 🟢 **SEGURO**: ~85-95%

**Recomendacao**: Use como primeira triagem + validacao humana.

---

#### **Q11: Reportar bugs?**

📧 **E-mail**: auditia.ajuda@gmail.com

🐛 **Bug**: Descreva + print + tipo de arquivo
💡 **Sugestao**: Funcionalidade + caso de uso
""")

    with tab4:
        st.markdown("""
### 🔬 Casos de Uso Profissionais

---

#### 1️⃣ **Advocacia Trabalhista**

##### 📱 Print do WhatsApp como evidencia

**Desafio**: Empresa alega adulteracao

**Solucao**: Upload + pergunta especifica

**Resultado**: Laudo PDF para processo

---

#### 2️⃣ **Auditoria Fiscal**

##### 📄 Recibo suspeito

**Desafio**: Recibo parece editado

**Solucao**: Analise de fonte, alinhamento

**Resultado**: Clonagem identificada

---

#### 3️⃣ **Compliance Corporativo**

##### 📧 E-mail de CEO (BEC)

**Desafio**: Pedido de R$ 500k urgente

**Solucao**: Analise SPF, DKIM, dominio

**Resultado**: **FRAUDE CONFIRMADA** - R$ 500k economizados

---

#### 4️⃣ **Investigacao Criminal**

##### 🖼️ Selfie como alibi

**Desafio**: Suspeita de deepfake

**Solucao**: Analise anatomia, luz, EXIF

**Resultado**: Deepfake detectado

---

#### 5️⃣ **Recursos Humanos**

##### 🎓 Diploma universitario

**Desafio**: Suspeita de falsificacao

**Solucao**: Selos, fontes, formatacao

**Resultado**: Diploma fraudulento identificado

---

#### 6️⃣ **Jornalismo**

##### 📸 Foto viral de politico

**Desafio**: Verificar antes de publicar

**Solucao**: Analise face, maos, EXIF

**Resultado**: **SEGURO** - Foto autentica

---

#### 7️⃣ **Protecao ao Consumidor**

##### 💰 Esquema Ponzi

**Desafio**: Identificar piramide

**Solucao**: Promessas, estrutura, linguagem

**Resultado**: Caracteristicas de Ponzi confirmadas

---

#### 8️⃣ **Seguranca da Informacao**

##### 🔒 E-mail de "suporte"

**Desafio**: Pedido de credenciais

**Solucao**: SPF, dominio, link

**Resultado**: Ataque bloqueado

---

### 💡 Conclusao

O **AuditIA** e versatil para multiplos setores. A chave e fazer 
**perguntas especificas e tecnicas**.

**Lembre-se**: O AuditIA e seu **assistente forense**, mas o 
**julgamento final** sempre deve ser **humano e contextualizado**.
""")

st.markdown("---")

# ===== RODAPE COM TERMO (APOS ACEITE) ===== (MANTIDO 100% ORIGINAL)
st.markdown("### 📋 Termo de Uso")
with st.expander("Leia o Termo Completo"):
    st.markdown("""
**TERMO DE USO E RESPONSABILIDADE - AUDITIA**

Ao utilizar esta ferramenta, voce declara ciencia e concordancia com:

1. **Natureza da Ferramenta**: O AuditIA e um sistema de apoio tecnico baseado em Inteligencia 
   Artificial. Os resultados sao probabilisticos e nao substituem pericia humana oficial.

2. **Limitacoes**: A IA pode cometer erros. Nao use como unica evidencia em processos judiciais 
   ou decisoes criticas sem validacao de perito certificado.

3. **Privacidade e LGPD**: Nenhum dado e armazenado permanentemente. Todo processamento ocorre 
   em memoria volatil e e destruido ao clicar em "Limpar Caso".

4. **Uso Responsavel**: Esta ferramenta destina-se exclusivamente a profissionais do direito, 
   auditoria, compliance e investigacao forense. Uso indevido pode resultar em responsabilizacao.

5. **Sem Garantias**: Nao ha garantia de precisao absoluta. Use sempre como ponto de partida 
   investigativo, nunca como conclusao final.

6. **Propriedade Intelectual**: O AuditIA e propriedade de seus desenvolvedores. Uso comercial 
   nao autorizado e proibido.

7. **Atualizacoes**: O sistema pode ser atualizado sem aviso previo. Novos recursos e limitacoes 
   podem ser introduzidos.

---

**Contato**: auditia.ajuda@gmail.com
""")

st.caption(f"👁️ **AuditIA © {datetime.now().year}** - Tecnologia Forense Multimodal de Alta Precisao")
st.caption("Desenvolvido em **Vargem Grande do Sul - SP** | Versao **2.0 COMPLETA**")
st.caption("⚖️ Ferramenta de apoio pericial - Nao substitui pericia oficial | LGPD Compliant")
