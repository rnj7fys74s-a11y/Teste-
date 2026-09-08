# ==========================================
# TELA 3: PAINEL DE CONTROLE (ATUALIZADO COM FILTROS)
# ==========================================
elif menu == "📊 Painel de Controle":
    st.header("📊 Ambiente de Controle, Saldos e Auditoria")
    st.markdown("---")
    
    # ---------------------------------------------------------
    # SEÇÃO 1: ESTOQUE E SALDOS
    # ---------------------------------------------------------
    st.subheader("📦 Consulta de Inventário (Saldos Atuais)")
    
    # Filtro independente para o Estoque
    busca_produto = st.text_input("🔍 Pesquisar Produto (Digite o Código de Barras ou Nome do Item):")
    
    # Cria uma cópia para aplicar os filtros sem estragar o banco
    df_estoque_filtrado = st.session_state.cadastro_produtos.copy()
    
    if busca_produto:
        df_estoque_filtrado = df_estoque_filtrado[
            (df_estoque_filtrado['CodigoBarras'].astype(str).str.contains(busca_produto, case=False)) |
            (df_estoque_filtrado['Nome'].str.contains(busca_produto, case=False))
        ]
    
    # Função para destacar em vermelho os produtos abaixo do estoque mínimo
    def destacar_criticos(row):
        return ['background-color: #ffcccc' if row['SaldoAtual'] <= row['EstoqueMinimo'] else '' for _ in row]
        
    if df_estoque_filtrado.empty:
        st.info("Nenhum produto encontrado com esse termo de pesquisa.")
    else:
        df_estilizado = df_estoque_filtrado.style.apply(destacar_criticos, axis=1)
        st.dataframe(df_estilizado, use_container_width=True)
        
    st.markdown("---")
    
    # ---------------------------------------------------------
    # SEÇÃO 2: HISTÓRICO E AUDITORIA
    # ---------------------------------------------------------
    st.subheader("🕵️‍♂️ Auditoria Geral de Movimentações")
    st.caption("Filtre o histórico por tipo de operação ou documentos específicos.")
    
    # Filtros independentes lado a lado para a Auditoria
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        filtro_tipo = st.selectbox("Filtrar por Operação:", ["Todos", "Apenas Entradas", "Apenas Saídas"])
        
    with col_f2:
        busca_doc = st.text_input("📄 Pesquisar por Documento (Nº Nota ou Nº Requisição):")
        
    # Cria uma cópia do histórico para aplicar as regras
    df_mov_filtrado = st.session_state.movimentacao_estoque.copy()
    
    # Aplica Filtro 1: Tipo de Movimentação
    if filtro_tipo == "Apenas Entradas":
        df_mov_filtrado = df_mov_filtrado[df_mov_filtrado['Tipo'] == "Entrada"]
    elif filtro_tipo == "Apenas Saídas":
        df_mov_filtrado = df_mov_filtrado[df_mov_filtrado['Tipo'] == "Saida"]
        
    # Aplica Filtro 2: Busca por Documento (Nota/Requisição)
    if busca_doc:
        df_mov_filtrado = df_mov_filtrado[
            df_mov_filtrado['NumeroNota'].astype(str).str.contains(busca_doc, case=False)
        ]
        
    # Exibe o resultado da auditoria filtrada
    if df_mov_filtrado.empty:
        st.info("Nenhuma movimentação localizada com os filtros selecionados.")
    else:
        st.dataframe(df_mov_filtrado, use_container_width=True)
