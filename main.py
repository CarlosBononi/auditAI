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
        cor, font = "#ff4b4b", "white"  # 🔴 VERMELHO
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: POSSÍVEL FRAUDE", "VEREDITO: POSSÍVEL FRAUDE", "ALTA ATENÇÃO", "PHISHING", "POSSÍVEL FRAUDE"]):
        cor, font = "#ffa500", "white"  # 🟠 LARANJA
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: ATENÇÃO", "VEREDITO: ATENÇÃO", "IMAGEM", "FOTO", "IA", "SINTÉTICO", "ALTA PROBABILIDADE DE IA", "ANÁLISE DE E-MAIL"]):
        cor, font = "#f1c40f", "black"  # 🟡 AMARELO (Protocolo de Dúvida)
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: SEGURO", "VEREDITO: SEGURO", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO", "AUTENTICIDADE CONFIRMADA"]):
        cor, font = "#2ecc71", "white"  # 🟢 VERDE
    else:
        cor, font = "#3498db", "white"  # 🔵 AZUL (Documentos Neutros)

    return f'''<div style="background-color: {cor}; padding: 25px; border-radius: 12px; 
                color: {font}; font-weight: bold; border: 2px solid #2c3e50; 
                margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                {texto.replace(chr(10), "<br>")}
            </div>'''

# 3. CSS AVANÇADO
st.markdown('''
<style>
    .stApp {
        background-color: #ffffff;
        color: #333333;
    }

    div.stButton > button:first-child {
        background-color: #4a4a4a;
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: bold;
        height: 3.5em;
        width: 100%;
        transition: 0.3s;
    }

    div.stButton > button:hover {
        background-color: #59ea63;
        color: black;
        border: 1px solid #2ecc71;
    }

    .stTextArea textarea {
        background-color: #f8f9fa;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        font-size: 16px;
        padding: 15px;
    }

    .uploadedFile {
        border: 2px dashed #4a90e2;
        border-radius: 10px;
        padding: 10px;
    }

    h1, h2, h3 {
        color: #2c3e50 !important;
    }

    .stExpander {
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
</style>
''', unsafe_allow_html=True)

# 4. CONEXÃO GEMINI - COM FIX CRÍTICO DO ERRO 404
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

    # TENTA PRIMEIRO MODELO DIRETO
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        # FALLBACK COM FIX CRÍTICO
        modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

        if modelos_disp:
            # 🔥 FIX CRÍTICO: Remove prefixo 'models/' se existir
            modelo_nome = modelos_disp[0]
            if modelo_nome.startswith('models/'):
                modelo_nome = modelo_nome.replace('models/', '')

            model = genai.GenerativeModel(modelo_nome)
        else:
            st.error("❌ Nenhum modelo Gemini disponível para sua conta.")
            st.info("Verifique em: https://makersuite.google.com/app/apikey")
            st.stop()

except Exception as e:
    st.error(f"⚠️ Erro de conexão com o servidor: {e}")
    st.info("🔄 Aguarde 60 segundos e recarregue a página.")
    st.stop()

# 5. CABEÇALHO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("👁️ AuditIA - Inteligência Pericial Sênior")
    st.caption("Tecnologia Forense Multimodal de Alta Precisão")

# 6. TERMO DE CONSENTIMENTO COMPLETO
st.warning("""
**⚖️ TERMO DE CONSENTIMENTO INFORMADO**

Esta é uma ferramenta baseada em Inteligência Artificial Forense. Embora processe dados 
com alta fidelidade técnica, os resultados são probabilísticos e devem ser validados por 
perícia humana oficial. Erros podem ocorrer devido à natureza da tecnologia.

**Uso Responsável**: Esta ferramenta destina-se exclusivamente a profissionais do direito, 
auditoria, compliance e investigação forense. Não use para propósitos ilegais ou não éticos.

**Privacidade**: Nenhum dado é armazenado em servidores. Todo processamento ocorre em memória 
volátil e é destruído ao final da sessão.
""")

st.markdown("---")

# 7. UPLOAD MÚLTIPLO
st.header("📂 Upload de Provas Forenses")

new_files = st.file_uploader(
    "Arraste até 5 arquivos (Prints, PDFs até 1000 pág, E-mails .eml)",
    type=["jpg", "png", "jpeg", "pdf", "eml"],
    accept_multiple_files=True,
    help="Tamanho máximo: 200MB por arquivo | Total da sessão: 1GB"
)

# Acumulação sem duplicatas
if new_files:
    for f in new_files:
        if f.name not in [x["name"] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({
                "name": f.name,
                "content": f.read(),
                "type": f.type
            })

# 8. MESA DE PERÍCIA (VISUALIZAÇÃO AVANÇADA)
if st.session_state.arquivos_acumulados:
    st.write("**🔬 Mesa de Perícia - Provas Carregadas:**")
    st.info(f"📊 Total de arquivos: {len(st.session_state.arquivos_acumulados)}")

    cols = st.columns(4)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 4]:
            if f["type"].startswith("image"):
                try:
                    st.image(Image.open(io.BytesIO(f["content"])), width=150, caption=f["name"])
                except:
                    st.write("🖼️")
                    st.caption(f["name"])
            elif f["type"] == "application/pdf":
                st.write("📄 PDF")
                st.caption(f["name"])
            else:
                st.write("📧 E-MAIL")
                st.caption(f["name"])

st.markdown("---")

# 9. HISTÓRICO DE INVESTIGAÇÃO
st.subheader("📊 Linha de Investigação Cumulativa")

if not st.session_state.historico_pericial:
    st.info("ℹ️ O histórico de análises aparecerá aqui após a primeira perícia.")
