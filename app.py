import streamlit as st
from database import criar_tabelas
from produtos import adicionar_produto, listar_produtos, atualizar_estoque, editar_produto, deletar_produto
from vendas import (
    registrar_venda, historico_vendas, faturamento_total,
    produtos_mais_vendidos, vendas_por_dia,
    grafico_produtos_mais_vendidos, grafico_vendas_por_dia, gerar_comprovante_pdf
)
import time

criar_tabelas()
st.title('Sistema de Vendas - Loja')
st.markdown("""
<style>
div.stButton > button {
    height: 80px;
    font-size: 17px;
    font-weight: 600;
    border-radius: 14px;
    border: 1px solid #e0e0e0;
}
div[data-testid="stMetric"] {
    background-color: #f8f9fb;
    border-radius: 14px;
    padding: 18px;
    border: 1px solid #eee;
}
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] div {
    color: #1a1a1a !important;
}
</style>
""", unsafe_allow_html=True)

st.write("")

col1, col2, col3, col4 = st.columns(4)

opcoes_menu = [
    (col1, "Produtos", "🛍️ Produtos"),
    (col2, "Nova venda", "💰 Nova venda"),
    (col3, "Histórico", "📋 Histórico"),
    (col4, "Dashboard", "📊 Dashboard"),
]

if "menu" not in st.session_state:
    st.session_state.menu = "Produtos"

for coluna, valor, rotulo in opcoes_menu:
    with coluna:
        tipo = "primary" if st.session_state.menu == valor else "secondary"
        if st.button(rotulo, key=valor, use_container_width=True, type=tipo):
            if st.session_state.menu != valor:
                st.session_state.menu = valor
                st.rerun()

menu = st.session_state.menu

if menu == 'Produtos':
    st.header('Produtos Cadastrados')
    produtos = listar_produtos()
    
    busca = st.text_input("Buscar produto", placeholder="Digite o nome do produto...")
    
    if busca:
        produtos = [p for p in produtos if busca.lower() in p[1].lower()]
    
    with st.expander("Cadastrar novo produto"):
        with st.form("form_cadastro_produto", clear_on_submit=True):
            nome = st.text_input("Nome")
            categoria = st.text_input("Categoria")
            tamanho = st.text_input("Tamanho")
            cor = st.text_input("Cor")
            preco = st.number_input("Preço", min_value=0.0, step=0.01)
            estoque = st.number_input("Estoque inicial", min_value=0, step=1)
            
            submetido = st.form_submit_button("Salvar produto")
            
            if submetido:
                if not nome.strip() or not categoria.strip() or not tamanho.strip() or not cor.strip():
                    st.error("Todos os campos de texto (Nome, Categoria, Tamanho e Cor) são obrigatórios!")
                elif preco <= 0:
                    st.error("O preço do produto deve ser maior que zero.")
                else:
                    adicionar_produto(nome.strip(), categoria.strip(), tamanho.strip(), cor.strip(), preco, estoque)
                    st.success(f"Produto '{nome}' cadastrado com sucesso!")
                    time.sleep(1.5)
                    st.rerun()
    
    if not produtos:
        st.info('Nenhum produto cadastrado ainda.')
    else:
        for produto in produtos:
            id, nome, categoria, tamanho, cor, preco, estoque, ativo = produto
            cor_estoque = "🟢" if estoque > 5 else "🟡" if estoque > 0 else "🔴"
            
            with st.expander(f"{nome} — R$ {preco:.2f} — {cor_estoque} {estoque} un."):
                st.write(f"**Categoria:** {categoria}  |  **Tamanho/Cor:** {tamanho}/{cor}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Editar", key=f"editar_{id}"):
                        st.session_state.editando_id = id
                with col_b:
                    if st.button("Excluir", key=f"excluir_{id}"):
                        st.session_state.confirmando_exclusao = id
                
                if st.session_state.get("confirmando_exclusao") == id:
                    st.warning(f"Excluir '{nome}'? Essa ação não pode ser desfeita.")
                    col_sim, col_nao = st.columns(2)
                    with col_sim:
                        if st.button("Sim, excluir", key=f"confirma_sim_{id}", type="primary"):
                            deletar_produto(id)
                            st.session_state.confirmando_exclusao = None
                            st.success(f"Produto '{nome}' removido.")
                            time.sleep(1)
                            st.rerun()
                    with col_nao:
                        if st.button("Cancelar", key=f"confirma_nao_{id}"):
                            st.session_state.confirmando_exclusao = None
                            st.rerun()
                
                if st.session_state.get("editando_id") == id:
                    with st.form(f"form_editar_{id}"):
                        novo_nome = st.text_input("Nome", value=nome)
                        nova_categoria = st.text_input("Categoria", value=categoria)
                        novo_tamanho = st.text_input("Tamanho", value=tamanho)
                        nova_cor = st.text_input("Cor", value=cor)
                        novo_preco = st.number_input("Preço", value=preco, min_value=0.0, step=0.01)
                        
                        col_salvar, col_cancelar = st.columns(2)
                        with col_salvar:
                            salvar = st.form_submit_button("Salvar alterações")
                        with col_cancelar:
                            cancelar = st.form_submit_button("Cancelar")
                        
                        if salvar:
                            editar_produto(id, novo_nome, nova_categoria, novo_tamanho, nova_cor, novo_preco)
                            st.session_state.editando_id = None
                            st.success("Produto atualizado!")
                            time.sleep(1)
                            st.rerun()
                        if cancelar:
                            st.session_state.editando_id = None
                            st.rerun()

