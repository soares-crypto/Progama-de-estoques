from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = "estoque_seguro_123"

# --- FUNÇÕES DE DADOS ---
def carregar_dados(arquivo):
    caminho = os.path.join(base_dir, arquivo)
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {} if "estoque" in arquivo else []

def salvar_dados(arquivo, dados):
    caminho = os.path.join(base_dir, arquivo)
    with open(caminho, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def carregar_config():
    caminho = os.path.join(base_dir, "config.json")
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --- ROTAS DE NAVEGAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('usuario').strip()
        s = request.form.get('senha').strip()
        config = carregar_config()
        
        if config:
            adm = config["acessos"]["admin"]
            usr = config["acessos"]["comum"]
            if u == adm["usuario"] and s == adm["senha"]:
                session['usuario'], session['nivel'] = u, 'admin'
                return redirect(url_for('index'))
            elif u == usr["usuario"] and s == usr["senha"]:
                session['usuario'], session['nivel'] = u, 'usuario'
                return redirect(url_for('index'))
        flash("Acesso Negado!")
    return render_template('login.html')

@app.route('/')
def index():
    if 'usuario' not in session: 
        return redirect(url_for('login'))
    
    estoque = carregar_dados("dados_estoque.json")
    historico = carregar_dados("historico_movimentacoes.json")
    
    v_e = sum(i['quantidade'] * i['preco'] for i in estoque.values())
    l_v = sum(m.get('total', 0) for m in historico if m.get('tipo') == "SAÍDA")
    
    return render_template('index.html', 
                           estoque=estoque, 
                           historico=reversed(historico), 
                           v_e=v_e, 
                           l_v=l_v, 
                           nivel=session.get('nivel'))

# --- LÓGICA DE OPERAÇÕES ---
@app.route('/adicionar', methods=['POST'])
def adicionar():
    estoque = carregar_dados("dados_estoque.json")
    historico = carregar_dados("historico_movimentacoes.json")
    
    nome = request.form.get('nome').capitalize()
    qtd = int(request.form.get('qtd'))
    preco = float(request.form.get('preco').replace(',', '.'))
    validade = request.form.get('validade') 
    
    dt = datetime.strptime(validade, '%Y-%m-%d')
    validade_br = dt.strftime('%d/%m/%Y')

    if dt.year != 2026:
        flash("Erro: Apenas produtos com validade em 2026!")
        return redirect(url_for('index'))

    estoque[nome] = {
        "quantidade": estoque.get(nome, {}).get('quantidade', 0) + qtd,
        "preco": preco,
        "validade": validade_br
    }
    historico.append({
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "tipo": "ENTRADA", "produto": nome, "quantidade": qtd, "total": qtd * preco
    })
    
    salvar_dados("dados_estoque.json", estoque)
    salvar_dados("historico_movimentacoes.json", historico)
    return redirect(url_for('index'))

@app.route('/vender', methods=['POST'])
def vender():
    estoque = carregar_dados("dados_estoque.json")
    historico = carregar_dados("historico_movimentacoes.json")
    nome = request.form.get('nome').capitalize()
    qtd = int(request.form.get('qtd'))

    if nome in estoque and estoque[nome]['quantidade'] >= qtd:
        # Lógica de venda original mantida
        preco = estoque[nome]['preco']
        estoque[nome]['quantidade'] -= qtd
        if estoque[nome]['quantidade'] <= 0: del estoque[nome]
        
        historico.append({
            "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "tipo": "SAÍDA", "produto": nome, "quantidade": qtd, "total": qtd * preco
        })
        salvar_dados("dados_estoque.json", estoque)
        salvar_dados("historico_movimentacoes.json", historico)
    else:
        flash("Estoque insuficiente ou produto inexistente!")
    
    return redirect(url_for('index'))

# --- NOVA ROTA: APAGAR ITEM (SÓ PARA ADMIN) ---
@app.route('/apagar/<nome>')
def apagar(nome):
    if session.get('nivel') != 'admin':
        flash("Acesso Proibido!")
        return redirect(url_for('index'))
    
    estoque = carregar_dados("dados_estoque.json")
    if nome in estoque:
        del estoque[nome]
        salvar_dados("dados_estoque.json", estoque)
        flash(f"Item {nome} removido!")
    return redirect(url_for('index'))

@app.route('/sair')
def sair():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)