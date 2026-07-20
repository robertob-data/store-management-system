from database import conectar

def adicionar_produto(nome, categoria, tamanho, cor, preco, quantidade_estoque):
    conecao = conectar()
    cursor = conecao.cursor()
    
    cursor.execute('''  
                   INSERT INTO produtos (nome, categoria, tamanho, cor, preco, quantidade_estoque)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ''', (nome, categoria, tamanho, cor, preco, quantidade_estoque))
    conecao.commit()
    conecao.close()
    
def listar_produtos():
    conecao = conectar()
    cursor = conecao.cursor()
    cursor.execute('SELECT * FROM produtos WHERE ativo = 1')
    produtos = cursor.fetchall()
    conecao.close()    
    return produtos
        
def atualizar_estoque(produto_id, nova_quantidade):
    conecao = conectar()
    cursor = conecao.cursor()
    
    cursor.execute('''
                   UPDATE produtos
                   SET quantidade_estoque = ?
                   WHERE id = ?
                   ''', (nova_quantidade, produto_id))
    
    if cursor.rowcount == 0:
        conecao.close()
        print(f"Erro: produto com id {produto_id} não encontrado.")
        return False
    
    conecao.commit()
    conecao.close()
    
    print(f'Estoque do produto: {produto_id} atualizado para: {nova_quantidade}')
    return True
    
def editar_produto(produto_id, nome, categoria, tamanho, cor, preco):
    conecao = conectar()
    cursor = conecao.cursor()
    
    cursor.execute('''
                   UPDATE produtos
                   SET nome = ?, categoria = ?, tamanho = ?, cor = ?, preco = ?
                   WHERE id = ?
                   
                   ''', (nome, categoria, tamanho, cor, preco, produto_id))
    conecao.commit()
    conecao.close()
    
    print(f'Produto: {produto_id} Editado com sucesso!')

def deletar_produto(produto_id):
    conecao = conectar()
    cursor = conecao.cursor()
    
    
    cursor.execute(''' 
                   UPDATE produtos
                   SET ativo = 0
                   WHERE id = ?
                   ''', (produto_id,))
    
    if cursor.rowcount == 0:
        conecao.close()
        print(f'Produto com ID: {produto_id} nao encontrado')
        return False
    
    conecao.commit()
    conecao.close()
    print(f'Produto id: {produto_id} removido (desativado)')
    return True