if menu == "Nova venda":
    st.header("Registrar nova venda")
    
    if "itens_venda_atual" not in st.session_state:
        st.session_state.itens_venda_atual = []
    
    produtos = listar_produtos()
    
    if not produtos:
        st.info("Cadastre produtos antes de registrar uma venda.")
    else:
        opcoes = {f"{p[1]} ({p[3]}/{p[4]}) - Estoque: {p[6]}": {"id": p[0], "estoque": p[6]} for p in produtos}
        
        col1, col2 = st.columns([3, 1])
        with col1:
            escolha = st.selectbox("Produto", opcoes.keys())
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
        
        if st.button("Adicionar item"):
            produto_id = opcoes[escolha]["id"]
            estoque_disponivel = opcoes[escolha]["estoque"]
            
            qtd_ja_no_carrinho = sum(item["quantidade"] for item in st.session_state.itens_venda_atual if item["produto_id"] == produto_id)
            qtd_total_solicitada = qtd_ja_no_carrinho + quantidade
            
            if estoque_disponivel == 0:
                st.error("Este produto está esgotado!")
            elif qtd_total_solicitada > estoque_disponivel:
                if qtd_ja_no_carrinho > 0:
                    st.error(f"Estoque insuficiente! Você já adicionou {qtd_ja_no_carrinho}x ao carrinho e restam apenas {estoque_disponivel - qtd_ja_no_carrinho}x disponíveis no estoque.")
                else:
                    st.error(f"Estoque insuficiente! Você tentou adicionar {quantidade}x, mas restam apenas {estoque_disponivel}x em estoque.")
            else:
                st.session_state.itens_venda_atual.append({
                    "produto_id": produto_id,
                    "quantidade": quantidade,
                    "nome": escolha
                })
                st.rerun()
        
        if st.session_state.itens_venda_atual:
            st.subheader("Itens da venda")
            for item in st.session_state.itens_venda_atual:
                st.write(f"- {item['nome']} — {item['quantidade']}x")
            
            botoes_col1, botoes_col2 = st.columns([1, 1])
            
            with botoes_col1:
                if st.button("Finalizar venda", type="primary"):
                    sucesso = registrar_venda(st.session_state.itens_venda_atual)
                    if sucesso:
                        itens_completos = []
                        valor_total_venda = 0
                        for item in st.session_state.itens_venda_atual:
                            produto = [p for p in listar_produtos() if p[0] == item["produto_id"]][0]
                            preco = produto[5]
                            subtotal = preco * item["quantidade"]
                            valor_total_venda += subtotal
                            itens_completos.append({
                                "nome": produto[1],
                                "quantidade": item["quantidade"],
                                "preco_unitario": preco,
                                "subtotal": subtotal
                            })
                        
                        from datetime import datetime
                        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        pdf = gerar_comprovante_pdf(itens_completos, valor_total_venda, data_hora)
                        pdf_bytes = bytes(pdf.output())
                        
                        st.success("Venda registrada com sucesso!")
                        st.download_button("Baixar comprovante", data=pdf_bytes, file_name="comprovante.pdf", mime="application/pdf")
                        
                        st.session_state.itens_venda_atual = []
            
            with botoes_col2:
                if st.button("Limpar venda", use_container_width=True):
                    st.session_state.itens_venda_atual = []
                    st.toast("Carrinho limpo!")
                    st.rerun()