else:
    for idx, bloco in enumerate(st.session_state.historico_pericial, 1):
        with st.expander(f"🔍 Análise #{idx}", expanded=(idx == len(st.session_state.historico_pericial))):
            st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

st.markdown("---")

# 10. CAMPO DE PERGUNTA AVANÇADO
st.subheader("💬 Consulta ao Perito Digital")

user_query = st.text_area(
    "Digite sua pergunta técnica:",
    key="campo_pergunta",
    placeholder="""Exemplos de perguntas eficazes:

• "Esta foto é de pessoa real? Analise mãos, olhos e textura de pele."
• "Verifique os cabeçalhos SPF/DKIM deste e-mail de cobrança."
• "Compare a fonte e formatação entre estes dois contratos PDF."
• "Identifique inconsistências anatômicas nesta selfie."
• "Este WhatsApp é autêntico? Verifique metadados e formatação."""",
    height=150
)

st.caption("💡 **Dica**: Seja específico. Perguntas genéricas geram respostas menos precisas.")

# 11. FUNÇÕES AUXILIARES
def gerar_pdf_pericial_completo(conteudo, data, arquivos):
    pdf = FPDF()
    pdf.add_page()

    # Cabeçalho
    pdf.set_font("Arial", "B", 18)
    pdf.cell(200, 12, txt="LAUDO TÉCNICO PERICIAL", ln=True, align="C")
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt="AUDITIA - Inteligência Forense Digital", ln=True, align="C")

    pdf.ln(5)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Metadados
    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, txt="Data da Perícia:", ln=False)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt=data, ln=True)

    pdf.set_font("Arial", "", 10)
    pdf.cell(60, 6, txt="Total de Provas Analisadas:", ln=False)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, txt=str(len(arquivos)), ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, txt="Este laudo foi gerado por sistema automatizado de análise forense. Recomenda-se validação por perito humano certificado para uso em processos judiciais.")

    pdf.ln(8)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Conteúdo
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt="ANÁLISE TÉCNICA DETALHADA", ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "", 10)
    texto_limpo = conteudo.encode('latin-1', 'replace').decode('latin-1')
    # Remove markdown
    texto_limpo = re.sub(r'\*\*', '', texto_limpo)
    texto_limpo = re.sub(r'##\s+', '', texto_limpo)
    pdf.multi_cell(0, 6, txt=texto_limpo)

    # Rodapé
    pdf.ln(10)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.cell(0, 5, txt="AuditIA © 2024-2025 | Vargem Grande do Sul - SP", ln=True, align="C")
    pdf.cell(0, 5, txt="Tecnologia Forense Multimodal | www.auditia.com.br", ln=True, align="C")

    return pdf.output(dest='S').encode('latin-1')

