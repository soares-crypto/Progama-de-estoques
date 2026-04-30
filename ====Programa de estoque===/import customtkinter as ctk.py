import customtkinter as ctk
import sqlite3
import json
import os
from tkinter import messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Configurações de Aparência
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ARQUIVO_CONFIG = "config.json"
DB_NAME = "estoque_v2.db"

# --- BANCO DE DADOS SQLITE ---
def iniciar_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Tabela de Produtos
    c.execute('''CREATE TABLE IF NOT EXISTS produtos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT UNIQUE,
                    quantidade INTEGER,
                    preco REAL,
                    validade TEXT,
                    estoque_minimo INTEGER,
                    categoria TEXT)''')
    # Tabela de Histórico/Vendas
    c.execute('''CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    tipo TEXT,
                    produto TEXT,
                    quantidade INTEGER,
                    total REAL)''')
    conn.commit()
    conn.close()

iniciar_db()

# --- FUNÇÕES DE SISTEMA ---
def carregar_configuracoes():
    if os.path.exists(ARQUIVO_CONFIG):
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

# --- TELA DE LOGIN (Mantida Original) ---
class LoginScreen(ctk.CTk):
    def __init__(self, on_login_success, config_data):
        super().__init__()
        self.on_login_success = on_login_success
        self.config = config_data
        self.title("Acesso ao Sistema")
        self.geometry("400x450")
        self.resizable(False, False)
        
        self.label = ctk.CTkLabel(self, text="🔒 LOGIN DO SISTEMA", font=("Roboto", 22, "bold"))
        self.label.pack(pady=(50, 30))

        self.entry_user = ctk.CTkEntry(self, placeholder_text="Usuário", width=280, height=45)
        self.entry_user.pack(pady=10)

        self.entry_pass = ctk.CTkEntry(self, placeholder_text="Senha", width=280, height=45, show="*")
        self.entry_pass.pack(pady=10)

        self.btn_login = ctk.CTkButton(self, text="ENTRAR", width=280, height=50, command=self.verificar_login)
        self.btn_login.pack(pady=40)

    def verificar_login(self):
        u_digitado = self.entry_user.get().strip()
        s_digitada = self.entry_pass.get().strip()
        credenciais = self.config.get("acessos", {})
        
        for nivel, dados in credenciais.items():
            if u_digitado == dados.get("usuario") and s_digitada == dados.get("senha"):
                self.destroy()
                self.on_login_success(nivel)
                return
        messagebox.showerror("Erro", "Acesso Negado!")

