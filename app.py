import streamlit as st
import pandas as pd
from datetime import datetime

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
        {"Tipo": "Entrada", "CodigoBarras": "7891000101", "Quantidade": 50, "ValorUnitario": 2.50, "NumeroNota": "123", "QuemRetirou": "-", "AutorizadoPor": "-", "OperadorAlmoxarifado": "sistema@empresa.com", "Data": "2026-03-01 10:00:00"},
        {"Tipo": "Entrada", "CodigoBarras": "7891000102", "Quantidade": 15, "ValorUnitario": 45.00, "NumeroNota": "124", "QuemRetirou": "-", "AutorizadoPor": "-", "OperadorAlmoxarifado": "sistema@empresa.com", "Data": "2026-03-02 11:30:00"},
        {"Tipo": "Entrada", "CodigoBarras": "7891000103", "Quantidade": 5, "ValorUnitario": 12.90, "NumeroNota": "125", "QuemRetirou": "-", "AutorizadoPor": "-", "OperadorAlmoxarifado": "sistema@empresa.com", "Data": "2026-03-03 14:15:00"}
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
    
    col_item1, col_item2, col_item3 = st.columns(3)
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
                    "ValorUnitario": item["ValorUnitario"], "NumeroNota": txt_nota, "QuemRetirou": "-", 
                    "AutorizadoPor": "-", "OperadorAlmoxarifado": "usuario_logado@empresa.com", "Data": item["Data"]
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
                        "OperadorAlmoxarifado": "operador_almoxarifado@empresa.com",
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
# TELA 3: PAINEL DE CONTROLE (SEM FUNÇÕES EXTERNAS)
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