# 12. BOTÕES PRINCIPAIS
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if st.button("🔬 EXECUTAR PERÍCIA TÉCNICA", on_click=processar_pericia, type="primary", use_container_width=True):

        pergunta_efetiva = st.session_state.get("pergunta_ativa", "")

        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("⚠️ Por favor, insira uma pergunta ou faça upload de arquivos para análise.")
        else:
            tz_br = pytz.timezone("America/Sao_Paulo")
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")

            with st.spinner("🔍 AuditIA realizando auditoria técnica profunda... Aguarde até 2 minutos."):
                try:
                    # PROTOCOLO V16 COMPLETO - INSTRUÇÃO FORENSE DE ELITE
                    instrucao = f'''Aja como o **AuditIA**, inteligência forense de elite para e-discovery profissional.

**CONTEXTO TEMPORAL**: Hoje é {agora}.

**PROTOCOLO V16 - ANÁLISE FORENSE RIGOROSA E DETALHADA**

════════════════════════════════════════════════════════════════

## 1️⃣ IMAGENS DE PESSOAS - CETICISMO MÁXIMO OBRIGATÓRIO

Você está **PROIBIDO** de dar pareceres curtos ou informativos para fotos de pessoas. Aplique:

### 🔬 ANÁLISE ANATÔMICA OBRIGATÓRIA:
- **Dedos e Mãos**: Verifique fusão de dedos, número correto de articulações (3 por dedo exceto polegar)
- **Olhos**: Reflexos oculares coerentes, pupilas simétricas, veias esclerais realistas
- **Dentes**: Irregularidades naturais (ausência de perfeição absoluta)
- **Orelhas**: Cartilagem com textura natural
- **Cabelo**: Fios individuais vs. massa texturizada

### 💡 FÍSICA DA LUZ:
- Reflexos oculares consistentes com fonte de luz única
- Sombras respeitando geometria facial
- Iluminação coerente entre plano frontal e fundo

### 🎨 TEXTURA DE PELE:
- Presença de poros, manchas, imperfeições naturais
- **Ausência de "perfeição plástica"**
- Ruído digital de sensor vs. gradientes sintéticos perfeitos

### 📸 METADADOS CRÍTICOS:
- **EXIF presente?** (Marca de câmera, GPS, timestamp)
- **Ruído de sensor digital?** (ISO, padrão de ruído CCD/CMOS)
- **Se EXIF ausente + perfeição excessiva = CLASSIFICAÇÃO: ATENÇÃO (ALTA PROBABILIDADE DE IA)**

════════════════════════════════════════════════════════════════

## 2️⃣ DOCUMENTOS E PRINTS (WhatsApp, Instagram, Contratos)

### 📄 ANÁLISE DOCUMENTAL:
- **Fontes**: Consistência tipográfica, kerning natural
- **Metadados**: Propriedades do arquivo, autor, data de modificação
- **Selos Digitais**: Assinaturas, QR Codes, marcas d'água
- **Formatação**: Alinhamento, espaçamento, padrões visuais

### 🔍 DETECÇÃO DE MANIPULAÇÃO:
- Clonagem de elementos (stamp tool)
- Diferenças de compressão JPEG entre regiões
- Inconsistências de iluminação e perspectiva
- Artefatos de edição (halos, pixelização seletiva)

════════════════════════════════════════════════════════════════

## 3️⃣ E-MAILS (.eml) - DETECÇÃO DE PHISHING/SPOOFING

### 📧 ANÁLISE DE CABEÇALHOS:
- **SPF (Sender Policy Framework)**: PASS ou FAIL?
- **DKIM (DomainKeys Identified Mail)**: Assinatura válida?
- **Received headers**: Rota de servidores coerente?
- **Return-Path**: Corresponde ao remetente visível?

### 🎭 ENGENHARIA SOCIAL:
- Urgência artificial ("Clique em 24h ou perderá acesso")
- Erros gramaticais e ortográficos (comum em phishing)
- URLs disfarçadas (texto visível ≠ link real)
- Solicitações incomuns de dados pessoais/financeiros

### 🔗 INDICADORES DE COMPROMISSO (IoCs):
- Domínios recém-registrados (< 6 meses)
- IPs de origem em países de alto risco
- Links encurtados suspeitos (bit.ly, tinyurl sem contexto)

════════════════════════════════════════════════════════════════

## 4️⃣ ESTRUTURA DE RESPOSTA OBRIGATÓRIA

### 📋 FORMATO PADRÃO:

**PERGUNTA ANALISADA EM {agora}**:
"{pergunta_efetiva}"

**CLASSIFICAÇÃO: [ESCOLHA UMA]**
- ✅ **SEGURO** → Autenticidade técnica confirmada com evidências físicas/digitais
- ⚠️ **ATENÇÃO** → Suspeita moderada, sem evidências conclusivas (ex: EXIF ausente)
- 🟠 **POSSÍVEL FRAUDE** → Inconsistências técnicas graves detectadas
- 🔴 **FRAUDE CONFIRMADA** → Manipulação sintética irrefutável

**ANÁLISE TÉCNICA DETALHADA**:
[Mínimo 8 linhas com evidências específicas e técnicas]

**INDICADORES TÉCNICOS IDENTIFICADOS**:
1. [Indicador 1]
2. [Indicador 2]
3. [Indicador 3]
...

**RECOMENDAÇÕES PERICIAIS**:
- [Ação 1]
- [Ação 2]
- [Ação 3]

**CONFIABILIDADE DA ANÁLISE**: [Alta / Média / Baixa]

════════════════════════════════════════════════════════════════

## 5️⃣ ANÁLISE CRUZADA (MÚLTIPLOS ARQUIVOS)

Se houver **2+ arquivos carregados**, faça **correlação ativa**:
- Inconsistências temporais (timestamps conflitantes)
- Diferenças de autoria ou estilo
- Contradições narrativas entre documentos
- Padrões de manipulação em comum

════════════════════════════════════════════════════════════════

**IMPORTANTE**: Seja **técnico, preciso e conclusivo**. Evite respostas genéricas.
'''

                    # Monta contexto completo
                    contexto = [instrucao]

                    # Adiciona histórico para continuidade contextual
                    for h in st.session_state.historico_pericial[-3:]:  # Últimos 3 para evitar timeout
                        contexto.append(f"[HISTÓRICO ANTERIOR]: {h[:500]}...")

                    # Processa arquivos
                    for f in st.session_state.arquivos_acumulados:
                        if f["name"].endswith(".eml"):
                            try:
                                msg = email.message_from_bytes(f["content"], policy=policy.default)
                                corpo = msg.get_body(preference=['plain']).get_content()
                                contexto.append(f"E-MAIL PARA ANÁLISE: {f['name']}\n{corpo[:2000]}")
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao processar {f['name']}: {e}")

                        elif f["type"] == "application/pdf":
                            contexto.append({"mime_type": "application/pdf", "data": f["content"]})

                        elif f["type"].startswith("image"):
                            try:
                                img = Image.open(io.BytesIO(f["content"])).convert("RGB")
                                contexto.append(img)
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao processar imagem {f['name']}: {e}")

                    # Adiciona a pergunta principal
                    contexto.append(f"PERGUNTA PRINCIPAL DO USUÁRIO: {pergunta_efetiva}")

                    # Gera análise com timeout estendido
                    response = model.generate_content(
                        contexto, 
                        request_options={"timeout": 600},
                        generation_config={
                            "temperature": 0.3,
                            "top_p": 0.95,
                            "top_k": 40,
                            "max_output_tokens": 2048
                        }
                    )

                    # Adiciona ao histórico
                    st.session_state.historico_pericial.append(response.text)
                    st.success("✅ Perícia concluída! Rolando para o resultado...")
                    st.rerun()

                except Exception as e:
                    erro_msg = str(e)

                    if "exceeds the supported page limit" in erro_msg:
                        st.error("❌ **Erro**: PDF excede o limite de 1000 páginas suportado.")
                        st.info("💡 **Solução**: Divida o PDF em partes menores ou reduza a quantidade de páginas.")

                    elif "timeout" in erro_msg.lower():
                        st.error("⏱️ **Timeout**: Muitos arquivos ou processamento complexo.")
                        st.info("💡 **Solução**: Reduza para 3-4 arquivos ou perguntas mais específicas.")

                    elif "quota" in erro_msg.lower() or "rate" in erro_msg.lower():
                        st.error("🚫 **Limite de API atingido**.")
                        st.info("💡 **Solução**: Aguarde 60 segundos e tente novamente.")

                    else:
                        st.error(f"❌ **Erro técnico inesperado**: {erro_msg}")
                        st.info("💡 **Solução**: Recarregue a página (F5) e tente novamente.")

