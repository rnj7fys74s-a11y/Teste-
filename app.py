import streamlit as st
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Configuração da página do aplicativo
st.set_page_config(page_title="Controle de Estoque Inteligente", layout="wide", page_icon="📦")

# 1. SIMULAÇÃO DO BANCO DE DADOS (Utiliza a memória da sessão do navegador)
if "cadastro_produtos" not in st.session_state:
    st.session_state.cadastro_produtos = pd.DataFrame([
        {"CodigoBarras": "7891000101", "Nome": "Parafuso Sextavado M8", "SaldoAtual": 50, "EstoqueMinimo": 20},
        {"CodigoBarras": "7891000102", "Nome": "Graxa Industrial Azul", "SaldoAtual": 15, "EstoqueMinimo": 10},
        {"CodigoBarras": "7891000103", "Nome": "Fita Isolante 20m", "SaldoAtual": 5, "EstoqueMinimo": 15}
    ])

if "historico_notas" not in st.session_state:
    st.session_state.historico_notas = pd.DataFrame(columns=["NumeroNota", "Fornecedor", "NumeroRequisicao", "DataRegistro"])

if "movimentacao_estoque" not in st.session_state:
    st.session_state.movimentacao_estoque = pd.DataFrame([
        {"Tipo": "Entrada", "CodigoBarras": "7891000101", "Quantidade": 50, "ValorUnitario": 2.50, "NumeroNota": "123", "QuemRetirou": "-", "AutorizadoPor": "-", "Data": "2026-03-01 10:00:00"},
        {"Tipo": "Entrada", "CodigoBarras": "7891000102", "Quantidade": 15, "ValorUnitario": 45.00, "NumeroNota": "124", "QuemRetirou": "-", "AutorizadoPor": "-", "Data": "2026-03-02 11:30:00"},
        {"Tipo": "Saida", "CodigoBarras": "7891000101", "Quantidade": 5, "ValorUnitario": 2.50, "NumeroNota": "REQ-001", "QuemRetirou": "Carlos Silva", "AutorizadoPor": "Gerente Carlos", "Data": "2026-03-02 14:00:00"},
        {"Tipo": "Saida", "CodigoBarras": "7891000103", "Quantidade": 2, "ValorUnitario": 12.90, "NumeroNota": "REQ-002", "QuemRetirou": "Ana Souza", "AutorizadoPor": "Supervisor Marcos", "Data": "2026-03-03 09:15:00"},
        {"Tipo": "Saida", "CodigoBarras": "7891000101", "Quantidade": 10, "ValorUnitario": 2.50, "NumeroNota": "REQ-003", "QuemRetirou": "Carlos Silva", "AutorizadoPor": "Gerente Carlos", "Data": "2026-03-03 16:45:00"}
    ])

if "col_temporaria_entrada" not in st.session_state:
    st.session_state.col_temporaria_entrada = []

# Título Principal do Sistema
st.title("📦 Sistema Ativo de Almoxarifado")
st.markdown("---")

# MENU DE NAVEGAÇÃO LATERAL
menu = st.sidebar.radio("Selecione a Tela:", ["📥 Entrada por NF-e", "📤 Requisição de Saída", "📊 Painel de Controle"])

