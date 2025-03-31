import os
import streamlit as st
import pandas as pd
import json

st.set_page_config(layout="wide")
st.title("📊 Análise de Reclamações por Unidade")

# 📁 Carregar os dados da planilha (suporta 1 ou 2 arquivos para localizações diferentes)
@st.cache_data
def carregar_dados():
    if os.path.exists("Reclamacoes_2025_Traduzido_Portugal.xlsx") and os.path.exists("Reclamacoes_2025_Traduzido_Londres.xlsx"):
        # Carregar dados de Portugal
        excel_pt = pd.ExcelFile("Reclamacoes_2025_Traduzido_Portugal.xlsx")
        df_pt = pd.concat([excel_pt.parse(mes).assign(Mês=mes) for mes in excel_pt.sheet_names], ignore_index=True)
        df_pt["Localização"] = "Portugal"
        # Carregar dados de Londres
        excel_ld = pd.ExcelFile("Reclamacoes_2025_Traduzido_Londres.xlsx")
        df_ld = pd.concat([excel_ld.parse(mes).assign(Mês=mes) for mes in excel_ld.sheet_names], ignore_index=True)
        df_ld["Localização"] = "Londres"
        df = pd.concat([df_pt, df_ld], ignore_index=True)
    else:
        excel = pd.ExcelFile("Reclamacoes_2025_Traduzido.xlsx")
        df = pd.concat([excel.parse(mes).assign(Mês=mes) for mes in excel.sheet_names], ignore_index=True)
        df["Localização"] = "N/A"
    df["Review date"] = pd.to_datetime(df["Review date"], errors='coerce')
    df["Negative review (PT)"] = df["Negative review (PT)"].fillna("").astype(str).str.lower()
    return df

df_all = carregar_dados()

# 📌 Dicionário de temas atualizado
temas_keywords = {
    "Limpeza": ["sujo", "empoeirada", "sem papel", "sujeira", "limpo", "limpeza", "poeira", "imundo", "lençóis", "toalhas", "cheiro ruim", "odor", "quarto sujo", "cheiro nojento"],
    "Acesso/Check-in": ["porta", "check-in estava uma bagunça", "não acessei o lugar", "chaves", "não conseguimos entrar.", "trancado", "não consegui entrar", "código não funcionou", "problema no acesso", "sem chave", "problema com o código", "acesso difícil", "demora no check-in"],
    "Itens faltando": ["sem papel higiênico", "exceto garfos", "faltando", "não tinha", "sem toalha", "sem sabonete", "sem cobertor", "sem travesseiro", "sem utensílios", "sem itens básicos", "poucos pratos", "faltavam copos"],
    "Atendimento": ["atendimento ruim", "não respondam às mensagens", "não respondeu", "sem resposta", "demoraram para ajudar", "ninguém apareceu", "pessoal inútil", "equipe despreparada", "falta de suporte", "comunicação ruim", "resposta demorada", "não profissional"],
    "Manutenção/Estrutura": ["remoto", "aquecedor", "incêndio", "tínhamos água", "água quente", "chuveiro quebrado", "chuveiro", "caixa elétrica", "alarme", "vazamento", "lâmpada queimada", "teto rachado", "paredes descascando", "radiador", "aquecimento não funcionou", "equipamento com defeito", "sem luz", "tomada não funciona", "problema estrutural", "estragado", "mofo", "infiltração"],
    "Conforto": ["colchão ruim", "frio", "cama desconfortável", "muito frio", "muito calor", "barulhento", "sem isolamento", "muito pequeno", "sem ventilação", "ambiente gelado", "não tinha aquecedor"],
    "Internet": ["sem wi-fi", "internet ruim", "internet", "wi-fi não funcionou", "sem sinal", "conexão fraca", "internet lenta", "wi-fi caindo"],
    "Barulho": ["barulho", "ruído", "som alto", "vizinho barulhento", "festa", "gritaria", "incomodado com o barulho"],
    "Anúncio incorreto": ["não era como nas fotos", "leva uma hora ", "anúncio enganoso", "fotos diferentes", "expectativa diferente", "propaganda enganosa", "não era o que esperava"],
    "Avaliação genérica": ["péssima experiência", "horrível", "não recomendo", "decepção", "terrível", "pior estadia", "nada"]
}

def identificar_tema(texto):
    encontrados = [tema for tema, palavras in temas_keywords.items() if any(p in texto for p in palavras)]
    return ", ".join(encontrados) if encontrados else "Outro"

