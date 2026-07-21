from database import conectar
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF


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
    
    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor("#EDEAE3")
    ax.set_facecolor("#EDEAE3")
    ax.bar(nomes, quantidades, color="#7A8B69")
    ax.set_title("Produtos mais vendidos")
    ax.set_ylabel("Quantidade vendida")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", fontsize=9)
    fig.tight_layout()
    return fig

def grafico_vendas_por_dia():
    dados = vendas_por_dia()
    dias = [linha[0] for linha in dados]
    totais = [linha[1] for linha in dados]
    
    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_facecolor("#EDEAE3")
    ax.set_facecolor("#EDEAE3")
    ax.plot(dias, totais, marker="o", color="#7A8B69", linewidth=2)
    ax.fill_between(dias, totais, alpha=0.15, color="#7A8B69")
    ax.set_title("Vendas por dia")
    ax.set_ylabel("Faturamento (R$)")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", fontsize=9)
    fig.tight_layout()
    return fig

def gerar_comprovante_pdf(itens, valor_total, data_hora):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, "Loja", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Comprovante de venda", ln=True, align="C")
    pdf.ln(3)
    
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, f"Data: {data_hora}", ln=True)
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(90, 8, "Item", border="B")
    pdf.cell(30, 8, "Qtd", border="B", align="C")
    pdf.cell(35, 8, "Preço un.", border="B", align="R")
    pdf.cell(35, 8, "Subtotal", border="B", align="R", ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    for item in itens:
        pdf.cell(90, 8, item["nome"], border="B")
        pdf.cell(30, 8, str(item["quantidade"]), border="B", align="C")
        pdf.cell(35, 8, f"R$ {item['preco_unitario']:.2f}", border="B", align="R")
        pdf.cell(35, 8, f"R$ {item['subtotal']:.2f}", border="B", align="R", ln=True)
    
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(20, 20, 20)
    pdf.cell(0, 10, f"Total: R$ {valor_total:.2f}", align="R", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "Obrigado pela preferência!", align="C")
    
    return pdf