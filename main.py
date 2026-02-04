import streamlit as st
import google.generativeai as genai
from PIL import Image
from fpdf import FPDF
import io
from datetime import datetime, timedelta

# 1. Configuração de Página e Estilo (Branco e Cinza Pericial)
st.set_page_config(page_title="AuditIA", page_icon="👁️", layout="centered")

def aplicar_cor_veredito(texto):
    texto_upper = texto.upper()
    # Cores dinâmicas para o Semáforo de Risco
    if "FRAUDE CONFIRMADA" in texto_upper: cor = "#ff4b4b"      # Vermelho
    elif "POSSÍVEL FRAUDE" in texto_upper: cor = "#ffa500"     # Laranja
    elif "ATENÇÃO" in texto_upper: cor = "#f1c40f"             # Amarelo
    elif "SEGURO" in texto_upper: cor = "#2ecc71"              # Verde
    else: cor = "#3498db"                                      # Azul (Neutro)
    
    return f'<div style="background-color: {cor}; padding: 20px; border-radius: 10px; color: white; font-weight: bold; border: 1px solid #4a4a4a;">{texto}</div>'

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; color: #333333; }
    div.stButton > button:first-child { background-color: #4a4a4a; color: white; font-weight: bold; width: 100%; height: 3.5em; border-radius: 8px; }
    div.stButton > button:first-child:hover { background-color: #59ea63; color: black; }
    .stTextArea textarea { background-color: #f8f9fa; border: 1px solid #d1d5db; }
    </style>
    """, unsafe_allow_html=True)

# 2. Conexão Segura (Lógica de listagem para evitar erro 404)
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    modelos = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    model = genai.GenerativeModel(modelos[0])
except Exception as e:
    st.error("Erro de conexão com a API."); st.stop()

# 3. Cabeçalho (Logo Grande e à Esquerda)
try:
    logo = Image.open("Logo_AI_1.png")
    st.image(logo, width=450) # Tamanho aumentado conforme solicitado
except:
    st.title("👁️ AuditIA")

st.markdown("### Auditoria de Integridade Digital")

# 4. Interface (Imagem e PDF)
uploaded_file = st.file_uploader("📸 Envie evidências (Print ou PDF):", type=["jpg", "png", "jpeg", "pdf"])
if uploaded_file and uploaded_file.type != "application/pdf":
    st.image(uploaded_file, use_container_width=True)

user_input = st.text_area("📝 Descreva o caso ou cole o link:", placeholder="Ex: Analise este contrato/print...", height=120)

# Função PDF de Saída (Relatório)
def gerar_pdf_saida(texto, data_f):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio de Auditoria - AuditIA", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, txt=f"Data da Analise: {data_f}", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    # Limpeza para evitar erros de caractere no PDF
    texto_limpo = texto.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# 5. Execução
if st.button("🚀 INICIAR AUDITORIA INTELIGENTE"):
    if not user_input and not uploaded_file:
        st.warning("Forneça conteúdo.")
    else:
        # Horário de Brasília (UTC-3)
        data_br = (datetime.now() - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
        
        with st.spinner("Auditando..."):
            try:
                instrucao = f"Aja como o AuditIA perito em fraudes. Hoje é {data_br}. No início do veredito, classifique como: FRAUDE CONFIRMADA, POSSÍVEL FRAUDE, ATENÇÃO ou SEGURO."
                conteudo = [instrucao]
                if uploaded_file:
                    if uploaded_file.type == "application/pdf":
                        conteudo.append({"mime_type": "application/pdf", "data": uploaded_file.read()})
                    else:
                        conteudo.append(Image.open(uploaded_file).convert('RGB'))
                if user_input: conteudo.append(user_input)
                
                response = model.generate_content(conteudo)
                resultado = response.text
                
                st.subheader("📋 Relatório AuditIA")
                st.markdown(aplicar_cor_veredito(resultado), unsafe_allow_html=True)
                
                # Download PDF Automático após a análise
                pdf_bytes = gerar_pdf_saida(resultado, data_br)
                st.download_button(label="📥 Baixar Relatório em PDF", data=pdf_bytes, file_name=f"auditIA_{datetime.now().strftime('%d%m%Y')}.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Erro: {e}")

# 6. Manual Robustecido de Utilização
st.markdown("---")
with st.expander("💡 MANUAL DE UTILIZAÇÃO - Como dominar o AuditIA"):
    st.markdown("""
    O **AuditIA** utiliza inteligência pericial para proteger sua integridade digital:
    
    * **Análise de Prints**: Envie capturas de tela do WhatsApp ou Instagram. O robô identifica padrões de manipulação psicológica e engenharia social.
    * **Leitura de PDFs**: Suba contratos ou boletos suspeitos. O AuditIA extrai dados e verifica inconsistências em CNPJs ou links de pagamento.
    * **Consciência Temporal**: O robô sabe a data e hora atual de Brasília, essencial para validar se um boleto está vencido ou se uma oferta é um golpe de "urgência falsa".
    * **Semáforo de Veredito**:
        * 🔴 **FRAUDE CONFIRMADA**: Risco imediato detectado.
        * 🟠 **POSSÍVEL FRAUDE**: Alto índice de suspeita.
        * 🟡 **ATENÇÃO**: Elementos duvidosos presentes.
        * 🟢 **SEGURO**: Padrões de integridade validados.
    """)

st.caption("AuditIA - Tecnologia e Segurança Digital | Vargem Grande do Sul - SP")