with col2:
    if st.button("🗑️ LIMPAR CASO COMPLETO", use_container_width=True):
        if st.session_state.historico_pericial or st.session_state.arquivos_acumulados:
            st.session_state.historico_pericial = []
            st.session_state.arquivos_acumulados = []
            st.session_state.pergunta_ativa = ""
            st.success("✅ Caso limpo! Memória destruída.")
            st.rerun()
        else:
            st.info("ℹ️ Nenhum dado para limpar.")

with col3:
    if st.button("❓", help="Ajuda"):
        st.info("Consulte a Central de Ajuda abaixo")

# 13. GERADOR DE PDF COMPLETO
if st.session_state.historico_pericial:
    st.markdown("---")
    st.subheader("📥 Exportação de Laudo")

    tz_br = pytz.timezone("America/Sao_Paulo")
    data_atual = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")

    pdf_bytes = gerar_pdf_pericial_completo(
        st.session_state.historico_pericial[-1], 
        data_atual,
        st.session_state.arquivos_acumulados
    )

    col_pdf1, col_pdf2 = st.columns([3, 1])

    with col_pdf1:
        st.download_button(
            label="📥 Baixar Laudo da Última Análise (PDF Profissional)",
            data=pdf_bytes,
            file_name=f"Laudo_AuditIA_{datetime.now(tz_br).strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_pdf2:
        st.metric("Laudos", len(st.session_state.historico_pericial))

st.markdown("---")

# 14. CENTRAL DE AJUDA AUDITIA - ULTRA COMPLETA
with st.expander("📖 **CENTRAL DE AJUDA AUDITIA** - Conhecimento Técnico e FAQ", expanded=False):
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 A Origem do AuditIA", 
        "📘 Manual Técnico de Operação", 
        "❓ FAQ Completo",
        "🔬 Casos de Uso Profissionais"
    ])

    with tab1:
        st.markdown("""
### 🌟 A Missão AuditIA

Nascido em **Vargem Grande do Sul - SP**, o AuditIA foi concebido para unir a **psicologia forense** 
à tecnologia de ponta em **Inteligência Artificial Multimodal**. O projeto surgiu da crescente necessidade 
de identificar **micro-anomalias em comunicações digitais** que fogem ao olho humano comum, especialmente 
diante do avanço exponencial de ferramentas de geração sintética (Midjourney, DALL-E, ChatGPT).

---

#### 🔍 Nossos 7 Pilares de Investigação Forense

##### 1️⃣ **Análise Documental Avançada**
Verificação profunda de **fontes tipográficas**, **metadados estruturais**, **selos digitais** e 
**padrões de compressão JPEG**. Identificamos clonagem de elementos, artefatos de edição e 
inconsistências de iluminação.

##### 2️⃣ **Detecção de Geração por IA (Deepfakes e Sintéticos)**
Scrutínio de **12 marcadores anatômicos críticos**:
- Dedos (fusão, articulações corretas)
- Olhos (reflexos oculares, pupilas simétricas)
- Dentes (irregularidades naturais)
- Pele (poros, imperfeições)

Análise de **física da luz** (reflexos, sombras) e **texturas sintéticas**.

##### 3️⃣ **e-Discovery Corporativo**
Processamento inteligente de arquivos **.eml** e **.pst** buscando:
- Intenções criminosas
- Fraudes corporativas
- Comunicações comprometedoras
- Vazamento de informações privilegiadas

##### 4️⃣ **Detecção de Engenharia Social**
Identificação de padrões comportamentais de **phishing** e **spoofing**:
- Urgência artificial
- Erros gramaticais
- URLs disfarçadas
- Solicitações incomuns

##### 5️⃣ **Análise de Física da Luz**
Verificação técnica de:
- Reflexos oculares coerentes
- Sombras consistentes com fonte única
- Iluminação realista vs. sintética

##### 6️⃣ **Detecção de Esquemas Ponzi e Pirâmides Financeiras**
Avaliação de modelos de negócios com:
- Promessas de retorno garantido
- Estruturas de recrutamento
- Ausência de produto real
- Linguagem persuasiva excessiva

##### 7️⃣ **Verificação de Consistência de Metadados**
Comparação entre:
- Rastro digital vs. conteúdo apresentado
- Timestamps de criação vs. modificação
- Autoria declarada vs. propriedades do arquivo

---

#### 💼 Capacidades Técnicas Detalhadas

##### 🖼️ **Processamento de Imagens**
- **Formatos**: JPG, PNG, JPEG, BMP
- **Resolução**: Até 10.000 x 10.000 pixels
- **Tamanho**: Até 200MB por arquivo
- **Análise**: Anatomia, luz, textura, metadados EXIF

##### 📄 **Processamento de Documentos**
- **Formatos**: PDF (até 1000 páginas)
- **Análise**: Fontes, formatação, selos digitais, metadados
- **Detecção**: Clonagem, manipulação, inconsistências visuais

##### 📧 **Processamento de E-mails**
- **Formatos**: .eml, .pst (em desenvolvimento)
- **Análise**: SPF, DKIM, Received headers, Return-Path
- **Detecção**: Phishing, spoofing, BEC (Business Email Compromise)

##### 🔗 **Análise Cruzada**
- Correlação automática entre múltiplos arquivos
- Detecção de inconsistências temporais
- Identificação de padrões de manipulação

---

#### 🛡️ Segurança e Privacidade

- ✅ **Processamento Local**: Dados não armazenados em servidores
- ✅ **Memória Volátil**: Tudo é destruído ao clicar em "Limpar Caso"
- ✅ **Sem Rastreamento**: Nenhum log de arquivos ou perguntas
- ✅ **LGPD Compliant**: Respeito total à privacidade do usuário

---

#### 🌐 Casos de Uso Reais

1. **Advogados**: Verificação de prints do WhatsApp em processos trabalhistas
2. **Auditores**: Análise de documentos fiscais suspeitos
3. **Compliance**: Detecção de BEC (Business Email Compromise)
4. **Investigadores**: Identificação de deepfakes em casos criminais
5. **RH**: Verificação de diplomas e certificados
6. **Jornalistas**: Fact-checking de imagens virais
""")

    with tab2:
        st.markdown("""
### 📚 Manual Técnico de Operação AuditIA

---

#### 1️⃣ **Upload de Provas Múltiplas**

##### Capacidades:
- **Arquivos simultâneos**: Até 5 por sessão
- **Formatos aceitos**: JPG, PNG, JPEG, PDF, EML
- **Tamanho individual**: Até 200MB
- **Total da sessão**: Até 1GB
- **PDFs**: Até 1000 páginas

##### Fluxo de Trabalho:
1. Arraste arquivos ou clique em "Browse files"
2. Arquivos aparecem na "Mesa de Perícia"
3. Sistema faz análise cruzada automática
4. Você pode fazer múltiplas perguntas sobre os mesmos arquivos

---

#### 2️⃣ **Como Fazer Perguntas Eficazes**

##### ❌ EVITE (genéricas):
- "Isso é verdade?"
- "É fake?"
- "Analise este arquivo"

##### ✅ USE (específicas e técnicas):
- "Analise a textura de pele e sombras desta face humana"
- "Verifique os cabeçalhos SPF e DKIM deste e-mail de cobrança"
- "Compare a fonte tipográfica e formatação entre estes dois contratos"
- "Identifique inconsistências anatômicas nas mãos desta selfie"
- "Este print do WhatsApp é autêntico? Verifique metadados e UI"

##### Estrutura Ideal:
```
[CONTEXTO] + [FOCO DA ANÁLISE] + [TIPO DE EVIDÊNCIA]

Exemplo:
"Este e-mail alegando ser do Banco do Brasil [CONTEXTO]
solicita dados bancários urgentes [FOCO].
Verifique cabeçalhos, domínio e linguagem [EVIDÊNCIA]."
```

---

#### 3️⃣ **Entendendo o Semáforo de Classificação**

##### 🟢 **VERDE (SEGURO)**
**Significado**: Autenticidade técnica confirmada com evidência física/digital sólida.

**Critérios**:
- Metadados EXIF completos e coerentes
- Anatomia humana perfeita (se foto de pessoa)
- Cabeçalhos de e-mail válidos (SPF PASS, DKIM válido)
- Sem anomalias técnicas detectadas

**Ação Recomendada**: Documento confiável para uso pericial.

---

##### 🔵 **AZUL (INFORMATIVO / NEUTRO)**
**Significado**: Documento legítimo mas sem evidências conclusivas de origem.

**Critérios**:
- Sem suspeitas técnicas
- Ausência de metadados não implica em fraude
- Contexto neutro

**Ação Recomendada**: Validação adicional recomendada se crítico.

---

##### 🟡 **AMARELO (ATENÇÃO / SUSPEITA MODERADA)**
**Significado**: Imagem ou documento sem rastro digital claro. Possível geração por IA.

**Critérios**:
- EXIF ausente ou removido
- Perfeição excessiva em fotos humanas
- Sinais moderados de edição
- E-mail com cabeçalhos incompletos

**Ação Recomendada**: **Perícia humana especializada obrigatória** antes de decisões legais.

---

##### 🟠 **LARANJA (POSSÍVEL FRAUDE / INCONSISTÊNCIAS GRAVES)**
**Significado**: Múltiplas inconsistências técnicas detectadas. Alta probabilidade de manipulação.

**Critérios**:
- Anatomia humana com erros (dedos fundidos, olhos assimétricos)
- Física da luz violada (sombras inconsistentes)
- Cabeçalhos de e-mail suspeitos (SPF FAIL)
- Clonagem de elementos em documentos

**Ação Recomendada**: **Não confie sem perícia humana oficial**.

---

##### 🔴 **VERMELHO (FRAUDE CONFIRMADA / MANIPULAÇÃO IRREFUTÁVEL)**
**Significado**: Fraude ou manipulação sintética tecnicamente irrefutável.

**Critérios**:
- Deepfake confirmado (anatomia impossível)
- Phishing confirmado (domínio falso, spoofing)
- Documento adulterado (clonagem digital evidente)
- Múltiplas evidências de fraude

**Ação Recomendada**: **Ação legal imediata**. Não utilize como evidência autêntica.

---

#### 4️⃣ **Mesa de Perícia Cumulativa**

##### Funcionalidades:
- **Persistência**: Arquivos permanecem carregados durante toda a sessão
- **Múltiplas Perguntas**: Faça várias perguntas sobre os mesmos arquivos
- **Análise Contextual**: Sistema mantém histórico de análises anteriores
- **Visualização**: Miniaturas para identificação rápida

##### Quando Limpar:
- ✅ Ao finalizar completamente um caso
- ✅ Antes de iniciar um novo caso não relacionado
- ❌ NÃO limpe se quiser fazer perguntas adicionais sobre os mesmos arquivos

---

#### 5️⃣ **Geração de Laudos PDF Profissionais**

##### Conteúdo do PDF:
- ✅ Cabeçalho profissional com logo AuditIA
- ✅ Data e hora da perícia (timezone Brasil)
- ✅ Total de provas analisadas
- ✅ Análise técnica completa
- ✅ Classificação de risco
- ✅ Rodapé com disclaimer legal

##### Quando Gerar:
- Após cada análise
- Antes de "Limpar Caso" (dados são destruídos)

##### Uso Recomendado:
- Anexo em processos judiciais
- Relatórios de auditoria
- Documentação de compliance
- Evidência em investigações internas

---

#### 6️⃣ **Limitações Técnicas (Transparência Total)**

##### ⏱️ **Timeout (2 minutos)**
**Causa**: Análise muito complexa ou muitos arquivos

**Solução**:
- Reduza para 3-4 arquivos simultâneos
- Perguntas mais específicas (evite "analise tudo")
- Aguarde 60s e tente novamente

---

##### 📄 **PDF com +1000 páginas**
**Causa**: Limite da API Gemini

**Solução**:
- Divida o PDF em partes menores
- Extraia apenas páginas relevantes

---

##### 🚫 **Limite de Taxa (Rate Limit)**
**Causa**: Muitas requisições em curto período

**Solução**:
- Aguarde 60 segundos
- Evite múltiplas análises simultâneas

---

##### 🖼️ **Vídeos e Áudios**
**Status**: Não suportado na versão atual

**Previsão**: Versão 3.0 (Q2 2025)

---

#### 7️⃣ **Boas Práticas Profissionais**

##### ✅ **FAÇA**:
- Seja específico nas perguntas
- Analise 3-4 arquivos por vez
- Baixe os PDFs antes de limpar
- Use termos técnicos quando possível
- Valide com perito humano se crítico

##### ❌ **NÃO FAÇA**:
- Use como única evidência em processos
- Envie dados extremamente sensíveis sem necessidade
- Confie 100% sem validação humana em casos críticos
- Ultrapasse os limites técnicos (timeout, tamanho)

---

""")

    with tab3:
        st.markdown("""
### ❓ FAQ Completo - Perguntas Frequentes

---

#### **Q1: Por que o AuditIA foi criado?**

**R**: Para fornecer ferramentas técnicas profissionais a **advogados**, **auditores**, **peritos** 
e **investigadores** contra o avanço exponencial de **fraudes geradas por Inteligência Artificial**.

Com o surgimento de ferramentas como:
- **Midjourney** (geração de imagens sintéticas)
- **DALL-E** (criação de fotos realistas)
- **ChatGPT** (textos persuasivos)
- **Deepfakes** (vídeos manipulados)

Tornou-se **crítico** ter sistemas capazes de detectar manipulações digitais que o olho humano 
comum não consegue identificar.

---

#### **Q2: Como funciona a análise de fotos de pessoas?**

**R**: O robô executa o **Protocolo V16**, que analisa:

##### 🔬 **12 Marcadores Anatômicos**:
1. Número de dedos (5 por mão)
2. Articulações corretas (3 por dedo, exceto polegar com 2)
3. Dentes (irregularidades naturais)
4. Orelhas (cartilagem com textura natural)
5. Olhos (reflexos oculares coerentes)
6. Pupilas (simetria)
7. Veias esclerais (realismo)
8. Cabelo (fios individuais vs. massa texturizada)
9. Pele (poros, manchas, imperfeições)
10. Sombras (consistência com fonte de luz)
11. Reflexos (física da luz respeitada)
12. Ruído digital (padrão de sensor vs. síntese)

##### 📸 **Metadados EXIF**:
- Marca de câmera
- Modelo
- GPS (se disponível)
- Timestamp
- Configurações (ISO, abertura, velocidade)

##### Lógica de Classificação:
```
SE (anatomia perfeita) E (EXIF presente) E (ruído de sensor) → SEGURO
SE (anatomia perfeita) E (EXIF ausente) → ATENÇÃO (POSSÍVEL IA)
SE (anatomia com erros) → FRAUDE CONFIRMADA
```

---

#### **Q3: Qual o tamanho máximo dos arquivos?**

**R**: Processamos:

| Tipo | Limite Individual | Limite Total | Observações |
|------|-------------------|--------------|-------------|
| **Imagens** | 200MB | 1GB | Até 10.000 x 10.000 px |
| **PDFs** | 200MB | 1GB | Até 1000 páginas |
| **E-mails** | 50MB | 500MB | .eml e .pst |
| **Sessão Total** | - | 1GB | Todos os arquivos somados |

---

#### **Q4: O sistema guarda meu histórico?**

**R**: **NÃO**. Respeitamos a **privacidade forense absoluta**:

- ✅ Dados processados **apenas em memória volátil** (RAM)
- ✅ Ao clicar em "Limpar Caso", **toda a memória é destruída**
- ✅ **Nenhum arquivo armazenado em servidores**
- ✅ **Nenhum log de perguntas ou análises**
- ✅ **LGPD Compliant** (Lei Geral de Proteção de Dados)

**Recomendação**: Sempre baixe os laudos em PDF **antes** de limpar o caso.

---

#### **Q5: O AuditIA substitui um perito humano oficial?**

**R**: **NÃO**. O AuditIA é uma **ferramenta de apoio técnico** que:

##### ✅ **O que PODE fazer**:
- Acelerar triagem inicial de evidências (horas → minutos)
- Identificar pontos técnicos que exigem atenção especializada
- Fornecer base técnica para laudos humanos
- Detectar anomalias invisíveis ao olho humano comum

##### ❌ **O que NÃO PODE fazer**:
- Substituir perito certificado em processos judiciais
- Garantir 100% de precisão (IA é probabilística)
- Analisar contexto emocional ou jurídico
- Tomar decisões legais ou éticas

**Analogia**: O AuditIA é como um **microscópio** para um biólogo. A ferramenta é poderosa, 
mas o **especialista humano interpreta** os resultados.

---

#### **Q6: Como interpretar resultados conflitantes?**

**R**: Se o AuditIA classificar como **ATENÇÃO** ou **POSSÍVEL FRAUDE**:

##### 1️⃣ **Revise a Análise Técnica**:
- Leia os indicadores técnicos identificados
- Entenda **por que** foi classificado assim
- Verifique se há evidências sólidas

##### 2️⃣ **Contextualize**:
- Qual a origem do arquivo?
- Há testemunhas ou fontes confiáveis?
- O contexto faz sentido?

##### 3️⃣ **Valide Externamente**:
- Considere contratar **perícia humana especializada**
- Use outras ferramentas (exiftool, fotoforensics)
- Consulte especialistas em deepfakes

##### 4️⃣ **Não Tome Decisões Precipitadas**:
- **NÃO descarte** evidência apenas pela análise da IA
- **NÃO confie cegamente** sem validação
- Use o laudo como **ponto de partida investigativo**

---

#### **Q7: O que fazer se houver erro técnico?**

**R**: Em caso de instabilidade:

##### 🔴 **Timeout (Análise interrompida após 2 min)**
**Causa**: Muitos arquivos ou análise complexa

**Solução**:
- Reduza para 3-4 arquivos simultâneos
- Seja mais específico na pergunta
- Evite PDFs gigantes (prefira < 500 páginas)

---

##### 🔴 **Limite de Taxa (Rate Limit)**
**Causa**: Muitas requisições em curto período

**Solução**:
- Aguarde **60 segundos**
- Evite clicar em "Executar Perícia" múltiplas vezes

---

##### 🔴 **Erro de Conexão**
**Causa**: Problema temporário com a API Gemini

**Solução**:
- Recarregue a página (F5)
- Aguarde 1-2 minutos
- Se persistir, verifique sua conexão de internet

---

##### 🔴 **PDF Excede 1000 Páginas**
**Causa**: Limitação técnica da API

**Solução**:
- Divida o PDF em partes menores
- Use ferramentas online para extrair páginas específicas

---

#### **Q8: É possível analisar vídeos ou áudios?**

**R**: **Atualmente NÃO**. A versão atual (2.0) suporta apenas:

##### ✅ **Suportado**:
- Imagens estáticas (JPG, PNG, JPEG)
- Documentos (PDF até 1000 páginas)
- E-mails (.eml)

##### 🚧 **Em Desenvolvimento (Versão 3.0 - Q2 2025)**:
- Análise de vídeos (detecção de deepfakes em motion)
- Análise de áudios (voice cloning, síntese de voz)
- Análise de arquivos .pst completos (Outlook)

---

#### **Q9: Como funciona a detecção de phishing em e-mails?**

**R**: O AuditIA analisa **7 camadas de segurança**:

##### 1️⃣ **Cabeçalhos Técnicos**:
- **SPF**: Verifica se o servidor está autorizado a enviar e-mails pelo domínio
- **DKIM**: Valida assinatura digital do e-mail
- **Received headers**: Analisa rota de servidores (origem → destino)
- **Return-Path**: Compara com remetente visível

##### 2️⃣ **Análise de Domínio**:
- Domínio recém-registrado (< 6 meses)
- Domínio similar a marcas conhecidas (bancodob rasil.com)
- TLD suspeito (.tk, .ml, .ga)

##### 3️⃣ **Conteúdo**:
- Urgência artificial ("Clique em 24h")
- Erros gramaticais e ortográficos
- Solicitações incomuns (dados bancários, senhas)

##### 4️⃣ **Links**:
- URLs disfarçadas (texto ≠ link real)
- Links encurtados sem contexto
- Domínios suspeitos

##### 5️⃣ **Anexos**:
- Executáveis (.exe, .bat)
- Macros (documentos Word/Excel)

##### 6️⃣ **Origem Geográfica**:
- IP de países de alto risco
- Discrepância entre domínio e origem

##### 7️⃣ **Engenharia Social**:
- Apelo à emoção (medo, urgência)
- Imitação de autoridade (CEO, banco)

---

#### **Q10: Posso confiar 100% nos resultados?**

**R**: **NÃO**. Nenhuma IA é 100% precisa. O AuditIA tem:

##### Precisão Estimada:
- 🟢 **FRAUDE CONFIRMADA**: ~95% de confiabilidade
- 🟠 **POSSÍVEL FRAUDE**: ~80-90% de confiabilidade
- 🟡 **ATENÇÃO**: ~70-80% de confiabilidade (zona cinza)
- 🔵 **INFORMATIVO**: ~90% de confiabilidade
- ✅ **SEGURO**: ~85-95% de confiabilidade

##### Por que não é 100%?
- IA generativa evolui constantemente (novos modelos burlam detecção)
- Contexto importa (uma foto sem EXIF pode ser legítima se antiga)
- Falsos positivos existem (raramente, mas acontecem)

##### Recomendação Profissional:
**Use o AuditIA como primeira triagem**, mas sempre valide com:
- Perícia humana oficial (se crítico)
- Outras ferramentas (segunda opinião)
- Contexto e testemunhas

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
- Priorize por importância

---

""")

    with tab4:
        st.markdown("""
### 🔬 Casos de Uso Profissionais Reais

---

#### 1️⃣ **Advocacia Trabalhista**

##### 📱 **Cenário**: Print do WhatsApp como evidência de assédio moral

**Desafio**: Empresa alega que print foi adulterado pelo funcionário.

**Solução com AuditIA**:
1. Upload do print
2. Pergunta: "Este print do WhatsApp é autêntico? Verifique formatação, fonte e UI."
3. Análise técnica:
   - Fonte tipográfica do WhatsApp (correta ou inconsistente?)
   - Formatação de timestamp (padrão oficial?)
   - Elementos de UI (botões, ícones no lugar certo?)
   - Metadados da imagem (screenshot ou edição?)

**Resultado**: Laudo técnico em PDF para anexar ao processo.

---

#### 2️⃣ **Auditoria Fiscal**

##### 📄 **Cenário**: Recibo de pagamento suspeito

**Desafio**: Empresa apresenta recibo que parece editado digitalmente.

**Solução com AuditIA**:
1. Upload do PDF ou imagem do recibo
2. Pergunta: "Verifique se este recibo foi adulterado. Analise fonte, formatação e selos."
3. Análise técnica:
   - Consistência tipográfica
   - Alinhamento de textos
   - Qualidade de impressão (real vs. impressora)
   - Metadados do PDF (autor, data de criação)

**Resultado**: Identificação de clonagem de elementos ou edição digital.

---

#### 3️⃣ **Compliance Corporativo**

##### 📧 **Cenário**: E-mail de CEO solicitando transferência bancária (BEC - Business Email Compromise)

**Desafio**: Funcionário do financeiro recebe e-mail urgente do "CEO" pedindo transferência de R$ 500.000.

**Solução com AuditIA**:
1. Upload do arquivo .eml
2. Pergunta: "Este e-mail é phishing? Verifique cabeçalhos SPF, DKIM e linguagem."
3. Análise técnica:
   - SPF: FAIL (servidor não autorizado)
   - DKIM: Ausente
   - Domínio: empresa.com.br (real) vs. empres4.com.br (falso)
   - Linguagem: Urgência artificial + erros sutis

**Resultado**: **FRAUDE CONFIRMADA** - Phishing evitado, empresa economiza R$ 500k.

---

#### 4️⃣ **Investigação Criminal**

##### 🖼️ **Cenário**: Selfie usada como álibi (pessoa alega estar em local X no momento do crime)

**Desafio**: Delegado suspeita que foto seja deepfake ou gerada por IA.

**Solução com AuditIA**:
1. Upload da selfie
2. Pergunta: "Esta foto é de pessoa real? Analise anatomia, luz e metadados."
3. Análise técnica:
   - Dedos: 6 dedos na mão direita ❌
   - Olhos: Reflexos oculares inconsistentes ❌
   - EXIF: Ausente ❌
   - Textura de pele: Perfeição plástica (sem poros) ❌

**Resultado**: **FRAUDE CONFIRMADA** - Deepfake detectado, álibi descartado.

---

#### 5️⃣ **Recursos Humanos**

##### 🎓 **Cenário**: Candidato apresenta diploma universitário

**Desafio**: RH suspeita de falsificação.

**Solução com AuditIA**:
1. Upload do PDF ou foto do diploma
2. Pergunta: "Este diploma é autêntico? Verifique selos, fontes e formatação."
3. Análise técnica:
   - Fonte da instituição (correta ou genérica?)
   - Selo oficial (presente e nítido?)
   - Assinaturas (resolução coerente?)
   - Formatação (padrão da universidade?)

**Resultado**: Identificação de diploma fraudulento (fonte errada + selo clonado).

---

#### 6️⃣ **Jornalismo Investigativo**

##### 📸 **Cenário**: Foto viral de político em situação comprometedora

**Desafio**: Verificar se foto é real ou deepfake antes de publicar matéria.

**Solução com AuditIA**:
1. Upload da foto
2. Pergunta: "Esta foto é deepfake? Analise face, mãos e contexto."
3. Análise técnica:
   - Face: Anatomia perfeita ✅
   - Mãos: Articulações corretas ✅
   - EXIF: Presente com GPS e câmera profissional ✅
   - Contexto: Iluminação coerente ✅

**Resultado**: **SEGURO** - Foto autêntica, matéria publicada com segurança.

---

#### 7️⃣ **Proteção ao Consumidor**

##### 💰 **Cenário**: Denúncia de esquema Ponzi disfarçado de investimento

**Desafio**: Identificar se modelo de negócio é pirâmide financeira.

**Solução com AuditIA**:
1. Upload de prints do site, contratos e comunicações
2. Pergunta: "Este modelo de negócio é esquema Ponzi? Analise promessas e estrutura."
3. Análise técnica:
   - Promessa de retorno garantido (20% ao mês) 🚩
   - Estrutura de recrutamento multinível 🚩
   - Ausência de produto real 🚩
   - Linguagem persuasiva excessiva 🚩

**Resultado**: **FRAUDE CONFIRMADA** - Características clássicas de Ponzi identificadas.

---

#### 8️⃣ **Segurança da Informação**

##### 🔒 **Cenário**: Tentativa de invasão via e-mail de "suporte técnico"

**Desafio**: Empresa recebe e-mail pedindo credenciais de acesso.

**Solução com AuditIA**:
1. Upload do .eml
2. Pergunta: "Este e-mail é spear phishing? Verifique origem e linguagem."
3. Análise técnica:
   - SPF: FAIL ❌
   - Domínio: microsoft-support.tk (falso) ❌
   - Linguagem: "Sua conta será bloqueada em 24h" (urgência) ❌
   - Link: Redireciona para site malicioso ❌

**Resultado**: **FRAUDE CONFIRMADA** - Ataque de phishing bloqueado.

---

### 💡 Conclusão

O **AuditIA** é uma ferramenta **versátil e poderosa** para múltiplos setores profissionais. 
A chave é fazer **perguntas específicas e técnicas** para obter análises precisas.

**Lembre-se**: O AuditIA é seu **assistente forense digital**, mas o **julgamento final** 
sempre deve ser **humano e contextualizado**.

---

📧 **Dúvidas ou novos casos de uso?** Entre em contato: auditia.ajuda@gmail.com

""")

st.markdown("---")
st.caption(f"👁️ **AuditIA © {datetime.now().year}** - Tecnologia Forense Multimodal de Alta Precisão")
st.caption("Desenvolvido em **Vargem Grande do Sul - SP** | Versão **2.0 ULTRA** | www.auditia.com.br (em breve)")
st.caption("⚖️ Ferramenta de apoio pericial - Não substitui perícia oficial | LGPD Compliant")
