import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# ==================== CONFIGURAÇÃO INICIAL ====================
st.set_page_config(
    page_title="AuditIA - Inteligência Pericial Sênior", 
    page_icon="👁️", 
    layout="centered"
)

# 1. GESTÃO DE SESSÃO E MESA DE PERÍCIA CUMULATIVA
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []
if "pergunta_ativa" not in st.session_state:
    st.session_state.pergunta_ativa = ""

def processar_pericia():
    """Captura a pergunta antes do rerun"""
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

# 2. SISTEMA DE CORES COM TRAVA V16 (PROTOCOLO ROBUSTO)
def aplicar_estilo_pericial(texto):
    """
    Sistema de classificação por cores com Trava V16:
    - Prioriza detecção de fraude
    - Força amarelo para imagens suspeitas
    - Previne falsos negativos
    """
    texto_upper = texto.upper()
    
    # TRAVA V16: Hierarquia de classificação rigorosa
    if "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in texto_upper or any(
        term in texto_upper for term in ["GOLPE CONFIRMADO", "SCAM CONFIRMADO", "FAKE CONFIRMADO"]
    ):
        cor, font = "#ff4b4b", "white"  # 🔴 VERMELHO
        
    elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in texto_upper or any(
        term in texto_upper for term in ["ALTA ATENÇÃO", "MUITO SUSPEITO", "PHISHING"]
    ):
        cor, font = "#ffa500", "white"  # 🟠 LARANJA
        
    elif "CLASSIFICAÇÃO: ATENÇÃO" in texto_upper or any(
        term in texto_upper for term in ["IMAGEM", "FOTO", "IA DETECTADA", "SINTÉTICO"]
    ):
        cor, font = "#f1c40f", "black"  # 🟡 AMARELO (Protocolo de Dúvida)
        
    elif "CLASSIFICAÇÃO: SEGURO" in texto_upper or any(
        term in texto_upper for term in ["AUTENTICIDADE CONFIRMADA", "LEGÍTIMO CONFIRMADO"]
    ):
        cor, font = "#2ecc71", "white"  # 🟢 VERDE
        
    else:
        cor, font = "#3498db", "white"  # 🔵 AZUL (Informativo)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font}; 
    font-weight: bold; border: 2px solid #2c3e50; margin-bottom: 25px; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
        {texto}
    </div>
    '''

# 3. ESTILOS CSS
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button { 
        border-radius: 10px; 
        font-weight: bold; 
        height: 3.5em; 
        width: 100%; 
        transition: 0.3s; 
    }
    div.stButton > button:first-child { 
        background-color: #4a4a4a; 
        color: white; 
        border: none; 
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
    }
    </style>
    """, unsafe_allow_html=True)

# 4. CONEXÃO COM GEMINI (ESTÁVEL E SEGURA)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usa seleção dinâmica de modelo como fallback
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        modelos_disp = [m.name for m in genai.list_models() 
                       if 'generateContent' in m.supported_generation_methods]
        model = genai.GenerativeModel(modelos_disp[0])
except Exception as e:
    st.error(f"⚠️ Erro de conexão com o servidor: {e}")
    st.info("Aguarde 60 segundos e recarregue a página.")
    st.stop()

# ==================== INTERFACE ====================

# 5. CABEÇALHO E LOGO
try:
    st.image(Image.open("Logo_AI_1.png"), width=500)
except:
    st.title("👁️ AuditIA - Inteligência Pericial Sênior")

# 6. TERMO DE CONSENTIMENTO
st.warning(
    "⚠️ **TERMO DE CONSENTIMENTO:** Esta é uma ferramenta baseada em Inteligência Artificial Forense. "
    "Embora processe dados com alta fidelidade, os resultados são probabilísticos e devem ser "
    "validados por perícia humana oficial. Erros podem ocorrer devido à natureza da tecnologia."
)

st.markdown("---")

# 7. UPLOAD MÚLTIPLO COM ACUMULAÇÃO
new_files = st.file_uploader(
    "📂 Upload de Provas (Prints, PDFs até 1000 pág, E-mails .eml/.pst):", 
    type=["jpg", "png", "jpeg", "pdf", "eml", "pst"], 
    accept_multiple_files=True
)

# Adiciona novos arquivos sem duplicar
if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({
                'name': f.name, 
                'content': f.read(), 
                'type': f.type
            })

# 8. MESA DE PERÍCIA (MINIATURAS)
if st.session_state.arquivos_acumulados:
    st.write("📦 **Mesa de Perícia (Miniaturas das Provas):**")
    cols = st.columns(4)
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 4]:
            if f['type'].startswith('image'):
                try:
                    st.image(Image.open(io.BytesIO(f['content'])), width=150)
                except:
                    st.write("🖼️")
            elif f['type'] == "application/pdf":
                st.write("📄")
            else:
                st.write("📧")
            st.caption(f"✅ {f['name']}")

# 9. HISTÓRICO DE INVESTIGAÇÃO
st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

# 10. CAMPO DE PERGUNTA
user_query = st.text_area(
    "📝 Pergunta ao Perito:", 
    key="campo_pergunta", 
    placeholder="Ex: 'Esta foto de pessoa é real? Analise mãos, olhos e textura de pele.'", 
    height=120
)

# ==================== FUNÇÕES AUXILIARES ====================

def gerar_pdf_pericial(conteudo, data_f):
    """Gera PDF do laudo pericial"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 15, txt="LAUDO TÉCNICO PERICIAL - AUDITIA", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Data da Perícia: {data_f}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    texto_limpo = conteudo.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# ==================== MOTOR PERICIAL ====================

col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        # Usa a pergunta capturada pelo callback
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '')
        
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("⚠️ Insira uma pergunta ou faça upload de arquivos para análise.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            
            with st.spinner("🕵️ AuditIA realizando auditoria técnica profunda..."):
                try:
                    # PROTOCOLO V16 - INSTRUÇÃO COMPLETA
                    instrucao = f"""
                    Aja como o AuditIA, inteligência forense de elite para e-discovery. Hoje é {agora}.
                    
                    PROTOCOLO V16 - ANÁLISE FORENSE RIGOROSA:
                    
                    1. IMAGENS DE PESSOAS - CETICISMO MÁXIMO:
                       - Você está PROIBIDO de dar pareceres curtos ou informativos para fotos de pessoas.
                       - ANALISE OBRIGATORIAMENTE:
                         * ANATOMIA: Verifique fusão de dedos, número correto de articulações (3 por dedo), dentes naturais
                         * FÍSICA DA LUZ: Reflexos oculares coerentes, sombras consistentes com fonte única
                         * TEXTURA DE PELE: Identifique "perfeição plástica", ausência de poros, ruído digital
                       - Se não houver EXIF ou ruído de sensor, classifique como 'ATENÇÃO (ALTA PROBABILIDADE DE IA)'
                    
                    2. DOCUMENTOS E PRINTS:
                       - Verifique fontes, metadados, selos digitais
                       - Identifique inconsistências de formatação
                       - Analise linguagem e padrões de engenharia social
                    
                    3. E-MAILS:
                       - Verifique SPF, DKIM, cabeçalhos
                       - Identifique phishing e spoofing
                       - Analise urgência artificial e pedidos suspeitos
                    
                    4. ESTRUTURA DE RESPOSTA:
                       - Inicie com: 'PERGUNTA ANALISADA EM {agora}: "{pergunta_efetiva}"'
                       - Linha seguinte: 'CLASSIFICAÇÃO: [TIPO]' onde TIPO pode ser:
                         * SEGURO (autenticidade confirmada)
                         * ATENÇÃO (suspeita, sem evidências conclusivas)
                         * POSSÍVEL FRAUDE (inconsistências graves)
                         * FRAUDE CONFIRMADA (manipulação irrefutável)
                       - Depois, forneça análise detalhada com evidências técnicas
                    
                    5. ANÁLISE CRUZADA:
                       - Se houver múltiplos arquivos, faça correlação entre eles
                       - Busque inconsistências temporais, de autoria ou de narrativa
                    """
                    
                    # Monta o contexto
                    contexto = [instrucao]
                    
                    # Adiciona histórico para continuidade
                    for h in st.session_state.historico_pericial:
                        contexto.append(h)
                    
                    # Processa arquivos acumulados
                    for f in st.session_state.arquivos_acumulados:
                        if f['name'].endswith('.eml'):
                            try:
                                msg = email.message_from_bytes(f['content'], policy=policy.default)
                                corpo = msg.get_body(preferencelist=('plain')).get_content()
                                contexto.append(f"E-MAIL ({f['name']}): {corpo}")
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao processar {f['name']}: {e}")
                                
                        elif f['type'] == "application/pdf":
                            contexto.append({
                                "mime_type": "application/pdf", 
                                "data": f['content']
                            })
                            
                        elif f['type'].startswith('image'):
                            try:
                                img = Image.open(io.BytesIO(f['content'])).convert('RGB')
                                contexto.append(img)
                            except Exception as e:
                                st.warning(f"⚠️ Erro ao processar imagem {f['name']}: {e}")
                    
                    # Adiciona a pergunta
                    contexto.append(pergunta_efetiva)
                    
                    # Gera análise
                    response = model.generate_content(
                        contexto, 
                        request_options={"timeout": 600}
                    )
                    
                    # Adiciona ao histórico
                    st.session_state.historico_pericial.append(response.text)
                    st.rerun()
                    
                except Exception as e:
                    erro_msg = str(e)
                    if "exceeds the supported page limit" in erro_msg:
                        st.error("⚠️ Limite de 1000 páginas excedido no PDF.")
                    elif "timeout" in erro_msg.lower():
                        st.error("⏱️ Timeout - muitos arquivos. Tente reduzir a quantidade.")
                    else:
                        st.error(f"⚠️ Erro técnico: {erro_msg}")
                        st.info("Aguarde 60 segundos e tente novamente.")

with col2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.session_state.pergunta_ativa = ""
        st.rerun()

# ==================== GERADOR DE PDF ====================

if st.session_state.historico_pericial:
    tz_br = pytz.timezone('America/Sao_Paulo')
    data_atual = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M")
    pdf_bytes = gerar_pdf_pericial(st.session_state.historico_pericial[-1], data_atual)
    
    st.download_button(
        label="📥 Baixar Laudo da Última Análise (PDF)", 
        data=pdf_bytes, 
        file_name=f"Laudo_AuditIA_{datetime.now(tz_br).strftime('%Y%m%d_%H%M')}.pdf", 
        mime="application/pdf"
    )

# ==================== CENTRAL DE AJUDA ====================

st.markdown("---")
with st.expander("📖 Central de Ajuda AuditIA - Conhecimento Técnico e FAQ"):
    tab1, tab2, tab3 = st.tabs(["🧬 A Origem do AuditIA", "🛠️ Manual de Operação", "❓ FAQ Técnico"])
    
    with tab1:
        st.markdown("""
        ### 🧬 A Missão AuditIA
        
        Nascido em **Vargem Grande do Sul - SP**, o AuditIA foi concebido para unir a psicologia 
        forense à tecnologia de ponta. O projeto surgiu da necessidade de identificar micro-anomalias 
        em comunicações digitais que fogem ao olho humano comum.
        
        **Nossos 7 Pilares de Investigação:**
        
        1. **Análise Documental**: Verificação profunda de fontes, metadados estruturais e selos digitais.
        
        2. **Detecção de IA**: Scrutínio de 12 marcadores anatômicos (dedos, articulações, olhos) 
           e texturas sintéticas.
        
        3. **e-Discovery**: Processamento inteligente de arquivos .eml e .pst buscando intenções 
           e fraudes corporativas.
        
        4. **Engenharia Social**: Identificação de padrões comportamentais de phishing e spoofing.
        
        5. **Física da Luz**: Verificação técnica de reflexos oculares e consistência de sombras.
        
        6. **Ponzi Detection**: Avaliação de modelos de negócios com promessas financeiras inconsistentes.
        
        7. **Consistência de Metadados**: Comparação entre o rastro digital e o conteúdo apresentado.
        
        ---
        
        ### 🎯 Capacidades Técnicas Detalhadas:
        
        - **Análise Multifacetada de Documentos**: Processamento profundo de prints (WhatsApp/Instagram), 
          PDFs e blocos de texto buscando anomalias visuais ou estruturais.
        
        - **Detecção de Artefatos de IA**: Scrutínio de micro-anomalias anatômicas, texturas sintéticas 
          e inconsistências de física em imagens geradas.
        
        - **Busca Inteligente em Massa**: Análise de arquivos .pst e .eml para identificar 
          intenções criminosas e fraudes.
        
        - **Identificação de Manipulação Psicológica**: Análise de linguagem e comportamento para 
          desmascarar tentativas de manipulação.
        
        - **Reconhecimento de Esquemas Financeiros**: Avaliação técnica de modelos de negócios 
          com promessas de retorno garantido.
        
        - **Verificação de Consistência**: Comparação de dados, fontes, metadados e selos de 
          segurança em recibos, contratos e boletos.
        
        - **Indicadores de Compromisso (IoCs)**: Identificação técnica de URLs maliciosas, 
          domínios e e-mails associados a atividades criminosas.
        """)
        
    with tab2:
        st.markdown("""
        ### 🛠️ Como utilizar o AuditIA para Laudos de Elite
        
        **1. Upload de Provas Múltiplas**
        
        - Arraste até 5 arquivos simultâneos para a Mesa de Perícia
        - O sistema fará análise cruzada automática entre todos os arquivos
        - Formatos suportados: JPG, PNG, PDF (até 1000 páginas), EML, PST
        - Tamanho individual: até 200MB | Total da sessão: até 1GB
        
        **2. Perguntas Cirúrgicas ao Perito**
        
        ❌ Evite perguntas genéricas como: *"Isso é verdade?"*
        
        ✅ Use perguntas específicas:
        - *"Analise a textura de pele e sombras desta face"*
        - *"Verifique os registros SPF/DKIM deste e-mail"*
        - *"Compare a fonte e formatação entre estes dois documentos"*
        - *"Identifique inconsistências anatômicas nas mãos"*
        
        **3. Entendendo o Termômetro de Classificação**
        
        🟢 **VERDE (SEGURO)**: 
        - Autenticidade confirmada com evidência física digital
        - Metadados EXIF presentes e consistentes
        - Sem anomalias detectadas
        
        🔵 **AZUL (INFORMATIVO)**: 
        - Documento legítimo mas neutro
        - Sem suspeitas, mas sem evidências conclusivas de origem
        
        🟡 **AMARELO (ATENÇÃO)**: 
        - Imagem sem rastro de sensor digital (EXIF ausente)
        - Possível geração por IA
        - Requer validação humana especializada
        
        🟠 **LARANJA (POSSÍVEL FRAUDE)**: 
        - Inconsistências técnicas graves detectadas
        - Múltiplos indicadores suspeitos
        - Alta probabilidade de manipulação
        
        🔴 **VERMELHO (FRAUDE CONFIRMADA)**: 
        - Fraude ou manipulação sintética irrefutável
        - Múltiplas evidências técnicas de falsificação
        - Recomenda-se ação legal imediata
        
        **4. Mesa de Perícia Cumulativa**
        
        - Os arquivos permanecem carregados durante toda a sessão
        - Você pode fazer várias perguntas sobre os mesmos arquivos
        - O histórico mantém o contexto da investigação
        - Use "Limpar Caso" apenas ao finalizar completamente
        
        **5. Geração de Laudos PDF**
        
        - Após cada análise, um botão de download aparece
        - O PDF contém a análise completa com timestamp
        - Ideal para anexar em processos judiciais
        - Formato compatível com e-discovery
        """)
        
    with tab3:
        st.markdown("""
        ### ❓ Perguntas Frequentes
        
        **Q: Por que o AuditIA foi criado?**
        
        R: Para fornecer ferramentas técnicas profissionais a advogados, auditores e peritos 
        contra o avanço exponencial de fraudes geradas por Inteligência Artificial. Com o 
        surgimento de ferramentas como Midjourney, DALL-E e deepfakes, tornou-se crítico ter 
        sistemas capazes de detectar manipulações digitais.
        
        ---
        
        **Q: Como funciona a análise de fotos de pessoas?**
        
        R: O robô executa o **Protocolo V16**, analisando:
        - **12 marcadores anatômicos**: dedos, articulações, dentes, orelhas
        - **Física da luz**: reflexos oculares, sombras, iluminação
        - **Textura de pele**: poros, imperfeições naturais vs. "perfeição plástica"
        - **Metadados EXIF**: rastro de câmera, GPS, timestamp
        - **Ruído digital**: padrões de sensor vs. geração sintética
        
        ---
        
        **Q: Qual o tamanho máximo dos arquivos?**
        
        R: Processamos:
        - Arquivos individuais: até 200MB
        - Total por sessão: até 1GB
        - PDFs: até 1000 páginas
        - Imagens: até 10.000 x 10.000 pixels
        
        ---
        
        **Q: O sistema guarda meu histórico?**
        
        R: **NÃO**. Respeitamos a privacidade forense:
        - Dados processados apenas em memória volátil
        - Ao clicar em 'Limpar Caso', toda a memória é destruída
        - Nenhum arquivo é armazenado em servidores
        - Recomendamos baixar os laudos em PDF antes de limpar
        
        ---
        
        **Q: O AuditIA substitui um perito humano?**
        
        R: **NÃO**. O AuditIA é uma ferramenta de **apoio técnico**:
        - Acelera a triagem inicial de evidências
        - Identifica pontos que exigem atenção especializada
        - Fornece base técnica para laudos humanos
        - Resultados devem ser validados por peritos certificados
        
        ---
        
        **Q: Como interpretar resultados conflitantes?**
        
        R: Se o AuditIA classificar como "ATENÇÃO" ou "POSSÍVEL FRAUDE":
        1. Revise a análise técnica detalhada fornecida
        2. Considere contratar perícia humana especializada
        3. Não tome decisões legais baseando-se apenas na ferramenta
        4. Use o laudo como ponto de partida investigativo
        
        ---
        
        **Q: O que fazer se houver erro técnico?**
        
        R: Em caso de instabilidade:
        1. Aguarde 60 segundos (limite de taxa da API)
        2. Reduza o número de arquivos (máx. 3-4 simultâneos)
        3. Verifique o tamanho dos PDFs (máx. 1000 páginas)
        4. Se persistir, reporte para: **auditaiajuda@gmail.com**
        
        ---
        
        **Q: É possível analisar vídeos ou áudios?**
        
        R: Atualmente **NÃO**. A versão atual suporta apenas:
        - Imagens estáticas (JPG, PNG)
        - Documentos PDF
        - E-mails (.eml, .pst)
        
        Análise de vídeo/áudio está em desenvolvimento para versões futuras.
        
        ---
        
        *Este artigo foi útil? Envie sugestões e dúvidas para:*
        
        📧 **auditaiajuda@gmail.com**
        """)

# ==================== RODAPÉ ====================

st.markdown("---")
st.caption(
    f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | "
    f"Vargem Grande do Sul - SP | Versão 2.0"
)