# --- APP PRINCIPAL ---
class App(ctk.CTk):
    def __init__(self, nivel_acesso):
        super().__init__()
        self.nivel_acesso = nivel_acesso
        self.title(f"StockMaster Pro V2 - {self.nivel_acesso.upper()}")
        self.geometry("1200x800")

        # Layout Principal
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Menu Lateral
        self.nav_frame = ctk.CTkFrame(self, corner_radius=0, width=220)
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.nav_frame, text="📊 STOCK\nPRO", font=("bold", 24)).pack(pady=30)

        self.add_menu_btn("Início / Alertas", self.show_home)
        self.add_menu_btn("Cadastrar / Entrada", self.show_entrada)
        self.add_menu_btn("Vender Produto", self.show_vendas)
        self.add_menu_btn("Consultar Estoque", self.show_busca)
        
        if self.nivel_acesso == "admin":
            self.add_menu_btn("Inventário Geral", self.show_inventario)
            self.add_menu_btn("Dashboard Financeiro", self.show_financeiro)

        ctk.CTkButton(self.nav_frame, text="Sair", fg_color="#e74c3c", command=self.destroy).pack(side="bottom", pady=20, padx=20, fill="x")

        self.main_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        self.show_home()

    def add_menu_btn(self, text, cmd):
        ctk.CTkButton(self.nav_frame, text=text, command=cmd, height=40).pack(pady=5, padx=20, fill="x")

    def limpar_frame(self):
        for w in self.main_frame.winfo_children(): w.destroy()

    # --- TELAS ---
    def show_home(self):
        self.limpar_frame()
        ctk.CTkLabel(self.main_frame, text="Painel de Monitoramento", font=("bold", 26)).pack(pady=20)
        
        container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        container.pack(fill="both", expand=True)

        # Lógica de Alertas (SQLite)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Alerta Estoque Baixo
        c.execute("SELECT nome, quantidade, estoque_minimo FROM produtos WHERE quantidade <= estoque_minimo")
        baixos = c.fetchall()
        
        # Alerta Vencimento (30 dias)
        c.execute("SELECT nome, validade FROM produtos")
        todos = c.fetchall()
        hoje = datetime.now()
        vencendo = []
        for p in todos:
            try:
                dt = datetime.strptime(p[1], "%d/%m/%Y")
                if dt <= hoje + timedelta(days=30): vencendo.append(p[0])
            except: pass
        conn.close()

        # UI Alertas
        f_alertas = ctk.CTkScrollableFrame(container, label_text="Alertas Críticos")
        f_alertas.pack(side="left", fill="both", expand=True, padx=10)

        for b in baixos:
            ctk.CTkLabel(f_alertas, text=f"⚠️ BAIXO ESTOQUE: {b[0]} ({b[1]} un)", text_color="#e67e22").pack(anchor="w")
        for v in vencendo:
            ctk.CTkLabel(f_alertas, text=f"⏰ VENCIMENTO PRÓXIMO: {v}", text_color="#f1c40f").pack(anchor="w")

    def show_entrada(self):
        self.limpar_frame()
        c = ctk.CTkFrame(self.main_frame, fg_color="transparent"); c.pack(expand=True)
        ctk.CTkLabel(c, text="Cadastro de Mercadoria", font=("bold", 24)).pack(pady=20)
        
        self.e_n = self.inpt(c, "Nome do Produto")
        self.e_q = self.inpt(c, "Quantidade")
        self.e_p = self.inpt(c, "Preço Unitário")
        self.e_v = self.inpt(c, "Validade (DD/MM/AAAA)")
        self.e_m = self.inpt(c, "Estoque Mínimo (Alerta)")
        self.e_cat = ctk.CTkComboBox(c, values=["Alimentos", "Bebidas", "Limpeza", "Outros"], width=400, height=45)
        self.e_cat.pack(pady=10)
        
        ctk.CTkButton(c, text="SALVAR NO BANCO", fg_color="#2ecc71", height=50, command=self.add_db).pack(pady=20, fill="x")

    def add_db(self):
        # Validação Refatorada (Tratamento de Erros)
        try:
            nome = self.e_n.get().strip().capitalize()
            if not nome: raise ValueError("O nome não pode estar vazio.")
            
            try: qtd = int(self.e_q.get())
            except: raise ValueError("Quantidade deve ser um número inteiro.")
            
            try: preco = float(self.e_p.get().replace(",", "."))
            except: raise ValueError("Preço inválido. Use 0.00")
            
            try: est_min = int(self.e_m.get())
            except: raise ValueError("Estoque mínimo deve ser um número.")

            validade = self.e_v.get().strip()
            # Validação de data (Ano atual e formato)
            dt_val = datetime.strptime(validade, "%d/%m/%Y")
            if dt_val.year != datetime.now().year:
                raise ValueError("Só aceitamos produtos fabricados no ano atual.")

            cat = self.e_cat.get()

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute('''INSERT INTO produtos (nome, quantidade, preco, validade, estoque_minimo, categoria)
                         VALUES (?, ?, ?, ?, ?, ?)
                         ON CONFLICT(nome) DO UPDATE SET 
                         quantidade = quantidade + excluded.quantidade,
                         preco = excluded.preco,
                         validade = excluded.validade''', (nome, qtd, preco, validade, est_min, cat))
            
            c.execute("INSERT INTO historico (data, tipo, produto, quantidade, total) VALUES (?, ?, ?, ?, ?)",
                      (datetime.now().strftime("%d/%m/%Y %H:%M"), "ENTRADA", nome, qtd, qtd*preco))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Produto registrado com sucesso!")
            self.show_home()
        except ValueError as e:
            messagebox.showerror("Erro de Cadastro", str(e))
        except Exception as e:
            messagebox.showerror("Erro fatal", f"Erro no Banco: {e}")

    def show_vendas(self):
        self.limpar_frame()
        c = ctk.CTkFrame(self.main_frame, fg_color="transparent"); c.pack(expand=True)
        ctk.CTkLabel(c, text="Ponto de Venda", font=("bold", 24)).pack(pady=20)
        self.v_n = self.inpt(c, "Nome do Produto")
        self.v_q = self.inpt(c, "Quantidade")
        ctk.CTkButton(c, text="EFETUAR VENDA", fg_color="#3498db", height=50, command=self.venda_db).pack(pady=20, fill="x")

    def venda_db(self):
        try:
            nome = self.v_n.get().strip().capitalize()
            qtd_venda = int(self.v_q.get())
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT quantidade, preco FROM produtos WHERE nome=?", (nome,))
            res = c.fetchone()
            
            if res and res[0] >= qtd_venda:
                nova_qtd = res[0] - qtd_venda
                c.execute("UPDATE produtos SET quantidade=? WHERE nome=?", (nova_qtd, nome))
                c.execute("INSERT INTO historico (data, tipo, produto, quantidade, total) VALUES (?, ?, ?, ?, ?)",
                          (datetime.now().strftime("%d/%m/%Y %H:%M"), "SAÍDA", nome, qtd_venda, qtd_venda*res[1]))
                conn.commit()
                messagebox.showinfo("Sucesso", "Venda realizada!")
            else:
                messagebox.showerror("Erro", "Estoque insuficiente!")
            conn.close()
        except: messagebox.showerror("Erro", "Dados de venda inválidos")

    def show_inventario(self):
        self.limpar_frame()
        ctk.CTkLabel(self.main_frame, text="Inventário Geral (SQLite)", font=("bold", 24)).pack(pady=10)
        
        scroll = ctk.CTkScrollableFrame(self.main_frame)
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT nome, quantidade, preco, categoria, estoque_minimo FROM produtos")
        for p in c.fetchall():
            # Cor inteligente para estoque baixo
            cor = "#e67e22" if p[1] <= p[4] else "white"
            f = ctk.CTkFrame(scroll)
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"{p[3]} | {p[0]}", width=300, anchor="w", text_color=cor).pack(side="left", padx=10)
            ctk.CTkLabel(f, text=f"Qtd: {p[1]}").pack(side="left", padx=20)
            ctk.CTkLabel(f, text=f"R$ {p[2]:.2f}").pack(side="left", padx=20)
        conn.close()

    def show_financeiro(self):
        self.limpar_frame()
        ctk.CTkLabel(self.main_frame, text="Dashboard Analytics", font=("bold", 24)).pack(pady=10)
        
        fig_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        fig_container.pack(fill="both", expand=True)

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Dados para Pizza (Vendas por Produto)
        c.execute("SELECT produto, SUM(quantidade) FROM historico WHERE tipo='SAÍDA' GROUP BY produto")
        vendas_p = c.fetchall()
        
        # Dados para Barras (Vendas por Categoria)
        c.execute('''SELECT p.categoria, SUM(h.total) 
                     FROM historico h JOIN produtos p ON h.produto = p.nome 
                     WHERE h.tipo='SAÍDA' GROUP BY p.categoria''')
        vendas_c = c.fetchall()
        conn.close()

        if vendas_p:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), facecolor="#2b2b2b")
            
            # Gráfico de Pizza
            ax1.pie([x[1] for x in vendas_p], labels=[x[0] for x in vendas_p], autopct='%1.1f%%', textprops={'color':"w"})
            ax1.set_title("Top Produtos Vendidos", color="w")

            # Gráfico de Barras
            ax2.bar([x[0] for x in vendas_c], [x[1] for x in vendas_c], color="#3498db")
            ax2.set_title("Receita por Categoria", color="w")
            ax2.tick_params(colors='w')

            canvas = FigureCanvasTkAgg(fig, master=fig_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            ctk.CTkLabel(fig_container, text="Sem dados de vendas para gerar gráficos.").pack()

    # --- AUXILIAR ---
    def inpt(self, m, p):
        e = ctk.CTkEntry(m, placeholder_text=p, width=400, height=45); e.pack(pady=10); return e

# --- MAIN ---
def main():
    config = carregar_configuracoes()
    if not config:
        messagebox.showerror("Erro", "config.json não encontrado!")
        return
    
    def login_ok(nivel):
        app = App(nivel); app.mainloop()

    login = LoginScreen(on_login_success=login_ok, config_data=config)
    login.mainloop()

if __name__ == "__main__":
    main()