if menu == 'Histórico':
    st.header('Histórico de vendas')
    
    vendas = historico_vendas()
    
    if not vendas:
        st.info('Nenhuma venda registrada ainda.')
    else:
        vendas_agrupadas = {}
        for data_hora, nome, quantidade, preco_unitario in vendas:
            if data_hora not in vendas_agrupadas:
                vendas_agrupadas[data_hora] = []
            vendas_agrupadas[data_hora].append((nome, quantidade, preco_unitario))
        
        for data_hora, itens in sorted(vendas_agrupadas.items(), reverse=True):
            total_venda = sum(qtd * preco for _, qtd, preco in itens)
            
            with st.container(border=True):
                st.markdown(f"**{data_hora}**  ·  Total: R$ {total_venda:.2f}")
                for nome, quantidade, preco_unitario in itens:
                    st.caption(f"{quantidade}x {nome} — R$ {preco_unitario:.2f} cada")
                
                itens_pdf = [
                    {"nome": nome, "quantidade": qtd, "preco_unitario": preco, "subtotal": qtd * preco}
                    for nome, qtd, preco in itens
                ]
                pdf = gerar_comprovante_pdf(itens_pdf, total_venda, data_hora)
                pdf_bytes = bytes(pdf.output())
                
                st.download_button(
                    "Baixar comprovante",
                    data=pdf_bytes,
                    file_name=f"comprovante_{data_hora.replace(':', '-').replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{data_hora}"
                )
                    
if menu == 'Dashboard':
    st.header('Dashboard')
    
    total = faturamento_total()
    vendas = historico_vendas()
    produtos = listar_produtos()
    
    num_vendas = len(set(v[0] for v in vendas)) if vendas else 0
    ticket_medio = total / num_vendas if num_vendas > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Faturamento total', f'R$ {total:.2f}')
    with col2:
        st.metric('Ticket médio', f'R$ {ticket_medio:.2f}')
    with col3:
        st.metric('Vendas realizadas', num_vendas)
    
    st.subheader('Produtos mais vendidos')
    fig1 = grafico_produtos_mais_vendidos()
    st.pyplot(fig1)
    
    st.subheader('Vendas por dia')
    fig2 = grafico_vendas_por_dia()
    st.pyplot(fig2)
    
    st.subheader('Estoque baixo')
    produtos_baixo_estoque = [p for p in produtos if p[6] <= 5]
    if produtos_baixo_estoque:
        for p in produtos_baixo_estoque:
            st.warning(f"{p[1]} — restam apenas {p[6]} un.")
    else:
        st.success("Nenhum produto com estoque baixo.")
    
    st.subheader('Produtos parados')
    nomes_vendidos = set(v[1] for v in vendas)
    produtos_parados = [p for p in produtos if p[1] not in nomes_vendidos]
    if produtos_parados:
        for p in produtos_parados:
            st.caption(f"🔸 {p[1]} — nunca vendido")
    else:
        st.caption("Todos os produtos já tiveram alguma venda.")