df_all["Tema identificado"] = df_all["Negative review (PT)"].apply(identificar_tema)

# 🔍 Filtros Gerais
meses = sorted(df_all["Mês"].unique())
meses_selecionados = st.multiselect("Selecionar mês(es)", meses, default=meses)

# Filtro por localização, se aplicável
if "Localização" in df_all.columns and df_all["Localização"].nunique() > 1:
    localizacoes = sorted(df_all["Localização"].unique())
    localizacao_selecionada = st.selectbox("Selecionar localização", ["Todas"] + localizacoes)
    if localizacao_selecionada != "Todas":
        df_all = df_all[df_all["Localização"] == localizacao_selecionada]

# Filtro por Unidade (opcional)
unidades = sorted(df_all[df_all["Mês"].isin(meses_selecionados)]["Unit"].unique())
unidades_selecionadas = st.multiselect("Selecionar unidade(s)", unidades)
if unidades_selecionadas:
    df_filtrado = df_all[(df_all["Mês"].isin(meses_selecionados)) & (df_all["Unit"].isin(unidades_selecionadas))]
else:
    df_filtrado = df_all[df_all["Mês"].isin(meses_selecionados)]

# Remover registros com comentários em branco
df_filtrado = df_filtrado[df_filtrado["Negative review (PT)"].str.strip() != ""]

st.subheader("📋 Reclamações detalhadas")
st.dataframe(df_filtrado[["Review date", "Unit", "Localização", "Tema identificado", "Negative review (PT)", "Review score"]].sort_values("Review date"), use_container_width=True)

# 📘 SUGESTÕES PADRÃO
with open("sugestoes_padrao_final.json", "r", encoding="utf-8") as f:
    sugestoes_padrao = json.load(f)

# 📄 RELATÓRIO AUTOMÁTICO
st.markdown("---")
st.header("📄 Relatório automático da unidade/total")

if st.button("Gerar relatório"):
    # Filtrar registros para o relatório: desconsiderar notas 8, 9 ou 10 e comentários vazios
    df_relatorio = df_filtrado[~df_filtrado["Review score"].isin([8, 9, 10])]
    df_relatorio = df_relatorio[df_relatorio["Negative review (PT)"].str.strip() != ""]
    
    temas_splitados = df_relatorio["Tema identificado"].str.split(", ")
    temas_explodido = df_relatorio.loc[temas_splitados.index.repeat(temas_splitados.str.len())].copy()
    temas_explodido["Tema"] = [t for sub in temas_splitados for t in sub]
    contagem_temas = temas_explodido["Tema"].value_counts()

    top_3 = contagem_temas.head(3)
    restantes = contagem_temas[3:]

    exemplos_por_tema = {}
    for tema in contagem_temas.index:
        frases = df_relatorio[df_relatorio["Tema identificado"].str.contains(tema, na=False)]["Negative review (PT)"].dropna().unique().tolist()[:2]
        exemplos_por_tema[tema] = frases

    # Gerando o relatório em Markdown com formatação organizada
    relatorio = f"# Relatório da Unidade/Total\n\n"
    if "Localização" in df_relatorio.columns and df_relatorio["Localização"].nunique() == 1:
        relatorio += f"**Localização:** {df_relatorio['Localização'].iloc[0]}\n\n"
    relatorio += f"**Período:** {', '.join(meses_selecionados)}\n\n"
    
    relatorio += "## Top 3 Temas Mais Recorrentes\n"
    for tema, qtd in top_3.items():
        relatorio += f"- **{tema}**: {qtd} reclamações\n"
    
    if not restantes.empty:
        relatorio += "\n## Demais Temas Identificados\n"
        for tema, qtd in restantes.items():
            relatorio += f"- **{tema}**: {qtd} reclamações\n"

    relatorio += "\n## Exemplos de Reclamações\n"
    for tema, frases in exemplos_por_tema.items():
        if frases:
            relatorio += f"### {tema}\n"
            for frase in frases:
                relatorio += f"- {frase.strip()}\n"
    
    relatorio += "\n## Sugestões de Melhoria\n"
    for tema in contagem_temas.index:
        if tema in sugestoes_padrao:
            relatorio += f"### {tema}\n"
            relatorio += f"{sugestoes_padrao[tema]}\n\n"

    st.markdown(relatorio)
    st.download_button("📥 Baixar relatório como .md", relatorio, file_name="relatorio.md")
