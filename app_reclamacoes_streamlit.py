import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📊 Análise de Reclamações por Unidade")

# 📁 Carregar os dados da planilha
@st.cache_data
def carregar_dados():
    excel = pd.ExcelFile("Reclamacoes_2025_Traduzido.xlsx")
    df = pd.concat([excel.parse(mes).assign(Mês=mes) for mes in excel.sheet_names], ignore_index=True)

    # Padronizar colunas
    df.columns = df.columns.str.strip()

    # Verificar e converter datas se coluna existir
    if "Review date" in df.columns:
        df["Review date"] = pd.to_datetime(df["Review date"], errors='coerce')

    if "Negative review (PT)" in df.columns:
        df["Negative review (PT)"] = df["Negative review (PT)"].fillna("").astype(str).str.lower()

    return df

df_all = carregar_dados()

# 📌 Dicionário de temas atualizado
temas_keywords = {
    "Limpeza": ["sujo","usado","não estava pronto","cheirava a cigarros","higiene ","sala estava super suja ", "empoeirada", "sem papel", "sujeira", "limpo", "limpeza", "poeira", "imundo", "lençóis", "toalhas", "cheiro ruim", "odor", "quarto sujo", "cheiro nojento"],
    "Acesso/Check-in": ["porta","passei a noite lá não", "check-in estava uma bagunça", "não acessei o lugar", "chaves", "não conseguimos entrar.", "trancado", "não consegui entrar", "código não funcionou", "problema no acesso", "sem chave", "problema com o código", "acesso difícil", "demora no check-in"],
    "Itens faltando": ["sem papel higiênico","sem cabides no guarda -roupa", "não tem um shampoo", " nem um sabão", "exceto garfos", "faltando", "não tinha", "sem toalha", "sem sabonete", "sem cobertor", "sem travesseiro", "sem utensílios", "sem itens básicos", "poucos pratos", "faltavam copos"],
    "Atendimento": ["atendimento ruim", "comunicam corretamente","a falta de comunicação", "equipe do serviço","não respondam às mensagens", "não respondeu", "sem resposta", "demoraram para ajudar", "ninguém apareceu", "pessoal inútil", "equipe despreparada", "falta de suporte", "comunicação ruim", "resposta demorada", "não profissional"],
    "Manutenção/Estrutura": ["remoto","a luz no banheiro não funcionava","aquecimento","aquecedor", "incêndio", "tínhamos água", "água quente", "chuveiro quebrado", "chuveiro", "caixa elétrica", "alarme", "vazamento", "lâmpada queimada", "teto rachado", "paredes descascando", "radiador", "aquecimento não funcionou", "equipamento com defeito", "sem luz", "tomada não funciona", "problema estrutural", "estragado", "mofo", "infiltração"],
    "Conforto": ["colchão ruim","muito finos", "frio", "cama desconfortável", "muito frio", "muito calor", "barulhento", "sem isolamento", "muito pequeno", "sem ventilação", "ambiente gelado", "não tinha aquecedor"],
    "Internet": ["sem wi-fi", "internet ruim","wifi", "wi-fi", "internet", "wi-fi não funcionou", "sem sinal", "conexão fraca", "internet lenta", "wi-fi caindo"],
    "Barulho": ["barulho", "ruído", "som alto", "vizinho barulhento", "festa", "gritaria", "incomodado com o barulho"],
    "Anúncio incorreto": ["não era como nas fotos", "leva uma hora ", "anúncio enganoso", "fotos diferentes", "expectativa diferente", "propaganda enganosa", "não era o que esperava"],
    "Avaliação genérica": ["péssima experiência", "horrível", "não recomendo", "decepção", "terrível", "pior estadia", "nada"]
}

def identificar_tema(texto):
    encontrados = [tema for tema, palavras in temas_keywords.items() if any(p in texto for p in palavras)]
    return ", ".join(encontrados) if encontrados else "Outro"

df_all["Tema identificado"] = df_all["Negative review (PT)"].apply(identificar_tema)

# Filtros
meses = sorted(df_all["Mês"].unique())
meses_selecionados = st.multiselect("Selecionar mês(es)", meses, default=meses)

unidades = sorted(df_all[df_all["Mês"].isin(meses_selecionados)]["Unit"].unique())
unidades_selecionadas = st.multiselect("Selecionar unidade(s)", unidades)

temas_disponiveis = sorted(df_all["Tema identificado"].unique())
temas_escolhidos = st.multiselect("Selecionar tema(s)", temas_disponiveis)

# Aplicar filtros
df_filtrado = df_all[df_all["Mês"].isin(meses_selecionados)]

if unidades_selecionadas:
    df_filtrado = df_filtrado[df_filtrado["Unit"].isin(unidades_selecionadas)]

if temas_escolhidos:
    df_filtrado = df_filtrado[df_filtrado["Tema identificado"].apply(lambda t: any(tema in t for tema in temas_escolhidos))]

# Remover comentários vazios e notas 8, 9, 10
df_filtrado = df_filtrado[df_filtrado["Negative review (PT)"].str.strip() != ""]
df_filtrado = df_filtrado[~df_filtrado["Review score"].isin([8, 9, 10])]

# Exibir resultado
st.subheader("📋 Reclamações detalhadas")

if "Review date" in df_filtrado.columns:
    df_filtrado = df_filtrado.sort_values("Review date")

st.dataframe(
    df_filtrado[["Mês", "Unit", "Tema identificado", "Negative review (PT)", "Review score"]],
    use_container_width=True
)
