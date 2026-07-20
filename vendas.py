from database import conectar
import matplotlib.pyplot as plt
from datetime import datetime

def registrar_venda(itens):
    conecao = conectar()
    cursor = conecao.cursor()
    
     # Passo 1: calcular o valor total, buscando o preço atual de cada produto
    valor_total = 0
    for iten in itens:
        cursor.execute('SELECT preco, quantidade_estoque FROM produtos WHERE ID = ?', (iten['produto_id'],))
        resultado = cursor.fetchone()
        
        if resultado is None:
            conecao.close()
            print(f'[ERRO] produto {iten['produto_id']} nao encontrado.')
            return False
        
        preco, estoque_atual = resultado
    
        if estoque_atual < iten['quantidade']:
            conecao.close()
            print(f'[ERRO] estoque indisponivel pro produto {iten['produto_id']}')
            return None
    
        valor_total += preco * iten['quantidade']
    
    
    # Passo 2: criar o cabeçalho da venda (agora que já validamos tudo)
    
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(''' 
                   INSERT INTO vendas (data_hora, valor_total)
                   VALUES (?, ?)
                   ''', (data_hora, valor_total))
    venda_id = cursor.lastrowid
    
    # Passo 3: inserir cada item e descontar estoque
    for iten in itens:
        cursor.execute('SELECT preco FROM produtos WHERE id = ?', (iten['produto_id'],))
        preco = cursor.fetchone()[0]
        
        cursor.execute(''' 
                       INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario)
                       VALUES (?, ?, ?, ?)
                       ''', (venda_id, iten['produto_id'], iten['quantidade'], preco))
        
        cursor.execute(''' 
                       UPDATE produtos
                       SET quantidade_estoque = quantidade_estoque - ?
                       WHERE id = ?
                       
                       ''', (iten['quantidade'], iten['produto_id']))
        
    conecao.commit()
    conecao.close()
    print(f'Venda {venda_id} Registrada com sucesso1, Total R$: {valor_total:.2f}')
    return True
    
def historico_vendas(data_inicio=None, data_fim=None):
    conexao = conectar()
    cursor = conexao.cursor()
    
    query = '''
        SELECT 
            vendas.data_hora,
            produtos.nome,
            itens_venda.quantidade,
            itens_venda.preco_unitario
        FROM itens_venda
        JOIN vendas ON itens_venda.venda_id = vendas.id
        JOIN produtos ON itens_venda.produto_id = produtos.id
    '''
    parametros = []
    
    if data_inicio and data_fim:
        query += ' WHERE vendas.data_hora BETWEEN ? AND ?'
        parametros = [data_inicio, data_fim]
    
    query += ' ORDER BY vendas.data_hora DESC'
    
    cursor.execute(query, parametros)
    resultados = cursor.fetchall()
    conexao.close()
    
    for linha in resultados:
        data_hora, nome, quantidade, preco_unitario = linha
        subtotal = quantidade * preco_unitario
        print(f"{data_hora} | {nome} | {quantidade}x R${preco_unitario:.2f} = R${subtotal:.2f}")
        
    return resultados 
    
#dashboard
def faturamento_total():
    conecao = conectar()
    cursor = conecao.cursor()
    
    cursor.execute('SELECT SUM(valor_total) FROM vendas')
    resultado = cursor.fetchone()[0]
    conecao.close()
    
    return resultado if resultado is not None else 0

def produtos_mais_vendidos(limite=5):
    conecao = conectar()
    cursor = conecao.cursor()
    
    cursor.execute(''' 
                   SELECT produtos.nome , SUM(itens_venda.quantidade) as total_vendido
                   FROM itens_venda
                   JOIN produtos ON itens_venda.produto_id = produtos.id
                   GROUP BY produtos.nome
                   ORDER BY total_vendido DESC
                   LIMIT ?
                   
                   ''', (limite,))
    resultado = cursor.fetchall()
    conecao.close()
    
    return resultado

def vendas_por_dia():
    conecao = conectar()
    cursor = conecao.cursor()
    
    cursor.execute(''' 
                   SELECT DATE(data_hora) as dia, SUM(valor_total) as total_dia
                   FROM vendas
                   GROUP BY dia
                   ORDER BY dia
                   ''')
    
    resultados = cursor.fetchall()
    conecao.close()
    
    return resultados

def grafico_produtos_mais_vendidos(limite=5):
    dados = produtos_mais_vendidos(limite)
    nomes = [linha[0] for linha in dados]
    quantidades = [linha[1] for linha in dados]
    
    fig, ax = plt.subplots()
    ax.bar(nomes, quantidades, color="#6C63FF")
    ax.set_title("Produtos mais vendidos")
    ax.set_ylabel("Quantidade vendida")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    return fig

def grafico_vendas_por_dia():
    dados = vendas_por_dia()
    dias = [linha[0] for linha in dados]
    totais = [linha[1] for linha in dados]
    
    fig, ax = plt.subplots()
    ax.plot(dias, totais, marker="o", color="#6C63FF", linewidth=2)
    ax.fill_between(dias, totais, alpha=0.1, color="#6C63FF")
    ax.set_title("Vendas por dia")
    ax.set_ylabel("Faturamento (R$)")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    return fig