# ==========================================
# TELA 1: ENTRADA POR NF-E
# ==========================================
if menu == "📥 Entrada por NF-e":
    st.header("Lançamento Manual de Notas Fiscais")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        txt_nota = st.text_input("Número da NF-e")
    with col2:
        txt_fornecedor = st.text_input("Fornecedor")
    with col3:
        txt_requisicao_compra = st.text_input("Número da Requisição de Compra")
        
    st.markdown("### Adicionar Itens à Nota (Use o Coletor no campo de Código)")
    
    col_item1, col_item2, col_item3 = st.columns([2, 1, 1])
    with col_item1:
        txt_codigo_barras = st.text_input("Código de Barras do Produto", key="input_codigo_entrada")
    with col_item2:
        txt_qtd = st.number_input("Quantidade", min_value=1, step=1, key="input_qtd_entrada")
    with col_item3:
        txt_preco = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01, format="%.2f")

    if st.button("➕ Adicionar Item à Lista"):
        if txt_codigo_barras and txt_nota:
            st.session_state.col_temporaria_entrada.append({
                "CodigoBarras": txt_codigo_barras,
                "Quantidade": txt_qtd,
                "ValorUnitario": txt_preco,
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.toast("Item adicionado à lista temporária!", icon="✅")
        else:
            st.error("Por favor, preencha o número da nota e o código de barras.")

    if st.session_state.col_temporaria_entrada:
        st.markdown("#### Itens Prontos para Entrada")
        df_temp = pd.DataFrame(st.session_state.col_temporaria_entrada)
        st.dataframe(df_temp, use_container_width=True)
        
        if st.button("💾 CONFIRMAR ENTRADA NO ESTOQUE"):
            nova_nota = {"NumeroNota": txt_nota, "Fornecedor": txt_fornecedor, "NumeroRequisicao": txt_requisicao_compra, "DataRegistro": datetime.now().strftime("%Y-%m-%d")}
            st.session_state.historico_notas = pd.concat([st.session_state.historico_notas, pd.DataFrame([nova_nota])], ignore_index=True)
            
            for item in st.session_state.col_temporaria_entrada:
                mov = {
                    "Tipo": "Entrada", "CodigoBarras": item["CodigoBarras"], "Quantidade": item["Quantidade"], 
                    "ValorUnitario": item["ValorUnitario"], "NumeroNota": txt_nota, 
                    "QuemRetirou": "-", "AutorizadoPor": "-", "Data": item["Data"]
                }
                st.session_state.movimentacao_estoque = pd.concat([st.session_state.movimentacao_estoque, pd.DataFrame([mov])], ignore_index=True)
                
                idx = st.session_state.cadastro_produtos[st.session_state.cadastro_produtos['CodigoBarras'] == item["CodigoBarras"]].index
                if not idx.empty:
                    st.session_state.cadastro_produtos.loc[idx, 'SaldoAtual'] += item["Quantidade"]
                else:
                    novo_prod = {"CodigoBarras": item["CodigoBarras"], "Nome": f"Produto Novo ({item['CodigoBarras']})", "SaldoAtual": item["Quantidade"], "EstoqueMinimo": 5}
                    st.session_state.cadastro_produtos = pd.concat([st.session_state.cadastro_produtos, pd.DataFrame([novo_prod])], ignore_index=True)
            
            st.session_state.col_temporaria_entrada = []
            st.success("Nota Fiscal processada e estoque atualizado com sucesso!")

# ==========================================
# TELA 2: REQUISIÇÃO DE SAÍDA
# ==========================================
elif menu == "📤 Requisição de Saída":
    st.header("Lançamento de Requisições de Saída")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        txt_req_saida = st.text_input("Número da Requisição de Saída")
    with col_s2:
        txt_quem_retirou = st.text_input("Funcionário que Retirou")
    with col_s3:
        cmb_autorizado = st.selectbox("Autorizado por:", ["Selecione...", "Gerente Carlos", "Supervisor Marcos", "Diretora Ana"])

    st.markdown("---")
    txt_codigo_saida = st.text_input("Bipe o Código de Barras do Produto", key="input_codigo_saida")
    
    if txt_codigo_saida:
        prod_filtrado = st.session_state.cadastro_produtos[st.session_state.cadastro_produtos['CodigoBarras'] == txt_codigo_saida]
        
        if not prod_filtrado.empty:
            nome_prod = prod_filtrado.iloc[0]['Nome']
            saldo_prod = prod_filtrado.iloc[0]['SaldoAtual']
            
            historico_entradas = st.session_state.movimentacao_estoque[
                (st.session_state.movimentacao_estoque['CodigoBarras'] == txt_codigo_saida) & 
                (st.session_state.movimentacao_estoque['Tipo'] == "Entrada")
            ]
            ultimo_preco = historico_entradas.iloc[-1]['ValorUnitario'] if not historico_entradas.empty else 0.0
            
            st.info(f"📋 **Produto:** {nome_prod} | 📦 **Saldo Atual:** {saldo_prod} unidades | 💰 **Último Custo Pago:** R$ {ultimo_preco:.2f}")
            
            txt_qtd_saida = st.number_input("Quantidade para Retirada", min_value=1, step=1)
            
            if st.button("🔥 Confirmar Baixa de Saída"):
                if cmb_autorizado == "Selecione..." or not txt_req_saida or not txt_quem_retirou:
                    st.error("Preencha todas as identificações obrigatórias (Requisição, Quem Retirou e Autorizador).")
                elif txt_qtd_saida > saldo_prod:
                    st.error(f"Bloqueado: Saldo insuficiente! Você tentou retirar {txt_qtd_saida} mas só existem {saldo_prod} em estoque.")
                else:
                    idx = prod_filtrado.index
                    st.session_state.cadastro_produtos.loc[idx, 'SaldoAtual'] -= txt_qtd_saida
                    
                    nova_saida = {
                        "Tipo": "Saida", "CodigoBarras": txt_codigo_saida, "Quantidade": txt_qtd_saida, 
                        "ValorUnitario": ultimo_preco, "NumeroNota": f"REQ-{txt_req_saida}", 
                        "QuemRetirou": txt_quem_retirou, "AutorizadoPor": cmb_autorizado,
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state.movimentacao_estoque = pd.concat([st.session_state.movimentacao_estoque, pd.DataFrame([nova_saida])], ignore_index=True)
                    
                    st.success("Saída autorizada e registrada com sucesso!")
                    
                    novo_saldo = saldo_prod - txt_qtd_saida
                    if novo_saldo <= prod_filtrado.iloc[0]['EstoqueMinimo']:
                        st.warning(f"🚨 ATENÇÃO: O item '{nome_prod}' atingiu o estoque mínimo de segurança! Saldo restante: {novo_saldo}")
        else:
            st.error("Código de barras não localizado no cadastro do sistema.")

# ==========================================
# TELA 3: PAINEL DE CONTROLE (ATUALIZADO)
# ==========================================
elif menu == "📊 Painel de Controle":
    st.header("📊 Ambiente de Controle, Saldos e Auditoria")
    st.markdown("---")
    
    st.subheader("📦 Consulta de Inventário (Saldos Atuais)")
    busca_produto = st.text_input("🔍 Pesquisar Produto (Digite o Código de Barras ou Nome do Item):")
df_estoque_filtrado = st.session_state.cadastro_produtos.copy()
if busca_produto:
df_estoque_filtrado = df_estoque_filtrado[
(df_estoque_filtrado['CodigoBarras'].astype(str).str.contains(busca_produto, case=False)) |
(df_estoque_filtrado['Nome'].str.contains(busca_produto, case=False))
]
if df_estoque_filtrado.empty:
st.info("Nenhum produto encontrado com esse termo de pesquisa.")
else:
st.dataframe(df_estoque_filtrado, use_container_width=True)
st.markdown("---")
st.subheader("🕵️‍♂️ Auditoria Geral de Movimentações")
st.caption("Acompanhe entradas, saídas, responsáveis e valores consolidados consumidos.")
# Adicionando o campo Calculado "ValorTotal" no dataframe de exibição
df_mov = st.session_state.movimentacao_estoque.copy()
df_mov['ValorTotal'] = df_mov['Quantidade'] * df_mov['ValorUnitario']
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
filtro_tipo = st.selectbox("Filtrar por Operação:", ["Todos", "Apenas Entradas", "Apenas Saídas"])
with col_f2:
busca_doc = st.text_input("📄 Pesquisar por Documento (Nº Nota ou Nº Requisição):")
with col_f3:
# Cria dinamicamente a lista de pessoas que já retiraram algo para o filtro
lista_pessoas = ["Todos"] + sorted([p for p in df_mov['QuemRetirou'].unique() if p != "-"])
busca_pessoa = st.selectbox("👤 Filtrar por Funcionário (Consumo):", lista_pessoas)
# Aplicação sequencial dos filtros selecionados
if filtro_tipo == "Apenas Entradas":
df_mov = df_mov[df_mov['Tipo'] == "Entrada"]
elif filtro_tipo == "Apenas Saídas":
df_mov = df_mov[df_mov['Tipo'] == "Saida"]
if busca_doc:
df_mov = df_mov[df_mov['NumeroNota'].astype(str).str.contains(busca_doc, case=False)]
if busca_pessoa != "Todos":
df_mov = df_mov[df_mov['QuemRetirou'] == busca_pessoa]
# Exibe indicadores financeiros na tela caso haja registros correspondentes
if not df_mov.empty:
total_pecas = df_mov['Quantidade'].sum()
total_financeiro = df_mov['ValorTotal'].sum()
# Quadrinhos informativos sobre a seleção atual
c1, c2 = st.columns(2)
with c1:
st.metric(label="Volumetria Filtrada (Total Peças)", value=f"{total_pecas:,.0f} un")
with c2:
st.metric(label="Valor Financeiro Movimentado", value=f"R$ {total_financeiro:,.2f}")
# Reorganizando a ordem das colunas para melhor visualização na auditoria
ordem_colunas = ['Data', 'Tipo', 'NumeroNota', 'CodigoBarras', 'Quantidade', 'ValorUnitario', 'ValorTotal', 'QuemRetirou', 'AutorizadoPor']
st.dataframe(df_mov[ordem_colunas], use_container_width=True)
# ==========================================
# GERADOR DE RELATÓRIO EM PDF (REPORTLAB)
# ==========================================
st.markdown("### 🖨️ Exportação")
def gerar_pdf(dataframe):
buffer = io.BytesIO()
doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
elements = []
# Estilos de fontes e textos
styles = getSampleStyleSheet()
title_style = ParagraphStyle(
'ReportTitle',
parent=styles['Heading1'],
fontSize=18,
leading=22,
textColor=colors.HexColor("#1A365D"),
alignment=1, # Centralizado
spaceAfter=15
)
meta_style = ParagraphStyle(
'ReportMeta',
parent=styles['Normal'],
fontSize=10,
leading=14,
textColor=colors.HexColor("#4A5568"),
spaceAfter=20
)
# Elementos do cabeçalho
elements.append(Paragraph("RELATÓRIO DE AUDITORIA DE ALMOXARIFADO", title_style))
data_impressao = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
meta_texto = f"Data de Emissão: {data_impressao}"
meta_texto += f"Filtro de Operação: {filtro_tipo}"
meta_texto += f"Filtro de Funcionário: {busca_pessoa}"
elements.append(Paragraph(meta_texto, meta_style))
# Preparação da tabela estruturada em string para o PDF
dados_tabela = [["Data", "Tipo", "Doc/Req", "Código", "Qtd", "Unit (R$)", "Total (R$)", "Retirado Por"]]
for _, row in dataframe.iterrows():
dados_tabela.append([
str(row['Data'])[:10],
str(row['Tipo']),
str(row['NumeroNota']),
str(row['CodigoBarras']),
str(row['Quantidade']),
f"{row['ValorUnitario']:.2f}",
f"{row['ValorTotal']:.2f}",
str(row['QuemRetirou'])
])
# Adiciona linha de rodapé com somatórios acumulados
dados_tabela.append(["TOTAL", "", "", "", f"{total_pecas:.0f}", "", f"{total_financeiro:.2f}", ""])
# Configuração visual e limites da tabela
t = Table(dados_tabela, colWidths=[65, 45, 60, 65, 35, 55, 60, 165])
t.setStyle(TableStyle([
('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
('ALIGN', (0,0), (-1,-1), 'CENTER'),
('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
('FONTSIZE', (0,0), (-1,0), 9),
('BOTTOMPADDING', (0,0), (-1,0), 6),
('BACKGROUND', (0,1), (-1,-2), colors.HexColor("#F7FAFC")),
('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#EDF2F7")),
('FONTSIZE', (0,1), (-1,-1), 8),
]))
elements.append(t)
doc.build(elements)
buffer.seek(0)
return buffer.getvalue()
pdf_data = gerar_pdf(df_mov)
# Botão oficial de download nativo do Streamlit
st.download_button(
label="📄 Baixar Relatório Filtrado em PDF",
data=pdf_data,
file_name=f"auditoria_estoque_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
mime="application/pdf"
)
else:
st.info("Nenhuma movimentação localizada com os filtros selecionados.")

