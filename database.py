import sqlite3
def conectar():
    conect = sqlite3.connect('loja.db')
    conect.execute('PRAGMA foreign_keys = ON')
    return conect

def criar_tabelas():
    conecao = conectar()
    cursor = conecao.cursor()
    
    cursor.execute(''' 
                CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    categoria TEXT,
                    tamanho TEXT,
                    cor TEXT,
                    preco REAL NOT NULL,
                    quantidade_estoque INTEGER NOT NULL DEFAULT 0,
                    ativo INTEGER NOT NULL DEFAULT 1
                )
                   ''')
    
    
    cursor.execute(''' 
                   CREATE TABLE IF NOT EXISTS vendas (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       data_hora TEXT NOT NULL,
                       valor_total REAL NOT NULL
                   )
                   ''')
    
    cursor.execute(''' 
                   CREATE TABLE IF NOT EXISTS itens_venda (
                       id INTEGER PRIMARY KEY AUTOINCREMENT,
                       venda_id INTEGER NOT NULL,
                       produto_id INTEGER NOT NULL,
                       quantidade INTEGER NOT NULL,
                       preco_unitario REAL NOT NULL,
                       FOREIGN KEY (venda_id) REFERENCES vendas(id),
                       FOREIGN KEY (produto_id) REFERENCES produtos(id)
                       
                   )
                   ''')
    
    conecao.commit()
    conecao.close()
 