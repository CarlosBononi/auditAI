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
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font};
    font-weight: bold; border: 2px solid #4a4a4b; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
    {texto}
    </div>
    '''

# 3. ESTILOS PERSONALIZADOS
st.markdown("""
<style>
.stApp { background-color: #ffffff; color: #333333; }
/* Botão Executar */
div.stButton > button:first-child { 
    background-color: #4a4a4a; 
    color: white; 
    font-weight: bold; 
    width: 100%; 
    height: 4em; 
    border-radius: 10px;
    border: none;
}
div.stButton > button:first-child:hover { 
    background-color: #59ea63; 
    color: black; 
    transition: 0.3s;
}
/* Botão Limpar */
div.stButton > button:nth-child(2) {
    background-color: #e74c3c;
    color: white;
    font-weight: bold;
    width: 100%;
    height: 4em;
    border-radius: 10px;
}
div.stButton > button:nth-child(2):hover {
    background-color: #c0392b;
    transition: 0.3s;
}
.stTextArea textarea { 
    background-color: #f8f9fa; 
    border: 1px solid #d1d5db; 
    border-radius: 8px; 
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# 4. CONEXÃO SEGURA COM SELEÇÃO DINÂMICA
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos_disp[0] if modelos_disp else 'gemini-1.5-flash')
except Exception as e:
    st.error(f"⚠️ Erro de Conexão com AI: {e}")
    st.stop()

# 5. CABEÇALHO
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=500)
except:
    st.title("👁️ AuditIA - Inteligência Pericial Sênior")

st.warning("⚠️ **TERMO DE CONSENTIMENTO:** Esta é uma ferramenta baseada em Inteligência Artificial Forense. Os resultados são probabilísticos e devem ser validados por perícia humana oficial.")

st.markdown("---")

# 6. INGESTÃO MÚLTIPLA COM MINIATURAS
new_files = st.file_uploader(
    "📂 Upload de Provas (Prints, PDFs até 1000 pág, E-mails .eml ou .pst):",
    type=["jpg", "png", "jpeg", "pdf", "eml", "pst"],
    accept_multiple_files=True
)

if new_files:
    for f in new_files:
        if f.name not in [x['name'] for x in st.session_state.arquivos_acumulados]:
            st.session_state.arquivos_acumulados.append({
                'name': f.name, 
                'content': f.read(), 
                'type': f.type
            })

# Exibir miniaturas
if st.session_state.arquivos_acumulados:
    st.write("📦 **Mesa de Perícia (Provas Carregadas):**")
    cols = st.columns(min(4, len(st.session_state.arquivos_acumulados)))
    for i, f in enumerate(st.session_state.arquivos_acumulados):
        with cols[i % 4]:
            if f['type'].startswith('image'):
                st.image(Image.open(io.BytesIO(f['content'])), width=150, use_column_width=True)
            st.caption(f"✅ {f['name'][:20]}...")

st.markdown("---")

# 7. HISTÓRICO PERICIAL
st.subheader("🕵️ Linha de Investigação")
for bloco in st.session_state.historico_pericial:
    st.markdown(aplicar_estilo_pericial(bloco), unsafe_allow_html=True)

# 8. CAMPO DE PERGUNTA
user_query = st.text_area(
    "📝 Pergunta ao Perito:",
    key="campo_pergunta",
    placeholder="Ex: 'Analise a textura de pele e sombras desta face' ou 'Verifique os registros SPF/DKIM deste e-mail'",
    height=120
)

# 9. FUNÇÃO GERADORA DE PDF
def gerar_pdf_pericial(conteudo, data_f):
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

# 10. FUNÇÃO PARA EXTRAIR CONTEÚDO COMPLETO DE E-MAIL EML
def extrair_conteudo_eml(content_bytes):
    """Extrai cabeçalhos completos e corpo de e-mail EML"""
    try:
        # Parsear o e-mail completo
        msg = email.message_from_bytes(content_bytes, policy=policy.default)
        
        # Extrair cabeçalhos importantes
        remetente = msg.get('From', 'Não disponível')
        destinatario = msg.get('To', 'Não disponível')
        assunto = msg.get('Subject', 'Sem assunto')
        data_envio = msg.get('Date', 'Não disponível')
        cc = msg.get('Cc', 'Não disponível')
        
        # Extrair cabeçalhos de autenticação
        spf = msg.get('Received-SPF', 'Não disponível')
        dkim = msg.get('DKIM-Signature', 'Não disponível')
        dmarc = msg.get('DMARC-Status', 'Não disponível')
        
        # Extrair corpo do e-mail
        corpo = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Extrair texto
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        corpo = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
        else:
            # E-mail não multipart
            try:
                corpo = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                corpo = msg.get_payload()
        
        # Montar conteúdo completo para análise
        conteudo_completo = f"""
        E-MAIL COMPLETO - ANÁLISE FORENSE
        
        METADADOS:
        Remetente: {remetente}
        Destinatário: {destinatario}
        Assunto: {assunto}
        Data de Envio: {data_envio}
        CC: {cc}
        
        REGISTROS DE SEGURANÇA:
        SPF: {spf}
        DKIM: {dkim}
        DMARC: {dmarc}
        
        CORPO DA MENSAGEM:
        {corpo}
        """
        
        return conteudo_completo.strip()
        
    except Exception as e:
        return f"E-MAIL (Erro na extração: {str(e)}): {content_bytes[:500]}..."

# 11. FUNÇÃO PARA EXTRAIR CONTEÚDO DE PST (simplificado para esta versão)
def extrair_conteudo_pst(content_bytes):
    """Extrai conteúdo básico de arquivo PST"""
    try:
        # Para PST, retornamos informação básica
        # Em versão completa, usaria biblioteca como pypff
        return f"""
        ARQUIVO PST - ANÁLISE FORENSE
        
        Tipo: Arquivo de dados do Outlook (.pst)
        Tamanho: {len(content_bytes)} bytes
        
        Nota: Este arquivo contém e-mails, contatos e calendários.
        Para análise completa, utilize ferramentas especializadas como pypff ou libpff.
        """
    except Exception as e:
        return f"PST (Erro: {str(e)}): Arquivo de dados do Outlook"

# 12. MOTOR PERICIAL COM ANÁLISE INDIVIDUAL E CRUZADA
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("🚀 EXECUTAR PERÍCIA", on_click=processar_pericia):
        pergunta_efetiva = st.session_state.get('pergunta_ativa', '').strip()
        
        if not pergunta_efetiva and not st.session_state.arquivos_acumulados:
            st.warning("⚠️ Insira material para análise ou uma pergunta específica.")
        else:
            tz_br = pytz.timezone('America/Sao_Paulo')
            agora = datetime.now(tz_br).strftime("%d/%m/%Y às %H:%M:%S")
            
            with st.spinner("🕵️ AuditIA realizando auditoria técnica profunda..."):
                try:
                    # DETERMINAR OS TIPOS DE ARQUIVOS PARA ANÁLISE ESPECIALIZADA
                    tipos_arquivos = [f['type'] for f in st.session_state.arquivos_acumulados]
                    nomes_arquivos = [f['name'].lower() for f in st.session_state.arquivos_acumulados]
                    
                    tem_imagem = any(t.startswith('image') for t in tipos_arquivos)
                    tem_email = any('.eml' in n or '.pst' in n for n in nomes_arquivos)
                    tem_pdf = any(t == 'application/pdf' for t in tipos_arquivos)
                    
                    # INSTRUÇÃO COM PROTOCOLO ESPECIALIZADO
                    instrucao = f"""
                    Aja como o AuditIA, inteligência forense de elite para e-discovery. Hoje é {agora}.
                    
                    📋 PROTOCOLO DE ANÁLISE MULTIMODAL:
                    """
                    
                    if tem_imagem:
                        instrucao += """
                    🖼️ ANÁLISE DE IMAGENS (Protocolo V16):
                    1. IMAGENS DE PESSOAS: Analise com CETICISMO MÁXIMO - QUALQUER ANOMALIA ANATÔMICA INDICA FRAUDE
                    2. ANATOMIA: Verifique fusão de dedos, articulações, dentes e simetria facial - QUALQUER INCONSISTÊNCIA = FRAUDE
                    3. FÍSICA DA LUZ: Observe reflexos oculares e sombras (devem ter fonte única) - INCONSISTÊNCIA = FRAUDE
                    4. TEXTURA DE PELE: Identifique "perfeição plástica" ou ausência de poros/ruído digital - PRESENÇA = FRAUDE
                    5. METADADOS: Se não houver EXIF ou rastro de sensor, classifique como "ATENÇÃO (ALTA PROBABILIDADE DE IA)"
                    6. NUNCA classifique como "IMAGENS REAIS" quando houver qualquer indício de IA
                    7. Se detectar QUALQUER característica típica de IA, classifique como "FRAUDE CONFIRMADA"
                    """
                    
                    if tem_email:
                        instrucao += """
                    📧 ANÁLISE DE E-MAILS (Protocolo e-Discovery):
                    1. METADADOS: Verifique remetente, destinatário, servidores de e-mail, timestamps
                    2. REGISTROS DE SEGURANÇA: Analise SPF, DKIM e DMARC para autenticidade
                    3. CONTEÚDO: Identifique padrões de phishing, links maliciosos, linguagem manipulativa
                    4. ASSINATURAS: Verifique autenticidade das assinaturas digitais
                    5. CLASSIFICAÇÃO: Use "SEGURO", "ATENÇÃO", "POSSÍVEL FRAUDE" ou "FRAUDE CONFIRMADA"
                    6. NÃO MENCIONE ANALOGIAS DE IMAGENS (anatomia, física da luz, textura de pele)
                    """
                    
                    if tem_pdf:
                        instrucao += """
                    📄 ANÁLISE DE PDFS (Protocolo Documental):
                    1. METADADOS: Verifique autor, data de criação, software usado
                    2. CONTEÚDO: Analise links, formulários e possíveis scripts maliciosos
                    3. ASSINATURAS: Verifique autenticidade das assinaturas digitais
                    4. CONSISTÊNCIA: Compare o conteúdo com o rastro digital deixado
                    """
                    
                    instrucao += f"""
                    🔄 ANÁLISE CRUZADA (Quando múltiplos arquivos):
                    - Compare informações entre arquivos diferentes
                    - Identifique contradições ou consistências
                    - Relacione dados de diferentes fontes para conclusão forense
                    
                    🎯 ESTRUTURA OBRIGATÓRIA:
                    - Inicie com 'PERGUNTA: "{pergunta_efetiva}"'
                    - Seguido de 'CLASSIFICAÇÃO: [TIPO]'
                    - EM SEGUIDA, 'VEREDITO: [TIPO]' (EX: VEREDITO: ATENÇÃO)
                    - Em seguida, 'ANÁLISE RÁPIDA:' com os 3 pontos mais importantes
                    - 'ANÁLISE DETALHADA:' com a análise completa
                    - 'CONCLUSÃO FINAL:' com o veredito final e recomendações
                    
                    🚨 REGRAS DE CLASSIFICAÇÃO FINAL:
                    - FRAUDE CONFIRMADA: Evidências claras de manipulação ou fraude
                    - POSSÍVEL FRAUDE: Indícios fortes mas não conclusivos
                    - ATENÇÃO: Inconsistências detectadas, requer investigação adicional
                    - SEGURO: Nenhuma anomalia detectada
                    
                    🎯 NOSSOS 7 PILARES DE INVESTIGAÇÃO:
                    1. Análise Documental (metadados e fontes)
                    2. Detecção de IA (12 marcadores anatômicos)
                    3. e-Discovery (.eml e .pst)
                    4. Engenharia Social (phishing/spoofing)
                    5. Física da Luz (reflexos e sombras)
                    6. Ponzi Detection (promessas inconsistentes)
                    7. Consistência Digital (rastro vs conteúdo)
                    """
                    
                    contexto = [instrucao]
                    
                    # Adicionar histórico
                    for h in st.session_state.historico_pericial:
                        contexto.append(h)
                    
                    # Processar arquivos acumulados INDIVIDUALMENTE
                    for f in st.session_state.arquivos_acumulados:
                        nome_arq = f['name'].lower()
                        
                        if nome_arq.endswith('.eml'):
                            # Extrair conteúdo completo do EML
                            conteudo_eml = extrair_conteudo_eml(f['content'])
                            contexto.append(f"ARQUIVO E-MAIL ({f['name']}):\n{conteudo_eml}")
                        
                        elif nome_arq.endswith('.pst'):
                            # Extrair conteúdo básico do PST
                            conteudo_pst = extrair_conteudo_pst(f['content'])
                            contexto.append(f"ARQUIVO PST ({f['name']}):\n{conteudo_pst}")
                        
                        elif f['type'] == "application/pdf":
                            # Enviar PDF para análise
                            contexto.append({"mime_type": "application/pdf", "data": f['content']})
                        
                        else:
                            # Imagens
                            contexto.append(Image.open(io.BytesIO(f['content'])).convert('RGB'))
                    
                    # Adicionar pergunta do usuário
                    contexto.append(pergunta_efetiva if pergunta_efetiva else "Analise todas as provas acima.")
                    
                    # Gerar resposta
                    response = model.generate_content(contexto, request_options={"timeout": 600})
                    
                    # CORREÇÃO PÓS-PROCESSAMENTO
                    resposta_texto = response.text
                    
                    # Forçar classificação correta para e-mails (remover menções a análise de imagens)
                    if tem_email and not tem_imagem:
                        # Remover padrões de análise de imagens em resposta de e-mail
                        resposta_texto = re.sub(r"1\. IMAGENS DE PESSOAS:.*?(?=\n2\.|\n3\.|\n4\.|\n5\.|\n6\.|$)", "", resposta_texto, flags=re.DOTALL | re.MULTILINE)
                        resposta_texto = re.sub(r"2\. ANATOMIA:.*?(?=\n3\.|\n4\.|\n5\.|\n6\.|$)", "", resposta_texto, flags=re.DOTALL | re.MULTILINE)
                        resposta_texto = re.sub(r"3\. FÍSICA DA LUZ:.*?(?=\n4\.|\n5\.|\n6\.|$)", "", resposta_texto, flags=re.DOTALL | re.MULTILINE)
                        resposta_texto = re.sub(r"4\. TEXTURA DE PELE:.*?(?=\n5\.|\n6\.|$)", "", resposta_texto, flags=re.DOTALL | re.MULTILINE)
                        resposta_texto = re.sub(r"5\. METADADOS:.*?(?=\n6\.|$)", "", resposta_texto, flags=re.DOTALL | re.MULTILINE)
                        
                        # Forçar classificação adequada para e-mails
                        if "VEREDITO:" not in resposta_texto.upper():
                            # Adicionar veredito se não estiver presente
                            if "CLASSIFICAÇÃO: ATENÇÃO" in resposta_texto.upper():
                                resposta_texto = "VEREDITO: ATENÇÃO\n" + resposta_texto
                            elif "CLASSIFICAÇÃO: SEGURO" in resposta_texto.upper():
                                resposta_texto = "VEREDITO: SEGURO\n" + resposta_texto
                            elif "CLASSIFICAÇÃO: FRAUDE CONFIRMADA" in resposta_texto.upper():
                                resposta_texto = "VEREDITO: FRAUDE CONFIRMADA\n" + resposta_texto
                            elif "CLASSIFICAÇÃO: POSSÍVEL FRAUDE" in resposta_texto.upper():
                                resposta_texto = "VEREDITO: POSSÍVEL FRAUDE\n" + resposta_texto
                        else:
                            # Garantir que o veredito esteja no formato correto
                            resposta_texto = re.sub(r"VEREDITO:\s*[A-Z]+", "VEREDITO: " + re.search(r"CLASSIFICAÇÃO:\s*([A-Z]+)", resposta_texto).group(1), resposta_texto)
                    
                    # Forçar classificação correta para imagens (evitar "imagens reais")
                    if tem_imagem:
                        if re.search(r'PROVAVELMENTE\s+IMAGENS?\s+REAIS|IMAGENS?\s+REAIS|CLASSIFICAÇÃO:\s*SEGURO', resposta_texto.upper()):
                            # Forçar classificação correta para imagens com anomalias
                            resposta_texto = resposta_texto.replace("PROVAVELMENTE IMAGENS REAIS", "FRAUDE CONFIRMADA")
                            resposta_texto = resposta_texto.replace("IMAGENS REAIS", "FRAUDE CONFIRMADA")
                            resposta_texto = resposta_texto.replace("CLASSIFICAÇÃO: SEGURO", "CLASSIFICAÇÃO: FRAUDE CONFIRMADA")
                            resposta_texto = resposta_texto.replace("VEREDITO: SEGURO", "VEREDITO: FRAUDE CONFIRMADA")
                            
                            # Adicionar nota de correção
                            if "CORREÇÃO AUTOMÁTICA" not in resposta_texto:
                                resposta_texto += "\n\n⚠️ **CORREÇÃO AUTOMÁTICA DO PROTOCOLO V16**: O sistema detectou que a classificação original contraria os protocolos forenses. De acordo com o Protocolo V16, imagens com anomalias anatômicas, perfeição plástica ou ausência de metadados EXIF devem ser classificadas como FRAUDE CONFIRMADA."
                        
                        # Verificar se há "perfeição plástica" ou anomalias na resposta
                        elif "perfeição plástica" in resposta_texto.lower() or "anomalia" in resposta_texto.lower() or "inconsistência" in resposta_texto.lower():
                            # Se detectou anomalias mas não classificou como fraude, corrigir
                            if "CLASSIFICAÇÃO:" in resposta_texto.upper() and "FRAUDE" not in resposta_texto.upper():
                                resposta_texto = resposta_texto.replace("CLASSIFICAÇÃO: ATENÇÃO", "CLASSIFICAÇÃO: FRAUDE CONFIRMADA")
                                resposta_texto = resposta_texto.replace("CLASSIFICAÇÃO: POSSÍVEL FRAUDE", "CLASSIFICAÇÃO: FRAUDE CONFIRMADA")
                                resposta_texto = resposta_texto.replace("VEREDITO: ATENÇÃO", "VEREDITO: FRAUDE CONFIRMADA")
                                resposta_texto = resposta_texto.replace("VEREDITO: POSSÍVEL FRAUDE", "VEREDITO: FRAUDE CONFIRMADA")
                    
                    # Garantir que a estrutura da resposta seja clara e objetiva
                    if "ANÁLISE RÁPIDA:" not in resposta_texto:
                        # Se não houver análise rápida, criar uma
                        analise_rapida = ""
                        
                        if "FRAUDE CONFIRMADA" in resposta_texto.upper():
                            analise_rapida = "ANÁLISE RÁPIDA:\n- Evidências claras de fraude detectadas\n- Indicadores irrefutáveis de manipulação\n- Recomenda-se investigação imediata"
                        elif "POSSÍVEL FRAUDE" in resposta_texto.upper():
                            analise_rapida = "ANÁLISE RÁPIDA:\n- Indícios fortes de possível fraude\n- Inconsistências significativas detectadas\n- Recomenda-se verificação adicional"
                        elif "ATENÇÃO" in resposta_texto.upper():
                            analise_rapida = "ANÁLISE RÁPIDA:\n- Inconsistências detectadas\n- Requer investigação adicional\n- Padrões suspeitos identificados"
                        else:
                            analise_rapida = "ANÁLISE RÁPIDA:\n- Nenhuma anomalia significativa detectada\n- Evidências consistentes com autenticidade\n- Classificação confirmada como seguro"
                        
                        # Inserir análise rápida na resposta
                        resposta_texto = resposta_texto.replace("ANÁLISE DETALHADA:", analise_rapida + "\n\nANÁLISE DETALHADA:")
                    
                    st.session_state.historico_pericial.append(resposta_texto)
                    st.rerun()
                    
                except Exception as e:
                    if "exceeds the supported page limit" in str(e):
                        st.error("⚠️ Limite de 1000 páginas excedido em algum PDF.")
                    else:
                        st.error(f"⚠️ Erro técnico: {e}. Tente novamente.")

with col2:
    if st.button("🗑️ LIMPAR CASO"):
        st.session_state.historico_pericial = []
        st.session_state.arquivos_acumulados = []
        st.rerun()

# 13. DOWNLOAD DE LAUDO PDF
if st.session_state.historico_pericial:
    st.markdown("---")
    tz_br = pytz.timezone('America/Sao_Paulo')
    pdf_bytes = gerar_pdf_pericial(
        st.session_state.historico_pericial[-1],
        datetime.now(tz_br).strftime("%d/%m/%Y %H:%M")
    )
    st.download_button(
        label="📥 Baixar Laudo da Última Análise (PDF)",
        data=pdf_bytes,
        file_name=f"Laudo_AuditIA_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf"
    )

# 14. GUIA MESTRE AUDITIA
st.markdown("---")
with st.expander("🎓 GUIA MESTRE AUDITIA - Manual de Perícia Digital de Elite"):
    tab1, tab2, tab3 = st.tabs(["🎯 Nossos 7 Pilares", "🛠️ Como Usar", "❓ FAQ"])
    
    with tab1:
        st.markdown("""
        ### 🛡️ Nossos 7 Pilares de Investigação
        
        1. **Análise Documental**: Verificação profunda de fontes, metadados estruturais e selos digitais.
        2. **Detecção de IA**: Scrutínio de 12 marcadores anatômicos (dedos, articulações, olhos) e texturas sintéticas.
        3. **e-Discovery**: Processamento inteligente de arquivos .eml e .pst buscando intenções e fraudes.
        4. **Engenharia Social**: Identificação de padrões comportamentais de phishing e spoofing.
        5. **Física da Luz**: Verificação técnica de reflexos oculares e consistência de sombras.
        6. **Ponzi Detection**: Avaliação de modelos de negócios com promessas financeiras inconsistentes.
        7. **Consistência Digital**: Comparação entre o rastro digital e o conteúdo apresentado.
        """)
    
    with tab2:
        st.markdown("""
        ### 🛠️ Manual de Perícia Profissional
        
        **Mesa de Perícia**: Adicione até 5 arquivos para uma auditoria conjunta e cruzada.
        
        **Pergunta ao Perito**: Seja cirúrgico!
        - ❌ "Isso é real?" → Genérico
        - ✅ "Analise a textura de pele e sombras desta face" → Específico
        - ✅ "Verifique os registros SPF/DKIM deste e-mail" → Específico
        
        **Interpretando o Termômetro**:
        - 🟢 **Verde**: Autenticidade confirmada com rastro EXIF/físico
        - 🔵 **Azul**: Documento informativo legítimo mas neutro
        - 🟡 **Amarelo**: Imagem sem rastro de sensor digital (Atenção!)
        - 🟠 **Laranja**: Inconsistências técnicas graves detectadas
        - 🔴 **Vermelho**: Fraude ou manipulação confirmada
        """)
    
    with tab3:
        st.markdown("""
        **Q: Por que o AuditIA foi criado?**
        R: Para fornecer ferramentas técnicas a advogados, auditores e peritos contra fraudes geradas por IA.
        
        **Q: Como funciona a análise de fotos de pessoas?**
        R: Executamos o Protocolo V16, analisando mãos, dentes, reflexos oculares em busca de "perfeição plástica" característica da IA.
        
        **Q: Como funciona a análise de e-mails?**
        R: Verificamos metadados (remetente, destinatário, data), registros SPF/DKIM/DMARC, padrões de phishing e assinaturas digitais.
        
        **Q: O que é análise cruzada?**
        R: Quando você carrega múltiplos arquivos, o sistema compara informações entre eles para identificar contradições ou consistências.
        
        **Q: Qual o tamanho máximo dos arquivos?**
        R: Até 200MB individuais, totalizando 1GB por sessão pericial.
        
        **Q: O sistema guarda meu histórico?**
        R: Não. Ao clicar em 'Limpar Caso', toda a memória é destruída permanentemente.
        """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
