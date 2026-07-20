import streamlit as st
from database import criar_tabelas
from produtos import adicionar_produto, listar_produtos, atualizar_estoque, editar_produto, deletar_produto
from vendas import (
    registrar_venda, historico_vendas, faturamento_total,
    produtos_mais_vendidos, vendas_por_dia,
    grafico_produtos_mais_vendidos, grafico_vendas_por_dia
)
import time
criar_tabelas()
st.title('Sistema de Vendas - Loja')
st.markdown("""
<style>
div.stButton > button {
    height: 70px;
    font-size: 16px;
    border-radius: 12px;
}
div[data-testid="stMetric"] {
    background-color: #f0f2f6;
    border-radius: 12px;
    padding: 15px;
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

# Define a página inicial
if "menu" not in st.session_state:
    st.session_state.menu = "Produtos"

# Cria os botões
for coluna, valor, rotulo in opcoes_menu:
    with coluna:

        tipo = "primary" if st.session_state.menu == valor else "secondary"

        if st.button(
            rotulo,
            key=valor,
            use_container_width=True,
            type=tipo,
        ):

            # Só atualiza se realmente mudou
            if st.session_state.menu != valor:
                st.session_state.menu = valor
                st.rerun()

# Menu selecionado
menu = st.session_state.menu

if menu == 'Produtos':
    st.header('Produtos Cadastrados')
    produtos = listar_produtos()
    
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
                    
                    # Mostra a mensagem de sucesso
                    st.success(f"Produto '{nome}' cadastrado com sucesso!")
                    
                    # Espera 1.5 segundos para o usuário ler a mensagem antes de recarregar
                    time.sleep(1.5) 
                    st.rerun()
    
    if not produtos:
        st.info('Nenhum produto cadastrado ainda.')
    else:
        for produto in produtos:
            id, nome, categoria, tamanho, cor, preco, estoque, ativo = produto
            
    for produto in produtos:
        id, nome, categoria, tamanho, cor, preco, estoque, ativo = produto
        
        cor_estoque = "🟢" if estoque > 5 else "🟡" if estoque > 0 else "🔴"
        
        st.markdown(f"""
<div style="background-color:#f9f9f9; border-radius:10px; padding:12px 16px; margin-bottom:10px; border:1px solid #e0e0e0;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <b style="color:#1a1a1a;">{nome}</b><br>
            <span style="color:#666; font-size:13px;">{categoria} — {tamanho}/{cor}</span>
        </div>
        <div style="text-align:right;">
            <b style="color:#1a1a1a;">R$ {preco:.2f}</b><br>
            <span style="color:#333; font-size:13px;">{cor_estoque} Estoque: {estoque}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
                        
                    
if menu == "Nova venda":
    st.header("Registrar nova venda")
    
    if "itens_venda_atual" not in st.session_state:
        st.session_state.itens_venda_atual = []
    
    produtos = listar_produtos()
    
    if not produtos:
        st.info("Cadastre produtos antes de registrar uma venda.")
    else:
        # Mapeia os dados do produto. p[6] é o estoque atual do produto no banco.
        opcoes = {f"{p[1]} ({p[3]}/{p[4]}) - Estoque: {p[6]}": {"id": p[0], "estoque": p[6]} for p in produtos}
        
        col1, col2 = st.columns([3, 1])
        with col1:
            escolha = st.selectbox("Produto", opcoes.keys())
        with col2:
            quantidade = st.number_input("Quantidade", min_value=1, value=1)
        
        if st.button("Adicionar item"):
            produto_id = opcoes[escolha]["id"]
            estoque_disponivel = opcoes[escolha]["estoque"]
            
            # Descobre quanto deste produto já está no carrinho
            qtd_ja_no_carrinho = sum(item["quantidade"] for item in st.session_state.itens_venda_atual if item["produto_id"] == produto_id)
            qtd_total_solicitada = qtd_ja_no_carrinho + quantidade
            
            if estoque_disponivel == 0:
                st.error("Este produto está esgotado!")
            elif qtd_total_solicitada > estoque_disponivel:
                # Se já tem o item no carrinho, mostra o texto completo
                if qtd_ja_no_carrinho > 0:
                    st.error(f"Estoque insuficiente! Você já adicionou {qtd_ja_no_carrinho}x ao carrinho e restam apenas {estoque_disponivel - qtd_ja_no_carrinho}x disponíveis no estoque.")
                # Se o carrinho está vazio para esse produto, mostra uma mensagem direta
                else:
                    st.error(f"Estoque insuficiente! Você tentou adicionar {quantidade}x, mas restam apenas {estoque_disponivel}x em estoque.")
            else:
                st.session_state.itens_venda_atual.append({
                    "produto_id": produto_id,
                    "quantidade": quantidade,
                    "nome": escolha
                })
                st.rerun() # Atualiza a tela para mostrar o item no carrinho imediatamente
        
        if st.session_state.itens_venda_atual:
            st.subheader("Itens da venda")
            for item in st.session_state.itens_venda_atual:
                st.write(f"- {item['nome']} — {item['quantidade']}x")
            
            # Cria colunas para organizar os botões de ação final lado a lado
            botoes_col1, botoes_col2 = st.columns([1, 1])
            
            with botoes_col1:
                if st.button("Finalizar venda", type="primary"):
                    sucesso = registrar_venda(st.session_state.itens_venda_atual)
                    if sucesso:
                        st.success("Venda registrada com sucesso!")
                        st.session_state.itens_venda_atual = []
                        import time
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Erro ao registrar venda (confira estoque).")
            
            with botoes_col2:
                # O botão para limpar a venda atual que você pediu
                if st.button("Limpar venda", use_container_width=True):
                    st.session_state.itens_venda_atual = []
                    st.toast("Carrinho limpo!")
                    st.rerun()
                    
                    
if menu == 'Histórico':
    st.header('Historico de Vendas')
    
    vendas = historico_vendas()
    
    if not vendas:
        st.info('Nenhuma Venda Registrada Ainda.')
    else:
        for venda in vendas:
            data_hora, nome, quantidade, preco_unitario = venda
            subtotal = quantidade * preco_unitario
            st.text(f"{data_hora} — {nome} — {quantidade}x R$ {preco_unitario:.2f} = R$ {subtotal:.2f}")
            
            
if menu == 'Dashboard':
    st.header('Dashboard')
    
    total = faturamento_total()
    st.metric(f'Faturamento Total', f'R$ {total:.2f}')
    st.markdown("""
<style>
div.stButton > button {
    height: 70px;
    font-size: 16px;
    border-radius: 12px;
}
div[data-testid="stMetric"] {
    background-color: #f0f2f6;
    border-radius: 12px;
    padding: 15px;
}
div[data-testid="stMetric"] label,
div[data-testid="stMetric"] div {
    color: #1a1a1a !important;
}
</style>
""", unsafe_allow_html=True)
    
    st.subheader('Produtos Mais Vendidos')
    fig1 = grafico_produtos_mais_vendidos()
    st.pyplot(fig1)
    
    st.subheader('Vendas Por Dia')
    fig2 = grafico_vendas_por_dia()
    st.pyplot(fig2)