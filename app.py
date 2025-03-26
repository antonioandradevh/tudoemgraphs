import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from io import StringIO
import PyPDF2

# Configuração do app
st.set_page_config(layout="wide", page_title="📊 TudoemGraphs")

st.title("📊 TudoemGraphs")

# Upload de dados
uploaded_file = st.file_uploader("Carregue sua planilha, PDF ou arquivo de texto (CSV, Excel, TXT, PDF)", type=["csv", "xlsx", "txt", "pdf"])

def load_data(file):
    """Carrega o arquivo e retorna um DataFrame ou texto"""
    if file.name.endswith('.csv'):
        return pd.read_csv(file)
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file)
    elif file.name.endswith('.txt'):
        return file.read().decode("utf-8")
    elif file.name.endswith('.pdf'):
        pdf_reader = PyPDF2.PdfReader(file)
        text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        return text

def convert_to_text(data):
    """Converte os dados para formato textual com limite de 1000 caracteres"""
    if isinstance(data, pd.DataFrame):
        text = f"""
        **Estrutura dos dados:**
        - Total de registros: {len(data)}
        - Total de colunas: {len(data.columns)}
        - Colunas disponíveis: {', '.join(data.columns)}
        
        **Amostra dos dados:**
        {data.head(3).to_markdown(index=False)}
        """
        return text[:1000]
    else:
        return data[:1000]

def generate_visualizations(df):
    """Gera visualizações padrão para os dados carregados"""
    figures = []
    
    for col in df.select_dtypes(include=['number']).columns:
        figures.append(px.histogram(df, x=col, title=f"Distribuição de {col}"))
    
    numeric_cols = df.select_dtypes(include=['number']).columns
    if len(numeric_cols) >= 2:
        figures.append(px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], title=f"Relação entre {numeric_cols[0]} e {numeric_cols[1]}"))
    
    categorical_cols = df.select_dtypes(exclude=['number']).columns
    if len(categorical_cols) > 0 and len(numeric_cols) > 0:
        figures.append(px.bar(df, x=categorical_cols[0], y=numeric_cols[0], title=f"{categorical_cols[0]} vs {numeric_cols[0]}"))
    
    return figures

if uploaded_file:
    data = load_data(uploaded_file)
    data_text = convert_to_text(data)
    
    # Mostrar prévia com a planilha completa se for DataFrame
    st.header("📋 Prévia Completa dos Dados")
    if isinstance(data, pd.DataFrame):
        st.dataframe(data.style.set_sticky(), use_container_width=True)
    else:
        st.text_area("Conteúdo do Arquivo", data, height=300)
    
    # Análise completa
    st.header("🔍 Análise Completa")
    
    if st.button("Executar Análise Completa"):
        with st.spinner("Analisando dados com IA..."):
            try:
                prompt = f"""
                Analise este conjunto de dados e responda em formato markdown:
                
                1. **Principais insights** (3 a 5 pontos)
                2. **Padrões relevantes**
                3. **Possíveis problemas/valores atípicos**
                4. **Sugestões de visualização** (especifique tipos de gráficos e colunas a serem usadas)
                
                {data_text}
                """
                
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "phi3",
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.5}
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    analysis = result.get("response", "Erro ao interpretar a resposta da IA.")
                    
                    # Exibir análise formatada corretamente
                    st.markdown(f"""### 📊 Resultado da Análise
                    
                    {analysis}
                    """)
                    
                    # Gerar visualizações obrigatórias se for DataFrame
                    if isinstance(data, pd.DataFrame):
                        st.header("📈 Visualizações Automáticas")
                        figures = generate_visualizations(data)
                        
                        for fig in figures:
                            st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.error("Erro na conexão com a IA")
            
            except Exception as e:
                st.error(f"Erro na análise: {str(e)}")

# Instruções
st.markdown("---")
st.caption("""
**Instruções de Uso:**
1. Carregue uma planilha (CSV, Excel, PDF) ou um arquivo de texto (TXT)
2. Use nomes de colunas simples sem caracteres especiais
3. Mantenha o servidor Ollama rodando
4. Para dados complexos, use modelos maiores como 'llama3'
""")