import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
import email
from email import policy
from datetime import datetime
import pytz

# 1. GESTÃO DE SESSÃO E MESA DE PERÍCIA CUMULATIVA
if "historico_pericial" not in st.session_state:
    st.session_state.historico_pericial = []
if "arquivos_acumulados" not in st.session_state:
    st.session_state.arquivos_acumulados = []

def processar_pericia():
    st.session_state.pergunta_ativa = st.session_state.campo_pergunta
    st.session_state.campo_pergunta = ""

st.set_page_config(page_title="AuditIA - Inteligência Pericial Sênior", page_icon="👁️", layout="centered")

# 2. SEMÁFORO DE CORES COM PROTOCOLO V16 (UNIFICADO)
def aplicar_estilo_pericial(texto):
    texto_upper = texto.upper()
    
    # PROTOCOLO V16 - PRIORIDADE MÁXIMA PARA FRAUDE
    if any(term in texto_upper for term in ["CLASSIFICAÇÃO: FRAUDE CONFIRMADA", "CRIME", "GOLPE", "SCAM"]):
        cor, font = "#ff4b4b", "white"  # 🔴 VERMELHO
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: POSSÍVEL FRAUDE", "ALTA ATENÇÃO", "PHISHING"]):
        cor, font = "#ffa500", "white"  # 🟠 LARANJA
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: ATENÇÃO", "IMAGEM", "FOTO", "IA", "SINTÉTICO"]):
        cor, font = "#f1c40f", "black"  # 🟡 AMARELO (Protocolo de Dúvida)
    elif any(term in texto_upper for term in ["CLASSIFICAÇÃO: SEGURO", "INTEGRIDADE CONFIRMADA", "LEGÍTIMO"]):
        cor, font = "#2ecc71", "white"  # 🟢 VERDE
    else:
        cor, font = "#3498db", "white"  # 🔵 AZUL (Documentos Neutros)
    
    return f'''
    <div style="background-color: {cor}; padding: 25px; border-radius: 12px; color: {font};
    font-weight: bold; border: 2px solid #4a4a4a; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
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

# 10. MOTOR PERICIAL COM PROTOCOLO V16
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
                    # INSTRUÇÃO COM PROTOCOLO V16 MANDATÓRIO
                    instrucao = f"""
                    Aja como o AuditIA, inteligência forense de elite para e-discovery. Hoje é {agora}.
                    
                    📋 PROTOCOLO V16 - ANÁLISE OBRIGATÓRIA:
                    1. IMAGENS DE PESSOAS: Analise com CETICISMO MÁXIMO
                    2. ANATOMIA: Verifique fusão de dedos, articulações, dentes e simetria facial
                    3. FÍSICA DA LUZ: Observe reflexos oculares e sombras (devem ter fonte única)
                    4. TEXTURA DE PELE: Identifique "perfeição plástica" ou ausência de poros/ruído digital
                    5. METADADOS: Se não houver EXIF ou rastro de sensor, classifique como "ATENÇÃO"
                    6. ESTRUTURA: Inicie com 'PERGUNTA: "{pergunta_efetiva}"' seguido de 'CLASSIFICAÇÃO: [TIPO]'
                    
                    🎯 NOSSOS 7 PILARES:
                    - Análise Documental (metadados e fontes)
                    - Detecção de IA (12 marcadores anatômicos)
                    - e-Discovery (.eml e .pst)
                    - Engenharia Social (phishing/spoofing)
                    - Física da Luz (reflexos e sombras)
                    - Ponzi Detection (promessas inconsistentes)
                    - Consistência Digital (rastro vs conteúdo)
                    """
                    
                    contexto = [instrucao]
                    
                    # Adicionar histórico
                    for h in st.session_state.historico_pericial:
                        contexto.append(h)
                    
                    # Processar arquivos acumulados
                    for f in st.session_state.arquivos_acumulados:
                        if f['name'].endswith('.eml'):
                            msg = email.message_from_bytes(f['content'], policy=policy.default)
                            corpo = msg.get_body(preferencelist=('plain')).get_content()
                            contexto.append(f"E-MAIL {f['name']}: {corpo}")
                        elif f['type'] == "application/pdf":
                            contexto.append({"mime_type": "application/pdf", "data": f['content']})
                        else:
                            contexto.append(Image.open(io.BytesIO(f['content'])).convert('RGB'))
                    
                    # Adicionar pergunta do usuário
                    contexto.append(pergunta_efetiva if pergunta_efetiva else "Analise todas as provas acima.")
                    
                    # Gerar resposta
                    response = model.generate_content(contexto, request_options={"timeout": 600})
                    st.session_state.historico_pericial.append(response.text)
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

# 11. DOWNLOAD DE LAUDO PDF
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

# 12. GUIA MESTRE AUDITIA
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
        
        **Q: Qual o tamanho máximo dos arquivos?**
        R: Até 200MB individuais, totalizando 1GB por sessão pericial.
        
        **Q: O sistema guarda meu histórico?**
        R: Não. Ao clicar em 'Limpar Caso', toda a memória é destruída permanentemente.
        """)

st.caption(f"AuditIA © {datetime.now().year} - Tecnologia e Segurança Digital")
