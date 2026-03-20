#!/usr/bin/env python3
"""
Sistema de Estoque Profissional – GUI Tkinter
Versao 2.0.0 | Interface gráfica nativa, 100% mouse
Dependências: apenas stdlib (sqlite3, tkinter)
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import os
import sys
from datetime import datetime, date
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# TEMA / PALETA
# ═══════════════════════════════════════════════════════════════════

C = {
    "bg":       "#0d1a0d",
    "bg2":      "#111f11",
    "bg3":      "#162116",
    "sidebar":  "#0a140a",
    "border":   "#1e3a1e",
    "green":    "#39ff14",
    "green2":   "#27c409",
    "green3":   "#1a8c04",
    "green_dim":"#4a7a3a",
    "amber":    "#ffb300",
    "red":      "#ff4444",
    "text":     "#c8e6c0",
    "text_dim": "#6a9b5a",
    "sel_bg":   "#1a3d0a",
    "sel_fg":   "#39ff14",
    "input_bg": "#0d1a0d",
    "btn_bg":   "#162116",
    "btn_act":  "#1a4a0a",
    "topbar":   "#0a140a",
}
FONT_MAIN  = ("JetBrains Mono", 11)
FONT_BOLD  = ("JetBrains Mono", 11, "bold")
FONT_SM    = ("JetBrains Mono", 10)
FONT_LG    = ("JetBrains Mono", 14, "bold")
FONT_XL    = ("JetBrains Mono", 20, "bold")
FONT_TITLE = ("JetBrains Mono", 12, "bold")
FONT_MONO  = ("Courier", 11)

# fallback se JetBrains Mono não estiver instalada
import tkinter.font as tkfont
def _safe_font(family, size, *styles):
    try:
        f = tkfont.Font(family=family, size=size)
        f.actual()
        return (family, size) + styles
    except Exception:
        return ("Courier", size) + styles

def _fix_fonts():
    global FONT_MAIN, FONT_BOLD, FONT_SM, FONT_LG, FONT_XL, FONT_TITLE, FONT_MONO
    FONT_MAIN  = _safe_font("JetBrains Mono", 11)
    FONT_BOLD  = _safe_font("JetBrains Mono", 11, "bold")
    FONT_SM    = _safe_font("JetBrains Mono", 10)
    FONT_LG    = _safe_font("JetBrains Mono", 14, "bold")
    FONT_XL    = _safe_font("JetBrains Mono", 20, "bold")
    FONT_TITLE = _safe_font("JetBrains Mono", 12, "bold")

# ═══════════════════════════════════════════════════════════════════
# BANCO DE DADOS
# ═══════════════════════════════════════════════════════════════════

DB_PATH = os.environ.get("ESTOQUE_DB", str(Path.home() / "estoque.db"))

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def inicializar_banco():
    with conectar() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS config (chave TEXT PRIMARY KEY, valor TEXT);
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL UNIQUE, descricao TEXT);
            CREATE TABLE IF NOT EXISTS fornecedores (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
                contato TEXT, email TEXT, telefone TEXT, ativo INTEGER NOT NULL DEFAULT 1);
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
                descricao TEXT, sku TEXT UNIQUE,
                preco_venda REAL NOT NULL DEFAULT 0, preco_custo REAL NOT NULL DEFAULT 0,
                estoque INTEGER NOT NULL DEFAULT 0, estoque_minimo INTEGER NOT NULL DEFAULT 5,
                categoria_id INTEGER REFERENCES categorias(id),
                fornecedor_id INTEGER REFERENCES fornecedores(id),
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT DEFAULT (datetime('now','localtime')));
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL,
                email TEXT UNIQUE, telefone TEXT, endereco TEXT, cpf_cnpj TEXT,
                criado_em TEXT DEFAULT (datetime('now','localtime')));
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER REFERENCES clientes(id),
                status TEXT NOT NULL DEFAULT 'ativo',
                forma_pagamento TEXT NOT NULL DEFAULT 'Nao informado',
                total REAL NOT NULL DEFAULT 0, desconto REAL NOT NULL DEFAULT 0,
                observacao TEXT, criado_em TEXT DEFAULT (datetime('now','localtime')));
            CREATE TABLE IF NOT EXISTS pedido_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL REFERENCES pedidos(id),
                produto_id INTEGER NOT NULL REFERENCES produtos(id),
                quantidade INTEGER NOT NULL, preco_unitario REAL NOT NULL,
                subtotal REAL NOT NULL, devolvido INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS entradas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fornecedor_id INTEGER REFERENCES fornecedores(id),
                total REAL NOT NULL DEFAULT 0, observacao TEXT,
                criado_em TEXT DEFAULT (datetime('now','localtime')));
            CREATE TABLE IF NOT EXISTS entrada_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entrada_id INTEGER NOT NULL REFERENCES entradas(id),
                produto_id INTEGER NOT NULL REFERENCES produtos(id),
                quantidade INTEGER NOT NULL, preco_unitario REAL NOT NULL, subtotal REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL REFERENCES produtos(id),
                tipo TEXT NOT NULL, quantidade INTEGER NOT NULL,
                estoque_ant INTEGER NOT NULL, estoque_pos INTEGER NOT NULL,
                referencia TEXT, criado_em TEXT DEFAULT (datetime('now','localtime')));
            CREATE TABLE IF NOT EXISTS metas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, mes TEXT NOT NULL UNIQUE,
                valor_meta REAL NOT NULL,
                criado_em TEXT DEFAULT (datetime('now','localtime')));
        """)
    _set_config_defaults()

def _set_config_defaults():
    defaults = {"empresa_nome": "Minha Empresa", "empresa_cnpj": "",
                "empresa_telefone": "", "empresa_endereco": "", "alerta_estoque": "5"}
    with conectar() as conn:
        for k, v in defaults.items():
            conn.execute("INSERT OR IGNORE INTO config (chave,valor) VALUES (?,?)", (k, v))

def get_config(chave, default=""):
    with conectar() as conn:
        row = conn.execute("SELECT valor FROM config WHERE chave=?", (chave,)).fetchone()
        return row["valor"] if row else default

def set_config(chave, valor):
    with conectar() as conn:
        conn.execute("INSERT OR REPLACE INTO config (chave,valor) VALUES (?,?)", (chave, valor))

def registrar_movimentacao(conn, produto_id, tipo, quantidade, referencia=""):
    prod = conn.execute("SELECT estoque FROM produtos WHERE id=?", (produto_id,)).fetchone()
    ea = prod["estoque"]
    saidas = ("saida", "ajuste_reducao")
    ep = ea - abs(quantidade) if tipo in saidas else ea + abs(quantidade)
    conn.execute(
        "INSERT INTO movimentacoes (produto_id,tipo,quantidade,estoque_ant,estoque_pos,referencia)"
        " VALUES (?,?,?,?,?,?)",
        (produto_id, tipo, quantidade, ea, ep, referencia))

def seed():
    with conectar() as conn:
        if conn.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
            conn.executemany("INSERT INTO categorias (nome,descricao) VALUES (?,?)", [
                ("Informatica",   "Computadores, perifericos e acessorios"),
                ("Audio e Video", "Headsets, monitores e cabos"),
                ("Acessorios",    "Mouses, teclados e hubs"),
            ])
        if conn.execute("SELECT COUNT(*) FROM fornecedores").fetchone()[0] == 0:
            conn.executemany("INSERT INTO fornecedores (nome,email,telefone) VALUES (?,?,?)", [
                ("TechDistrib Ltda",   "vendas@techdistrib.com",     "(11) 98000-0001"),
                ("Global Imports S/A", "comercial@globalimports.com","(21) 97000-0002"),
            ])
        if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] == 0:
            conn.executemany(
                "INSERT INTO produtos (nome,sku,preco_venda,preco_custo,estoque,"
                "estoque_minimo,categoria_id,fornecedor_id) VALUES (?,?,?,?,?,?,?,?)", [
                ("Notebook Pro 15",  "NB-001", 4500.00, 3200.00, 10, 3, 1, 1),
                ("Mouse Ergonomico", "MS-001",   89.90,   45.00, 50,10, 3, 2),
                ("Teclado Mecanico", "TC-001",  199.00,  110.00, 30, 8, 3, 2),
                ("Monitor 24 FHD",   "MN-001", 1299.00,  850.00, 15, 4, 2, 1),
                ("Headset USB",      "HS-001",  349.00,  190.00,  2, 5, 2, 1),
                ("Hub USB-C 7p",     "HB-001",  129.90,   65.00,  0, 5, 3, 2),
            ])
        if conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0] == 0:
            conn.executemany("INSERT INTO clientes (nome,email,telefone) VALUES (?,?,?)", [
                ("Ana Lima",    "ana@email.com",   "(11) 91111-0001"),
                ("Bruno Costa", "bruno@email.com", "(11) 92222-0002"),
                ("Carla Souza", "carla@email.com", "(11) 93333-0003"),
            ])

# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════

def fmtR(v):
    try: return f"R$ {float(v):.2f}"
    except: return "R$ 0.00"

FORMAS_PAGAMENTO = [
    "Dinheiro","Cartao de Credito","Cartao de Debito",
    "PIX","Boleto","Transferencia","Cheque","Outro",
]

# ═══════════════════════════════════════════════════════════════════
# WIDGETS BASE
# ═══════════════════════════════════════════════════════════════════

def apply_dark_style():
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Dark.Treeview",
        background=C["bg2"], foreground=C["text"],
        fieldbackground=C["bg2"], borderwidth=0,
        rowheight=26, font=FONT_SM)
    style.configure("Dark.Treeview.Heading",
        background=C["bg3"], foreground=C["green"],
        relief="flat", font=FONT_BOLD, borderwidth=0)
    style.map("Dark.Treeview",
        background=[("selected", C["sel_bg"])],
        foreground=[("selected", C["sel_fg"])])
    style.map("Dark.Treeview.Heading",
        background=[("active", C["bg3"])])

    style.configure("Dark.Vertical.TScrollbar",
        background=C["bg3"], troughcolor=C["bg"],
        arrowcolor=C["green_dim"], borderwidth=0, relief="flat")
    style.map("Dark.Vertical.TScrollbar",
        background=[("active", C["green3"])])

    style.configure("Dark.TCombobox",
        fieldbackground=C["input_bg"], background=C["bg3"],
        foreground=C["text"], arrowcolor=C["green"],
        borderwidth=1, relief="flat", font=FONT_SM)
    style.map("Dark.TCombobox",
        fieldbackground=[("readonly", C["input_bg"])],
        foreground=[("readonly", C["text"])],
        selectbackground=[("readonly", C["sel_bg"])],
        selectforeground=[("readonly", C["sel_fg"])])


class DarkFrame(tk.Frame):
    def __init__(self, parent, **kw):
        kw.setdefault("bg", C["bg2"])
        kw.setdefault("relief", "flat")
        super().__init__(parent, **kw)


class DarkLabel(tk.Label):
    def __init__(self, parent, **kw):
        kw.setdefault("bg",   C["bg2"])
        kw.setdefault("fg",   C["text"])
        kw.setdefault("font", FONT_SM)
        super().__init__(parent, **kw)


class DarkEntry(tk.Entry):
    def __init__(self, parent, **kw):
        kw.setdefault("bg",               C["input_bg"])
        kw.setdefault("fg",               C["text"])
        kw.setdefault("insertbackground", C["green"])
        kw.setdefault("relief",           "flat")
        kw.setdefault("font",             FONT_SM)
        kw.setdefault("bd",               1)
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", C["border"])
        kw.setdefault("highlightcolor",   C["green3"])
        super().__init__(parent, **kw)


class DarkButton(tk.Button):
    def __init__(self, parent, **kw):
        kw.setdefault("bg",               C["btn_bg"])
        kw.setdefault("fg",               C["green"])
        kw.setdefault("activebackground", C["btn_act"])
        kw.setdefault("activeforeground", C["green"])
        kw.setdefault("relief",           "flat")
        kw.setdefault("font",             FONT_SM)
        kw.setdefault("cursor",           "hand2")
        kw.setdefault("bd",               0)
        kw.setdefault("padx",             12)
        kw.setdefault("pady",             5)
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", C["border"])
        super().__init__(parent, **kw)
        self.bind("<Enter>", lambda e: self.config(bg=C["btn_act"]))
        self.bind("<Leave>", lambda e: self.config(bg=kw.get("bg", C["btn_bg"])))


class DangerButton(DarkButton):
    def __init__(self, parent, **kw):
        kw["bg"]               = "#2a0a0a"
        kw["fg"]               = C["red"]
        kw["activebackground"] = "#3d1010"
        kw["highlightbackground"] = "#550a0a"
        super().__init__(parent, **kw)
        self.bind("<Enter>", lambda e: self.config(bg="#3d1010"))
        self.bind("<Leave>", lambda e: self.config(bg="#2a0a0a"))


class AmberButton(DarkButton):
    def __init__(self, parent, **kw):
        kw["bg"]               = "#2a1e00"
        kw["fg"]               = C["amber"]
        kw["activebackground"] = "#3d2c00"
        kw["highlightbackground"] = "#554400"
        super().__init__(parent, **kw)
        self.bind("<Enter>", lambda e: self.config(bg="#3d2c00"))
        self.bind("<Leave>", lambda e: self.config(bg="#2a1e00"))


def sep(parent, orient="h", **kw):
    bg = kw.pop("bg", C["border"])
    if orient == "h":
        f = tk.Frame(parent, height=1, bg=bg, **kw)
    else:
        f = tk.Frame(parent, width=1, bg=bg, **kw)
    return f


def card(parent, title="", **kw):
    """Retorna (outer_frame, inner_frame)"""
    kw.setdefault("bg", C["bg2"])
    outer = tk.Frame(parent, bg=C["border"], pady=1, padx=1)
    inner = tk.Frame(outer, **kw)
    inner.pack(fill="both", expand=True)
    if title:
        hdr = tk.Frame(inner, bg=C["bg3"])
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {title}", bg=C["bg3"], fg=C["green"],
                 font=FONT_BOLD, anchor="w", pady=6).pack(side="left")
        sep(inner, "h").pack(fill="x")
    body = tk.Frame(inner, bg=C["bg2"])
    body.pack(fill="both", expand=True, padx=8, pady=8)
    return outer, body


def make_tree(parent, columns, show_scrollbar=True):
    frame = tk.Frame(parent, bg=C["bg2"])

    tree = ttk.Treeview(frame, columns=[c[0] for c in columns],
                        show="headings", style="Dark.Treeview",
                        selectmode="browse")

    for cid, heading, width, anchor in columns:
        tree.heading(cid, text=heading)
        tree.column(cid, width=width, anchor=anchor, stretch=False)

    tree.tag_configure("low",   foreground=C["amber"])
    tree.tag_configure("zero",  foreground=C["red"])
    tree.tag_configure("ok",    foreground=C["green"])
    tree.tag_configure("dim",   foreground=C["text_dim"])
    tree.tag_configure("cancel",foreground=C["red"])
    tree.tag_configure("dev",   foreground=C["amber"])

    if show_scrollbar:
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview,
                            style="Dark.Vertical.TScrollbar")
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")

    tree.pack(side="left", fill="both", expand=True)
    return frame, tree


# ═══════════════════════════════════════════════════════════════════
# DIÁLOGOS MODAIS
# ═══════════════════════════════════════════════════════════════════

class FormDialog(tk.Toplevel):
    def __init__(self, parent, title, fields, width=480):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=C["bg2"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")
        hdr = tk.Frame(self, bg=C["bg3"])
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {title}", bg=C["bg3"], fg=C["green"],
                 font=FONT_TITLE, anchor="w", pady=10).pack(side="left")
        tk.Frame(self, bg=C["border"], height=1).pack(fill="x")

        body = tk.Frame(self, bg=C["bg2"], padx=20, pady=16)
        body.pack(fill="both")

        self._vars = {}
        self._combos = {}

        for i, (label, default, ftype) in enumerate(fields):
            row = tk.Frame(body, bg=C["bg2"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, bg=C["bg2"], fg=C["text_dim"],
                     font=FONT_SM, width=18, anchor="w").pack(side="left")

            if ftype == "readonly":
                tk.Label(row, text=str(default or ""), bg=C["bg2"],
                         fg=C["text"], font=FONT_SM).pack(side="left")
                self._vars[label] = default
                continue

            if ftype.startswith("select:"):
                opts = ftype[7:].split(",")
                var  = tk.StringVar(value=str(default) if default else (opts[0] if opts else ""))
                cb   = ttk.Combobox(row, textvariable=var, values=opts,
                                    state="readonly", style="Dark.TCombobox",
                                    width=32, font=FONT_SM)
                cb.pack(side="left", fill="x", expand=True)
                self._vars[label]   = var
                self._combos[label] = cb
            else:
                var = tk.StringVar(value=str(default or ""))
                ent = DarkEntry(row, textvariable=var, width=36)
                ent.pack(side="left", fill="x", expand=True)
                self._vars[label] = var

        sep(self, "h").pack(fill="x")
        btn_row = tk.Frame(self, bg=C["bg2"], pady=12, padx=20)
        btn_row.pack(fill="x")
        DarkButton(btn_row, text="✓  Confirmar",
                   command=self._confirm).pack(side="right", padx=(8, 0))
        DangerButton(btn_row, text="✕  Cancelar",
                     command=self.destroy).pack(side="right")

        self._center(parent)
        self.bind("<Return>", lambda e: self._confirm())
        self.bind("<Escape>", lambda e: self.destroy())
        self.wait_window()

    def _center(self, parent):
        self.update_idletasks()
        pw = parent.winfo_rootx(); ph = parent.winfo_rooty()
        pw2 = parent.winfo_width(); ph2 = parent.winfo_height()
        dw  = self.winfo_width();  dh  = self.winfo_height()
        x   = pw + (pw2 - dw) // 2
        y   = ph + (ph2 - dh) // 2
        self.geometry(f"+{x}+{y}")

    def _confirm(self):
        self.result = {}
        for label, var in self._vars.items():
            if isinstance(var, tk.StringVar):
                self.result[label] = var.get().strip()
            else:
                self.result[label] = var
        self.destroy()


class CartDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Novo Pedido")
        self.configure(bg=C["bg2"])
        self.transient(parent)
        self.grab_set()
        self.geometry("960x640")
        self._cart  = []
        self._build()
        self._load_prods()
        self._center(parent)
        self.wait_window()

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        hdr = tk.Frame(self, bg=C["bg3"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="  ◉  NOVO PEDIDO", bg=C["bg3"], fg=C["green"],
                 font=FONT_TITLE, pady=8).pack(side="left")
        self._lbl_total = tk.Label(hdr, text="Total: R$ 0,00",
                                   bg=C["bg3"], fg=C["amber"], font=FONT_BOLD)
        self._lbl_total.pack(side="right", padx=12)
        sep(self, "h").pack(fill="x")

        paned = tk.PanedWindow(self, bg=C["bg"], orient="horizontal",
                               sashwidth=4, sashrelief="flat", sashpad=0)
        paned.pack(fill="both", expand=True)

        left = tk.Frame(paned, bg=C["bg2"])
        paned.add(left, minsize=380)

        tk.Label(left, text="  Produtos disponíveis", bg=C["bg3"],
                 fg=C["green"], font=FONT_BOLD, anchor="w", pady=6).pack(fill="x")
        sep(left, "h").pack(fill="x")

        sf = tk.Frame(left, bg=C["bg2"], pady=6, padx=8)
        sf.pack(fill="x")
        tk.Label(sf, text="Buscar:", bg=C["bg2"], fg=C["text_dim"],
                 font=FONT_SM).pack(side="left")
        self._search_var = tk.StringVar()
        se = DarkEntry(sf, textvariable=self._search_var, width=24)
        se.pack(side="left", padx=6)
        self._search_var.trace_add("write", lambda *_: self._filter_prods())

        frm_tree, self._prod_tree = make_tree(left, [
            ("sku",    "SKU",     90,  "w"),
            ("nome",   "Produto", 200, "w"),
            ("disp",   "Disp",   55,  "center"),
            ("preco",  "Preço",  100, "e"),
        ])
        frm_tree.pack(fill="both", expand=True, padx=8, pady=4)

        tk.Label(left, text="  Duplo clique para adicionar ao carrinho",
                 bg=C["bg2"], fg=C["text_dim"], font=FONT_SM,
                 anchor="w", pady=4).pack(fill="x")
        self._prod_tree.bind("<Double-1>", self._on_add_prod)

        right = tk.Frame(paned, bg=C["bg2"])
        paned.add(right, minsize=340)

        tk.Label(right, text="  Carrinho", bg=C["bg3"],
                 fg=C["green"], font=FONT_BOLD, anchor="w", pady=6).pack(fill="x")
        sep(right, "h").pack(fill="x")

        frm_cart, self._cart_tree = make_tree(right, [
            ("nome",   "Produto", 160, "w"),
            ("qtd",    "Qtd",     45,  "center"),
            ("unit",   "Unit",    90,  "e"),
            ("sub",    "Subtotal",90,  "e"),
        ])
        frm_cart.pack(fill="both", expand=True, padx=8, pady=4)

        ctrl = tk.Frame(right, bg=C["bg2"], pady=4, padx=8)
        ctrl.pack(fill="x")
        DangerButton(ctrl, text="✕ Remover item",
                     command=self._remove_item).pack(side="left")
        AmberButton(ctrl, text="✎ Editar qtd",
                    command=self._edit_qty).pack(side="left", padx=6)

        sep(right, "h").pack(fill="x")

        pf = tk.Frame(right, bg=C["bg2"], padx=10, pady=8)
        pf.pack(fill="x")

        def row2(lbl):
            r = tk.Frame(pf, bg=C["bg2"])
            r.pack(fill="x", pady=3)
            tk.Label(r, text=lbl, bg=C["bg2"], fg=C["text_dim"],
                     font=FONT_SM, width=12, anchor="w").pack(side="left")
            return r

        with conectar() as conn:
            clientes = conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()

        r = row2("Cliente:")
        self._cli_var = tk.StringVar(value="Sem cliente")
        cli_opts = ["Sem cliente"] + [c["nome"] for c in clientes]
        self._cli_list = clientes
        ttk.Combobox(r, textvariable=self._cli_var, values=cli_opts,
                     state="readonly", style="Dark.TCombobox",
                     width=22).pack(side="left")

        r2 = row2("Pagamento:")
        self._pgto_var = tk.StringVar(value="PIX")
        ttk.Combobox(r2, textvariable=self._pgto_var, values=FORMAS_PAGAMENTO,
                     state="readonly", style="Dark.TCombobox",
                     width=22).pack(side="left")

        r3 = row2("Desconto R$:")
        self._desc_var = tk.StringVar(value="0")
        DarkEntry(r3, textvariable=self._desc_var, width=12).pack(side="left")

        r4 = row2("Observação:")
        self._obs_var = tk.StringVar()
        DarkEntry(r4, textvariable=self._obs_var, width=22).pack(side="left")

        sep(right, "h").pack(fill="x")
        btn_row = tk.Frame(right, bg=C["bg2"], pady=8, padx=8)
        btn_row.pack(fill="x")
        DarkButton(btn_row, text="✓  Finalizar Pedido",
                   command=self._finalize,
                   bg=C["green3"], fg="#fff",
                   activebackground=C["green2"]).pack(side="right")
        DangerButton(btn_row, text="✕  Cancelar",
                     command=self.destroy).pack(side="right", padx=6)

        self.bind("<Escape>", lambda e: self.destroy())

    def _load_prods(self):
        with conectar() as conn:
            self._all_prods = conn.execute(
                "SELECT * FROM produtos WHERE ativo=1 AND estoque>0 ORDER BY nome"
            ).fetchall()
        self._filter_prods()

    def _filter_prods(self):
        q = self._search_var.get().lower()
        self._prod_tree.delete(*self._prod_tree.get_children())
        for p in self._all_prods:
            if q and q not in p["nome"].lower() and q not in (p["sku"] or "").lower():
                continue
            in_cart = sum(i["qtd"] for i in self._cart if i["produto"]["id"] == p["id"])
            disp    = p["estoque"] - in_cart
            if disp <= 0:          tag = "cancel"
            elif disp <= p["estoque_minimo"]: tag = "low"
            else:                  tag = "ok"
            self._prod_tree.insert("", "end",
                iid=str(p["id"]),
                values=(p["sku"] or "-", p["nome"], disp, fmtR(p["preco_venda"])),
                tags=(tag,))

    def _on_add_prod(self, event):
        sel = self._prod_tree.selection()
        if not sel: return
        pid  = int(sel[0])
        prod = next((p for p in self._all_prods if p["id"] == pid), None)
        if not prod: return
        in_cart = sum(i["qtd"] for i in self._cart if i["produto"]["id"] == pid)
        avail   = prod["estoque"] - in_cart
        if avail <= 0:
            messagebox.showwarning("Sem estoque", f"'{prod['nome']}' sem estoque disponível.",
                                   parent=self)
            return
        qty = simpledialog.askinteger("Quantidade",
            f"Qtd de '{prod['nome']}'\n(disponível: {avail})",
            parent=self, minvalue=1, maxvalue=avail)
        if not qty: return
        existing = next((i for i in self._cart if i["produto"]["id"] == pid), None)
        if existing:
            existing["qtd"]      = min(prod["estoque"], existing["qtd"] + qty)
            existing["subtotal"] = round(existing["qtd"] * existing["preco"], 2)
        else:
            self._cart.append({"produto": dict(prod), "qtd": qty,
                               "preco": prod["preco_venda"],
                               "subtotal": round(qty * prod["preco_venda"], 2)})
        self._refresh_cart()
        self._filter_prods()

    def _refresh_cart(self):
        self._cart_tree.delete(*self._cart_tree.get_children())
        total = 0
        for item in self._cart:
            self._cart_tree.insert("", "end", values=(
                item["produto"]["nome"][:22],
                item["qtd"],
                fmtR(item["preco"]),
                fmtR(item["subtotal"])
            ))
            total += item["subtotal"]
        self._lbl_total.config(text=f"Total: {fmtR(total)}")

    def _remove_item(self):
        sel = self._cart_tree.selection()
        if not sel: return
        idx = self._cart_tree.index(sel[0])
        if 0 <= idx < len(self._cart):
            self._cart.pop(idx)
        self._refresh_cart()
        self._filter_prods()

    def _edit_qty(self):
        sel = self._cart_tree.selection()
        if not sel: return
        idx  = self._cart_tree.index(sel[0])
        item = self._cart[idx]
        prod = item["produto"]
        qty  = simpledialog.askinteger("Quantidade",
            f"Nova qtd de '{prod['nome']}'",
            parent=self, minvalue=1, maxvalue=prod["estoque"])
        if qty:
            item["qtd"]      = qty
            item["subtotal"] = round(qty * item["preco"], 2)
        self._refresh_cart()
        self._filter_prods()

    def _finalize(self):
        if not self._cart:
            messagebox.showwarning("Carrinho vazio",
                "Adicione ao menos um produto.", parent=self)
            return
        cli_nome = self._cli_var.get()
        cli_id   = next((c["id"] for c in self._cli_list if c["nome"] == cli_nome), None)
        forma    = self._pgto_var.get()
        try:
            desc = max(0.0, float(self._desc_var.get().replace(",",".") or "0"))
        except: desc = 0.0
        obs  = self._obs_var.get().strip() or None
        sub  = sum(i["subtotal"] for i in self._cart)
        total = max(0.0, round(sub - desc, 2))
        msg = (f"Cliente  : {cli_nome}\n"
               f"Pagamento: {forma}\n"
               f"Subtotal : {fmtR(sub)}\n"
               f"Desconto : {fmtR(desc)}\n"
               f"TOTAL    : {fmtR(total)}")
        if not messagebox.askyesno("Confirmar Pedido?", msg, parent=self):
            return
        with conectar() as conn:
            cur = conn.execute(
                "INSERT INTO pedidos (cliente_id,forma_pagamento,total,desconto,observacao)"
                " VALUES (?,?,?,?,?)", (cli_id, forma, total, desc, obs))
            pid = cur.lastrowid
            for item in self._cart:
                conn.execute(
                    "INSERT INTO pedido_itens (pedido_id,produto_id,quantidade,"
                    "preco_unitario,subtotal) VALUES (?,?,?,?,?)",
                    (pid, item["produto"]["id"], item["qtd"],
                     item["preco"], item["subtotal"]))
                registrar_movimentacao(conn, item["produto"]["id"], "saida",
                                       item["qtd"], f"Pedido #{pid}")
                conn.execute("UPDATE produtos SET estoque=estoque-? WHERE id=?",
                             (item["qtd"], item["produto"]["id"]))
        self.result = pid
        self.destroy()


class EntradaDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Nova Entrada de Estoque")
        self.configure(bg=C["bg2"])
        self.transient(parent)
        self.grab_set()
        self.geometry("900x580")
        self._itens = []
        self._build()
        self._center(parent)
        self.wait_window()

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width()  - self.winfo_width())  // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        hdr = tk.Frame(self, bg=C["bg3"])
        hdr.pack(fill="x")
        tk.Label(hdr, text="  ▣  NOVA ENTRADA DE ESTOQUE", bg=C["bg3"],
                 fg=C["green"], font=FONT_TITLE, pady=8).pack(side="left")
        self._lbl_total = tk.Label(hdr, text="Total: R$ 0,00",
                                   bg=C["bg3"], fg=C["amber"], font=FONT_BOLD)
        self._lbl_total.pack(side="right", padx=12)
        sep(self, "h").pack(fill="x")

        paned = tk.PanedWindow(self, bg=C["bg"], orient="horizontal", sashwidth=4)
        paned.pack(fill="both", expand=True)

        left = tk.Frame(paned, bg=C["bg2"])
        paned.add(left, minsize=380)
        tk.Label(left, text="  Selecionar produto", bg=C["bg3"],
                 fg=C["green"], font=FONT_BOLD, anchor="w", pady=6).pack(fill="x")
        sep(left, "h").pack(fill="x")
        frm, self._prod_tree = make_tree(left, [
            ("sku",    "SKU",    80,  "w"),
            ("nome",   "Produto",220, "w"),
            ("estq",   "Estq",  50,  "center"),
            ("custo",  "Custo", 90,  "e"),
        ])
        frm.pack(fill="both", expand=True, padx=8, pady=6)
        with conectar() as conn:
            prods = conn.execute(
                "SELECT * FROM produtos WHERE ativo=1 ORDER BY nome").fetchall()
        for p in prods:
            self._prod_tree.insert("", "end", iid=str(p["id"]),
                values=(p["sku"] or "-", p["nome"], p["estoque"], fmtR(p["preco_custo"])),
                tags=("ok",))
        self._prods = prods
        tk.Label(left, text="  Duplo clique para adicionar",
                 bg=C["bg2"], fg=C["text_dim"], font=FONT_SM,
                 anchor="w", pady=4).pack(fill="x")
        self._prod_tree.bind("<Double-1>", self._add_item)

        right = tk.Frame(paned, bg=C["bg2"])
        paned.add(right, minsize=340)
        tk.Label(right, text="  Itens da entrada", bg=C["bg3"],
                 fg=C["green"], font=FONT_BOLD, anchor="w", pady=6).pack(fill="x")
        sep(right, "h").pack(fill="x")
        frm2, self._item_tree = make_tree(right, [
            ("nome",  "Produto",170, "w"),
            ("qtd",   "Qtd",    45,  "center"),
            ("preco", "Custo",  90,  "e"),
            ("sub",   "Subtotal",90, "e"),
        ])
        frm2.pack(fill="both", expand=True, padx=8, pady=6)
        ctrl = tk.Frame(right, bg=C["bg2"], pady=4, padx=8)
        ctrl.pack(fill="x")
        DangerButton(ctrl, text="✕ Remover", command=self._remove_item).pack(side="left")

        sep(right, "h").pack(fill="x")
        ff = tk.Frame(right, bg=C["bg2"], padx=10, pady=8)
        ff.pack(fill="x")
        with conectar() as conn:
            forns = conn.execute("SELECT * FROM fornecedores WHERE ativo=1 ORDER BY nome").fetchall()
        self._forn_list = forns
        self._forn_var  = tk.StringVar(value="Sem fornecedor")
        r = tk.Frame(ff, bg=C["bg2"]); r.pack(fill="x", pady=3)
        tk.Label(r, text="Fornecedor:", bg=C["bg2"], fg=C["text_dim"],
                 font=FONT_SM, width=12, anchor="w").pack(side="left")
        ttk.Combobox(r, textvariable=self._forn_var,
                     values=["Sem fornecedor"] + [f["nome"] for f in forns],
                     state="readonly", style="Dark.TCombobox", width=22).pack(side="left")
        r2 = tk.Frame(ff, bg=C["bg2"]); r2.pack(fill="x", pady=3)
        tk.Label(r2, text="Observação:", bg=C["bg2"], fg=C["text_dim"],
                 font=FONT_SM, width=12, anchor="w").pack(side="left")
        self._obs_var = tk.StringVar()
        DarkEntry(r2, textvariable=self._obs_var, width=22).pack(side="left")

        sep(right, "h").pack(fill="x")
        btn_row = tk.Frame(right, bg=C["bg2"], pady=8, padx=8)
        btn_row.pack(fill="x")
        DarkButton(btn_row, text="✓  Registrar Entrada",
                   command=self._save, bg=C["green3"], fg="#fff",
                   activebackground=C["green2"]).pack(side="right")
        DangerButton(btn_row, text="✕  Cancelar",
                     command=self.destroy).pack(side="right", padx=6)

    def _add_item(self, _event=None):
        sel = self._prod_tree.selection()
        if not sel: return
        pid  = int(sel[0])
        prod = next((p for p in self._prods if p["id"] == pid), None)
        if not prod: return
        qty = simpledialog.askinteger("Quantidade",
            f"Qtd de '{prod['nome']}':", parent=self, minvalue=1)
        if not qty: return
        default_custo = str(prod["preco_custo"]).replace(".", ",")
        custo_s = simpledialog.askstring("Preço de custo",
            f"Preço de custo p/ '{prod['nome']}':",
            parent=self, initialvalue=default_custo)
        try: custo = float((custo_s or default_custo).replace(",","."))
        except: custo = prod["preco_custo"]
        sub = round(qty * custo, 2)
        self._itens.append({"produto": dict(prod), "quantidade": qty,
                             "preco_unitario": custo, "subtotal": sub})
        self._refresh()

    def _remove_item(self):
        sel = self._item_tree.selection()
        if not sel: return
        idx = self._item_tree.index(sel[0])
        if 0 <= idx < len(self._itens):
            self._itens.pop(idx)
        self._refresh()

    def _refresh(self):
        self._item_tree.delete(*self._item_tree.get_children())
        total = 0
        for it in self._itens:
            self._item_tree.insert("", "end", values=(
                it["produto"]["nome"][:22], it["quantidade"],
                fmtR(it["preco_unitario"]), fmtR(it["subtotal"])))
            total += it["subtotal"]
        self._lbl_total.config(text=f"Total: {fmtR(total)}")

    def _save(self):
        if not self._itens:
            messagebox.showwarning("Sem itens", "Adicione ao menos um produto.", parent=self)
            return
        forn_nome = self._forn_var.get()
        forn_id   = next((f["id"] for f in self._forn_list if f["nome"] == forn_nome), None)
        total     = round(sum(i["subtotal"] for i in self._itens), 2)
        obs       = self._obs_var.get().strip() or None
        if not messagebox.askyesno("Confirmar Entrada",
            f"{len(self._itens)} produto(s)\nTotal: {fmtR(total)}", parent=self):
            return
        with conectar() as conn:
            cur = conn.execute(
                "INSERT INTO entradas (fornecedor_id,total,observacao) VALUES (?,?,?)",
                (forn_id, total, obs))
            eid = cur.lastrowid
            for it in self._itens:
                conn.execute(
                    "INSERT INTO entrada_itens (entrada_id,produto_id,quantidade,"
                    "preco_unitario,subtotal) VALUES (?,?,?,?,?)",
                    (eid, it["produto"]["id"], it["quantidade"],
                     it["preco_unitario"], it["subtotal"]))
                registrar_movimentacao(conn, it["produto"]["id"], "entrada",
                                       it["quantidade"], f"Entrada #{eid}")
                conn.execute("UPDATE produtos SET estoque=estoque+?, preco_custo=? WHERE id=?",
                             (it["quantidade"], it["preco_unitario"], it["produto"]["id"]))
        self.result = eid
        self.destroy()


# ═══════════════════════════════════════════════════════════════════
# PÁGINAS
# ═══════════════════════════════════════════════════════════════════

class PageBase(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["bg"])
        self.app = app

    def refresh(self): pass

    def _toolbar(self, parent, buttons):
        bar = tk.Frame(parent, bg=C["bg"], pady=8)
        bar.pack(fill="x")
        for item in buttons:
            if item is None or (isinstance(item, tuple) and item[0] is None):
                tk.Frame(bar, width=1, bg=C["border"]).pack(side="left", padx=6, fill="y")
                continue
            text = item[0]
            cmd  = item[1]
            cls  = item[2] if len(item) > 2 else DarkButton
            cls(bar, text=text, command=cmd).pack(side="left", padx=2)
        return bar

    def _flash(self, msg, color=None):
        self.app.flash(msg, color)

    def _tree_sel_id(self, tree):
        sel = tree.selection()
        if not sel: return None
        return tree.item(sel[0], "values")


class PageDashboard(PageBase):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()
        self.refresh()

    def _build(self):
        self._kpi_frame = tk.Frame(self, bg=C["bg"])
        self._kpi_frame.pack(fill="x", padx=12, pady=(12, 6))

        mid = tk.Frame(self, bg=C["bg"])
        mid.pack(fill="both", expand=True, padx=12, pady=6)

        c1, b1 = card(mid, "◉  Últimos Pedidos")
        c1.pack(side="left", fill="both", expand=True)
        frm1, self._ped_tree = make_tree(b1, [
            ("#",       "#",        40,  "center"),
            ("cliente", "Cliente",  160, "w"),
            ("total",   "Total",    100, "e"),
            ("forma",   "Pagamento",140, "w"),
            ("status",  "Status",   80,  "center"),
            ("data",    "Data",     110, "w"),
        ])
        frm1.pack(fill="both", expand=True)

        c2, b2 = card(mid, "⚠  Estoque Baixo")
        c2.pack(side="right", fill="both", padx=(8, 0), ipadx=4)
        frm2, self._alrt_tree = make_tree(b2, [
            ("sku",   "SKU",     80, "w"),
            ("nome",  "Produto", 180, "w"),
            ("estq",  "Estq",   50, "center"),
            ("min",   "Mín",    50, "center"),
        ])
        frm2.pack(fill="both", expand=True)

        bot = tk.Frame(self, bg=C["bg"])
        bot.pack(fill="x", padx=12, pady=(0, 10))
        c3, b3 = card(bot, "◈  Meta do Mês")
        c3.pack(fill="x")
        self._meta_row = b3

        self._after_id = None
        self._schedule_refresh()

    def _schedule_refresh(self):
        self.refresh()
        self._after_id = self.after(10000, self._schedule_refresh)

    def refresh(self):
        hoje = str(date.today()); mes = hoje[:7]
        with conectar() as conn:
            v_hoje = conn.execute(
                "SELECT COALESCE(SUM(total),0) t,COUNT(*) n FROM pedidos"
                " WHERE status='ativo' AND DATE(criado_em)=?", (hoje,)).fetchone()
            v_mes = conn.execute(
                "SELECT COALESCE(SUM(total),0) t,COUNT(*) n FROM pedidos"
                " WHERE status='ativo' AND strftime('%Y-%m',criado_em)=?", (mes,)).fetchone()
            e_baixo = conn.execute(
                "SELECT COUNT(*) FROM produtos WHERE ativo=1 AND estoque<=estoque_minimo").fetchone()[0]
            e_zero  = conn.execute(
                "SELECT COUNT(*) FROM produtos WHERE ativo=1 AND estoque=0").fetchone()[0]
            val_est = conn.execute(
                "SELECT COALESCE(SUM(preco_venda*estoque),0) FROM produtos WHERE ativo=1").fetchone()[0]
            n_clientes = conn.execute("SELECT COUNT(*) FROM clientes").fetchone()[0]
            ultimos = conn.execute("""
                SELECT p.id, COALESCE(c.nome,'(sem cliente)') cliente,
                       p.total, p.status, p.forma_pagamento, p.criado_em
                FROM pedidos p LEFT JOIN clientes c ON c.id=p.cliente_id
                ORDER BY p.id DESC LIMIT 10""").fetchall()
            alertas = conn.execute(
                "SELECT nome,sku,estoque,estoque_minimo FROM produtos"
                " WHERE ativo=1 AND estoque<=estoque_minimo ORDER BY estoque").fetchall()
            meta_r = conn.execute("SELECT valor_meta FROM metas WHERE mes=?", (mes,)).fetchone()

        for w in self._kpi_frame.winfo_children():
            w.destroy()
        kpis = [
            ("Receita Hoje",    fmtR(v_hoje["t"]),    f"{v_hoje['n']} pedido(s)",   C["green"]),
            ("Receita do Mês",  fmtR(v_mes["t"]),     f"{v_mes['n']} pedido(s)",    C["green"]),
            ("Estoque Baixo",   str(e_baixo),          f"{e_zero} sem estoque",      C["amber"] if e_baixo else C["green"]),
            ("Valor em Estoque",fmtR(val_est),         f"{n_clientes} clientes",     C["green"]),
        ]
        for title, val, sub, color in kpis:
            kf = tk.Frame(self._kpi_frame, bg=C["bg3"],
                          highlightbackground=C["border"], highlightthickness=1)
            kf.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(kf, text=title, bg=C["bg3"], fg=C["text_dim"],
                     font=FONT_SM, anchor="w", padx=12, pady=4).pack(fill="x")
            tk.Label(kf, text=val, bg=C["bg3"], fg=color,
                     font=FONT_XL, anchor="w", padx=12).pack(fill="x")
            tk.Label(kf, text=sub, bg=C["bg3"], fg=C["text_dim"],
                     font=FONT_SM, anchor="w", padx=12, pady=4).pack(fill="x")

        self._ped_tree.delete(*self._ped_tree.get_children())
        for r in ultimos:
            tag = {"ativo":"ok","cancelado":"cancel","devolvido":"dev"}.get(r["status"],"dim")
            self._ped_tree.insert("", "end", tags=(tag,), values=(
                f"#{r['id']}", r["cliente"], fmtR(r["total"]),
                r["forma_pagamento"], r["status"].upper(), r["criado_em"][:16]))

        self._alrt_tree.delete(*self._alrt_tree.get_children())
        for a in alertas:
            tag = "zero" if a["estoque"] == 0 else "low"
            self._alrt_tree.insert("", "end", tags=(tag,), values=(
                a["sku"] or "-", a["nome"], a["estoque"], a["estoque_minimo"]))

        for w in self._meta_row.winfo_children():
            w.destroy()
        if meta_r:
            meta_val = meta_r["valor_meta"]
            pct      = min(100.0, v_mes["t"] / meta_val * 100)
            row = tk.Frame(self._meta_row, bg=C["bg2"])
            row.pack(fill="x")
            tk.Label(row, text=f"Meta: {fmtR(meta_val)}",
                     bg=C["bg2"], fg=C["text_dim"], font=FONT_SM).pack(side="left")
            tk.Label(row, text=f"Realizado: {fmtR(v_mes['t'])}  ({pct:.1f}%)",
                     bg=C["bg2"], fg=C["green"] if pct >= 100 else C["amber"],
                     font=FONT_BOLD).pack(side="left", padx=20)
            bar_frame = tk.Frame(self._meta_row, bg=C["bg2"])
            bar_frame.pack(fill="x", pady=4)
            cv = tk.Canvas(bar_frame, height=12, bg=C["bg3"], highlightthickness=0)
            cv.pack(fill="x")
            cv.update_idletasks()
            w_cv = cv.winfo_width() or 400
            filled = int(w_cv * pct / 100)
            cv.create_rectangle(0, 0, filled, 12,
                                 fill=C["green"] if pct < 100 else C["amber"], outline="")
        else:
            tk.Label(self._meta_row, text="Nenhuma meta definida para este mês.",
                     bg=C["bg2"], fg=C["text_dim"], font=FONT_SM).pack(side="left")
            DarkButton(self._meta_row, text="+ Definir Meta",
                       command=lambda: self.app.goto("relatorios")).pack(side="left", padx=10)


class PagePedidos(PageBase):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        self._toolbar(self, [
            ("+ Novo Pedido",     self._novo),
            ("🔍 Ver Detalhes",    self._ver),
            (None,),
            ("✕ Cancelar Pedido", self._cancelar, DangerButton),
        ])
        ff = tk.Frame(self, bg=C["bg"])
        ff.pack(fill="x", padx=4, pady=(0, 6))
        tk.Label(ff, text="Filtro:", bg=C["bg"], fg=C["text_dim"], font=FONT_SM).pack(side="left", padx=(8,4))
        self._filtro_var = tk.StringVar(value="todos")
        for val, lbl in [("todos","Todos"),("ativo","Ativos"),
                         ("cancelado","Cancelados"),("devolvido","Devolvidos")]:
            rb = tk.Radiobutton(ff, text=lbl, variable=self._filtro_var,
                                value=val, bg=C["bg"], fg=C["text_dim"],
                                selectcolor=C["bg3"], activebackground=C["bg"],
                                activeforeground=C["green"],
                                indicatoron=True, font=FONT_SM,
                                command=self.refresh, cursor="hand2")
            rb.pack(side="left", padx=4)

        c, b = card(self, "◉  Pedidos")
        c.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        frm, self._tree = make_tree(b, [
            ("#",         "#",          50,  "center"),
            ("cliente",   "Cliente",    180, "w"),
            ("itens",     "Itens",      50,  "center"),
            ("total",     "Total",      110, "e"),
            ("pagamento", "Pagamento",  160, "w"),
            ("data",      "Data",       130, "w"),
            ("status",    "Status",     90,  "center"),
        ])
        frm.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", lambda e: self._ver())
        self.refresh()

    def refresh(self):
        filtro = self._filtro_var.get()
        with conectar() as conn:
            if filtro == "todos":
                rows = conn.execute("""
                    SELECT p.id, COALESCE(c.nome,'(sem cliente)') cli,
                           p.total, p.status, p.forma_pagamento, p.criado_em,
                           COUNT(pi.id) itens
                    FROM pedidos p LEFT JOIN clientes c ON c.id=p.cliente_id
                    LEFT JOIN pedido_itens pi ON pi.pedido_id=p.id
                    GROUP BY p.id ORDER BY p.id DESC""").fetchall()
            else:
                rows = conn.execute("""
                    SELECT p.id, COALESCE(c.nome,'(sem cliente)') cli,
                           p.total, p.status, p.forma_pagamento, p.criado_em,
                           COUNT(pi.id) itens
                    FROM pedidos p LEFT JOIN clientes c ON c.id=p.cliente_id
                    LEFT JOIN pedido_itens pi ON pi.pedido_id=p.id
                    WHERE p.status=? GROUP BY p.id ORDER BY p.id DESC
                """, (filtro,)).fetchall()
        self._tree.delete(*self._tree.get_children())
        for r in rows:
            tag = {"ativo":"ok","cancelado":"cancel","devolvido":"dev"}.get(r["status"],"dim")
            self._tree.insert("", "end", iid=str(r["id"]), tags=(tag,), values=(
                f"#{r['id']}", r["cli"], r["itens"], fmtR(r["total"]),
                r["forma_pagamento"], r["criado_em"][:16], r["status"].upper()))

    def _selected_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selecione", "Clique em um pedido primeiro.", parent=self)
            return None
        return int(sel[0])

    def _novo(self):
        dlg = CartDialog(self)
        if dlg.result:
            self._flash(f"✓  Pedido #{dlg.result} registrado!", C["green"])
            self.refresh()

    def _ver(self):
        pid = self._selected_id()
        if not pid: return
        with conectar() as conn:
            ped = conn.execute("""
                SELECT p.*, COALESCE(c.nome,'(sem cliente)') cli
                FROM pedidos p LEFT JOIN clientes c ON c.id=p.cliente_id WHERE p.id=?
            """, (pid,)).fetchone()
            itens = conn.execute("""
                SELECT pi.*, pr.nome pnome, pr.sku
                FROM pedido_itens pi JOIN produtos pr ON pr.id=pi.produto_id
                WHERE pi.pedido_id=?""", (pid,)).fetchall()
        if not ped: return

        top = tk.Toplevel(self)
        top.title(f"Pedido #{pid}")
        top.configure(bg=C["bg2"])
        top.transient(self)
        top.grab_set()
        top.geometry("560x460")

        hdr = tk.Frame(top, bg=C["bg3"])
        hdr.pack(fill="x")
        st = ped["status"].upper()
        color = C["green"] if st == "ATIVO" else C["red"] if st == "CANCELADO" else C["amber"]
        tk.Label(hdr, text=f"  Pedido #{pid}  —  {st}",
                 bg=C["bg3"], fg=color, font=FONT_TITLE, pady=8).pack(side="left")
        sep(top, "h").pack(fill="x")

        info = tk.Frame(top, bg=C["bg2"], padx=16, pady=10)
        info.pack(fill="x")
        for lbl, val in [("Cliente", ped["cli"]),
                         ("Pagamento", ped["forma_pagamento"]),
                         ("Data", ped["criado_em"]),
                         ("Observação", ped["observacao"] or "-")]:
            r = tk.Frame(info, bg=C["bg2"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"{lbl}:", bg=C["bg2"], fg=C["text_dim"],
                     font=FONT_SM, width=12, anchor="w").pack(side="left")
            tk.Label(r, text=val, bg=C["bg2"], fg=C["text"],
                     font=FONT_SM, anchor="w").pack(side="left")

        sep(top, "h").pack(fill="x")
        frm, tree = make_tree(top, [
            ("sku",  "SKU",    80,  "w"),
            ("nome", "Produto",200, "w"),
            ("qtd",  "Qtd",    50,  "center"),
            ("unit", "Unit",   100, "e"),
            ("sub",  "Subtot", 100, "e"),
        ])
        frm.pack(fill="both", expand=True, padx=12, pady=8)
        for i in itens:
            tree.insert("", "end", values=(i["sku"] or "-", i["pnome"],
                i["quantidade"], fmtR(i["preco_unitario"]), fmtR(i["subtotal"])))

        sep(top, "h").pack(fill="x")
        bot = tk.Frame(top, bg=C["bg2"], padx=16, pady=10)
        bot.pack(fill="x")
        if ped["desconto"] > 0:
            tk.Label(bot, text=f"Desconto: {fmtR(ped['desconto'])}",
                     bg=C["bg2"], fg=C["amber"], font=FONT_SM).pack(side="left")
        tk.Label(bot, text=f"TOTAL: {fmtR(ped['total'])}",
                 bg=C["bg2"], fg=C["green"], font=FONT_BOLD).pack(side="right")
        DarkButton(top, text="Fechar", command=top.destroy).pack(pady=6)

    def _cancelar(self):
        pid = self._selected_id()
        if not pid: return
        with conectar() as conn:
            ped = conn.execute("SELECT * FROM pedidos WHERE id=? AND status='ativo'",
                               (pid,)).fetchone()
        if not ped:
            messagebox.showerror("Erro", "Pedido não encontrado ou não está ativo.", parent=self)
            return
        if not messagebox.askyesno("Cancelar Pedido",
            f"Cancelar Pedido #{pid} e restaurar estoque?", parent=self):
            return
        with conectar() as conn:
            conn.execute("UPDATE pedidos SET status='cancelado' WHERE id=?", (pid,))
            itens = conn.execute("SELECT * FROM pedido_itens WHERE pedido_id=?",
                                 (pid,)).fetchall()
            for it in itens:
                qtd_r = it["quantidade"] - it["devolvido"]
                if qtd_r > 0:
                    registrar_movimentacao(conn, it["produto_id"], "cancelamento",
                                           qtd_r, f"Cancelamento #{pid}")
                    conn.execute("UPDATE produtos SET estoque=estoque+? WHERE id=?",
                                 (qtd_r, it["produto_id"]))
        self._flash(f"⚠  Pedido #{pid} cancelado.", C["amber"])
        self.refresh()


class PageEstoque(PageBase):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        self._toolbar(self, [
            ("+ Nova Entrada",    self._nova_entrada),
            ("✎ Ajuste Manual",  self._ajuste),
            (None,),
            ("📋 Movimentações",  self._movimentacoes),
        ])
        c, b = card(self, "▣  Posição de Estoque")
        c.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        frm, self._tree = make_tree(b, [
            ("sku",    "SKU",      80,  "w"),
            ("nome",   "Produto",  210, "w"),
            ("cat",    "Categoria",120, "w"),
            ("estq",   "Estoque",  70,  "center"),
            ("min",    "Mínimo",   60,  "center"),
            ("pvenda", "Vl.Venda", 120, "e"),
            ("pcusto", "Vl.Custo", 120, "e"),
            ("status", "Status",   80,  "center"),
        ])
        frm.pack(fill="both", expand=True)

        self._lbl_totais = tk.Label(b, text="", bg=C["bg2"], fg=C["text_dim"], font=FONT_SM)
        self._lbl_totais.pack(anchor="e", pady=4)
        self.refresh()

    def refresh(self):
        with conectar() as conn:
            prods = conn.execute("""
                SELECT p.*, COALESCE(cat.nome,'-') cat
                FROM produtos p
                LEFT JOIN categorias cat ON cat.id=p.categoria_id
                WHERE p.ativo=1 ORDER BY p.nome""").fetchall()
        self._tree.delete(*self._tree.get_children())
        tot_v = tot_c = 0
        for p in prods:
            vv = p["preco_venda"] * p["estoque"]
            vc = p["preco_custo"] * p["estoque"]
            tot_v += vv; tot_c += vc
            if p["estoque"] == 0:    tag, st = "zero", "ZERO"
            elif p["estoque"] <= p["estoque_minimo"]: tag, st = "low", "BAIXO"
            else:                    tag, st = "ok",   "OK"
            self._tree.insert("", "end", tags=(tag,), values=(
                p["sku"] or "-", p["nome"], p["cat"],
                p["estoque"], p["estoque_minimo"],
                fmtR(vv), fmtR(vc), st))
        marg = (tot_v - tot_c) / tot_v * 100 if tot_v else 0
        self._lbl_totais.config(
            text=f"Total Venda: {fmtR(tot_v)}   Total Custo: {fmtR(tot_c)}   Margem: {marg:.1f}%")

    def _nova_entrada(self):
        dlg = EntradaDialog(self)
        if dlg.result:
            self._flash(f"✓  Entrada #{dlg.result} registrada!", C["green"])
            self.refresh()

    def _ajuste(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selecione", "Clique em um produto primeiro.", parent=self)
            return
        vals = self._tree.item(sel[0], "values")
        nome = vals[1]; estq_atual = int(vals[3])
        novo = simpledialog.askinteger("Ajuste de Estoque",
            f"Produto: {nome}\nEstoque atual: {estq_atual}\nNovo estoque:",
            parent=self, minvalue=0)
        if novo is None: return
        with conectar() as conn:
            prod = conn.execute(
                "SELECT id FROM produtos WHERE nome=? AND ativo=1", (nome,)).fetchone()
            if not prod: return
            diff = novo - estq_atual
            tipo = "ajuste_adicao" if diff >= 0 else "ajuste_reducao"
            registrar_movimentacao(conn, prod["id"], tipo, abs(diff), "Ajuste manual")
            conn.execute("UPDATE produtos SET estoque=? WHERE id=?", (novo, prod["id"]))
        self._flash(f"✓  {nome}: {estq_atual} → {novo}", C["green"])
        self.refresh()

    def _movimentacoes(self):
        with conectar() as conn:
            rows = conn.execute("""
                SELECT m.id, pr.nome pnome, m.tipo, m.quantidade,
                       m.estoque_ant, m.estoque_pos, m.referencia, m.criado_em
                FROM movimentacoes m JOIN produtos pr ON pr.id=m.produto_id
                ORDER BY m.id DESC LIMIT 300""").fetchall()

        top = tk.Toplevel(self)
        top.title("Log de Movimentações")
        top.configure(bg=C["bg2"])
        top.transient(self)
        top.geometry("900x500")
        frm, tree = make_tree(top, [
            ("id",    "#",         50,  "center"),
            ("prod",  "Produto",   200, "w"),
            ("tipo",  "Tipo",      120, "w"),
            ("qtd",   "Qtd",       50,  "center"),
            ("ant",   "Antes",     60,  "center"),
            ("pos",   "Depois",    60,  "center"),
            ("ref",   "Referência",160, "w"),
            ("data",  "Data",      120, "w"),
        ])
        frm.pack(fill="both", expand=True, padx=8, pady=8)
        for r in rows:
            tag = "ok" if r["tipo"] == "entrada" else ("cancel" if r["tipo"] == "saida" else "dev")
            tree.insert("", "end", tags=(tag,), values=(
                r["id"], r["pnome"], r["tipo"], r["quantidade"],
                r["estoque_ant"], r["estoque_pos"],
                r["referencia"] or "-", r["criado_em"][:16]))
        DarkButton(top, text="Fechar", command=top.destroy).pack(pady=6)


class PageProdutos(PageBase):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)

        tab_prods = tk.Frame(tabs, bg=C["bg"])
        tabs.add(tab_prods, text="  Produtos  ")
        self._build_prods_tab(tab_prods)

        tab_cats = tk.Frame(tabs, bg=C["bg"])
        tabs.add(tab_cats, text="  Categorias  ")
        self._build_cats_tab(tab_cats)

        tab_forn = tk.Frame(tabs, bg=C["bg"])
        tabs.add(tab_forn, text="  Fornecedores  ")
        self._build_forn_tab(tab_forn)

        style = ttk.Style()
        style.configure("TNotebook", background=C["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=C["bg3"], foreground=C["text_dim"],
                        padding=[12, 6], font=FONT_SM)
        style.map("TNotebook.Tab",
            background=[("selected", C["bg2"])],
            foreground=[("selected", C["green"])])

    def _build_prods_tab(self, parent):
        top = tk.Frame(parent, bg=C["bg"])
        top.pack(fill="x", pady=6, padx=4)
        DarkButton(top, text="+ Novo",    command=self._novo_prod).pack(side="left", padx=2)
        DarkButton(top, text="✎ Editar",  command=self._edit_prod).pack(side="left", padx=2)
        AmberButton(top, text="⏻ Ativar/Desativar", command=self._toggle_prod).pack(side="left", padx=2)

        tk.Label(top, text="Buscar:", bg=C["bg"], fg=C["text_dim"],
                 font=FONT_SM).pack(side="left", padx=(16,4))
        self._search = tk.StringVar()
        DarkEntry(top, textvariable=self._search, width=22).pack(side="left")
        self._search.trace_add("write", lambda *_: self.refresh())

        c, b = card(parent)
        c.pack(fill="both", expand=True)
        frm, self._prod_tree = make_tree(b, [
            ("id",    "ID",        45,  "center"),
            ("sku",   "SKU",       80,  "w"),
            ("nome",  "Produto",   220, "w"),
            ("cat",   "Categoria", 120, "w"),
            ("forn",  "Fornecedor",150, "w"),
            ("venda", "Venda",     100, "e"),
            ("custo", "Custo",     100, "e"),
            ("estq",  "Estoque",   70,  "center"),
            ("ativo", "Ativo",     55,  "center"),
        ])
        frm.pack(fill="both", expand=True)
        self._prod_tree.bind("<Double-1>", lambda e: self._edit_prod())
        self.refresh()

    def _build_cats_tab(self, parent):
        top = tk.Frame(parent, bg=C["bg"])
        top.pack(fill="x", pady=6, padx=4)
        DarkButton(top, text="+ Nova Categoria", command=self._nova_cat).pack(side="left", padx=2)
        DarkButton(top, text="✎ Editar",         command=self._edit_cat).pack(side="left", padx=2)

        c, b = card(parent)
        c.pack(fill="both", expand=True)
        frm, self._cat_tree = make_tree(b, [
            ("id",   "ID",         40,  "center"),
            ("nome", "Nome",       200, "w"),
            ("desc", "Descrição",  400, "w"),
        ])
        frm.pack(fill="both", expand=True)
        self._cat_tree.bind("<Double-1>", lambda e: self._edit_cat())
        self._refresh_cats()

    def _build_forn_tab(self, parent):
        top = tk.Frame(parent, bg=C["bg"])
        top.pack(fill="x", pady=6, padx=4)
        DarkButton(top, text="+ Novo Fornecedor", command=self._novo_forn).pack(side="left", padx=2)
        DarkButton(top, text="✎ Editar",          command=self._edit_forn).pack(side="left", padx=2)
        AmberButton(top, text="⏻ Ativar/Desativar", command=self._toggle_forn).pack(side="left", padx=2)

        c, b = card(parent)
        c.pack(fill="both", expand=True)
        frm, self._forn_tree = make_tree(b, [
            ("id",    "ID",       40,  "center"),
            ("nome",  "Nome",     200, "w"),
            ("email", "Email",    200, "w"),
            ("tel",   "Telefone", 140, "w"),
            ("ativo", "Status",   70,  "center"),
        ])
        frm.pack(fill="both", expand=True)
        self._forn_tree.bind("<Double-1>", lambda e: self._edit_forn())
        self._refresh_forn()

    def refresh(self):
        q = self._search.get().lower() if hasattr(self, "_search") else ""
        with conectar() as conn:
            prods = conn.execute("""
                SELECT p.*, COALESCE(cat.nome,'-') cat, COALESCE(f.nome,'-') forn
                FROM produtos p
                LEFT JOIN categorias cat ON cat.id=p.categoria_id
                LEFT JOIN fornecedores f ON f.id=p.fornecedor_id
                ORDER BY p.nome""").fetchall()
        self._prod_tree.delete(*self._prod_tree.get_children())
        for p in prods:
            if q and q not in p["nome"].lower() and q not in (p["sku"] or "").lower():
                continue
            tag = "cancel" if not p["ativo"] else \
                  ("zero" if p["estoque"] == 0 else \
                  ("low" if p["estoque"] <= p["estoque_minimo"] else "ok"))
            self._prod_tree.insert("", "end", iid=str(p["id"]), tags=(tag,), values=(
                p["id"], p["sku"] or "-", p["nome"], p["cat"], p["forn"],
                fmtR(p["preco_venda"]), fmtR(p["preco_custo"]),
                p["estoque"], "Sim" if p["ativo"] else "Não"))

    def _refresh_cats(self):
        with conectar() as conn:
            cats = conn.execute("SELECT * FROM categorias ORDER BY nome").fetchall()
        self._cat_tree.delete(*self._cat_tree.get_children())
        for c in cats:
            self._cat_tree.insert("", "end", iid=str(c["id"]), values=(
                c["id"], c["nome"], c["descricao"] or ""))

    def _refresh_forn(self):
        with conectar() as conn:
            forns = conn.execute("SELECT * FROM fornecedores ORDER BY nome").fetchall()
        self._forn_tree.delete(*self._forn_tree.get_children())
        for f in forns:
            tag = "ok" if f["ativo"] else "cancel"
            self._forn_tree.insert("", "end", iid=str(f["id"]), tags=(tag,), values=(
                f["id"], f["nome"], f["email"] or "-",
                f["telefone"] or "-", "Ativo" if f["ativo"] else "Inativo"))

    def _get_cats_forn(self):
        with conectar() as conn:
            cats  = conn.execute("SELECT * FROM categorias ORDER BY nome").fetchall()
            forns = conn.execute("SELECT * FROM fornecedores WHERE ativo=1 ORDER BY nome").fetchall()
        return cats, forns

    def _novo_prod(self):
        cats, forns = self._get_cats_forn()
        cat_opts  = ",".join(c["nome"] for c in cats)  or "Sem categoria"
        forn_opts = ",".join(f["nome"] for f in forns) or "Sem fornecedor"
        d = FormDialog(self, "Novo Produto", [
            ("Nome",            "",    "str"),
            ("SKU",             "",    "str"),
            ("Preço de venda",  "0",   "str"),
            ("Preço de custo",  "0",   "str"),
            ("Estoque inicial", "0",   "str"),
            ("Estoque mínimo",  "5",   "str"),
            ("Categoria",       cats[0]["nome"] if cats else "", f"select:{cat_opts}"),
            ("Fornecedor",      forns[0]["nome"] if forns else "", f"select:{forn_opts}"),
        ])
        if not d.result: return
        try:
            pv  = float(d.result["Preço de venda"].replace(",","."))
            pc  = float(d.result["Preço de custo"].replace(",","."))
            est = int(d.result["Estoque inicial"])
            em  = int(d.result["Estoque mínimo"])
        except:
            messagebox.showerror("Erro", "Valores numéricos inválidos.", parent=self); return
        cat_id  = next((c["id"] for c in cats  if c["nome"]  == d.result["Categoria"]),  None)
        forn_id = next((f["id"] for f in forns if f["nome"] == d.result["Fornecedor"]), None)
        try:
            with conectar() as conn:
                cur = conn.execute(
                    "INSERT INTO produtos (nome,sku,preco_venda,preco_custo,estoque,"
                    "estoque_minimo,categoria_id,fornecedor_id) VALUES (?,?,?,?,?,?,?,?)",
                    (d.result["Nome"], d.result["SKU"] or None, pv, pc, est, em,
                     cat_id, forn_id))
                if est > 0:
                    registrar_movimentacao(conn, cur.lastrowid, "entrada", est, "Estoque inicial")
            self._flash(f"✓  Produto '{d.result['Nome']}' cadastrado!", C["green"])
            self.refresh()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "SKU já existe.", parent=self)

    def _edit_prod(self):
        sel = self._prod_tree.selection()
        if not sel:
            messagebox.showinfo("Selecione", "Clique em um produto.", parent=self); return
        pid = int(sel[0])
        with conectar() as conn:
            p = conn.execute("SELECT * FROM produtos WHERE id=?", (pid,)).fetchone()
        cats, forns = self._get_cats_forn()
        cat_opts  = ",".join(c["nome"] for c in cats)  or "Sem categoria"
        forn_opts = ",".join(f["nome"] for f in forns) or "Sem fornecedor"
        cat_def   = next((c["nome"] for c in cats  if c["id"] == p["categoria_id"]),  "")
        forn_def  = next((f["nome"] for f in forns if f["id"] == p["fornecedor_id"]), "")
        d = FormDialog(self, "Editar Produto", [
            ("Nome",           p["nome"],                "str"),
            ("SKU",            p["sku"] or "",           "str"),
            ("Preço de venda", str(p["preco_venda"]),    "str"),
            ("Preço de custo", str(p["preco_custo"]),    "str"),
            ("Estoque mínimo", str(p["estoque_minimo"]), "str"),
            ("Categoria",      cat_def,  f"select:{cat_opts}"),
            ("Fornecedor",     forn_def, f"select:{forn_opts}"),
        ])
        if not d.result: return
        try:
            pv = float(d.result["Preço de venda"].replace(",","."))
            pc = float(d.result["Preço de custo"].replace(",","."))
            em = int(d.result["Estoque mínimo"])
        except:
            messagebox.showerror("Erro", "Valores numéricos inválidos.", parent=self); return
        cat_id  = next((c["id"] for c in cats  if c["nome"]  == d.result["Categoria"]),  None)
        forn_id = next((f["id"] for f in forns if f["nome"] == d.result["Fornecedor"]), None)
        with conectar() as conn:
            conn.execute(
                "UPDATE produtos SET nome=?,sku=?,preco_venda=?,preco_custo=?,"
                "estoque_minimo=?,categoria_id=?,fornecedor_id=? WHERE id=?",
                (d.result["Nome"], d.result["SKU"] or None, pv, pc, em,
                 cat_id, forn_id, pid))
        self._flash(f"✓  Produto atualizado!", C["green"])
        self.refresh()

    def _toggle_prod(self):
        sel = self._prod_tree.selection()
        if not sel:
            messagebox.showinfo("Selecione", "Clique em um produto.", parent=self); return
        pid = int(sel[0])
        with conectar() as conn:
            p = conn.execute("SELECT nome,ativo FROM produtos WHERE id=?", (pid,)).fetchone()
            novo = 0 if p["ativo"] else 1
            conn.execute("UPDATE produtos SET ativo=? WHERE id=?", (novo, pid))
        self._flash(f"{'✓' if novo else '⚠'}  '{p['nome']}' {'ativado' if novo else 'desativado'}.")
        self.refresh()

    def _nova_cat(self):
        d = FormDialog(self, "Nova Categoria", [
            ("Nome",      "", "str"),
            ("Descrição", "", "str"),
        ])
        if not d.result or not d.result["Nome"]: return
        try:
            with conectar() as conn:
                conn.execute("INSERT INTO categorias (nome,descricao) VALUES (?,?)",
                             (d.result["Nome"], d.result["Descrição"] or None))
            self._flash(f"✓  Categoria '{d.result['Nome']}' criada!", C["green"])
            self._refresh_cats()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Categoria já existe.", parent=self)

    def _edit_cat(self):
        sel = self._cat_tree.selection()
        if not sel: return
        cid = int(sel[0])
        with conectar() as conn:
            c = conn.execute("SELECT * FROM categorias WHERE id=?", (cid,)).fetchone()
        d = FormDialog(self, "Editar Categoria", [
            ("Nome",      c["nome"],           "str"),
            ("Descrição", c["descricao"] or "", "str"),
        ])
        if not d.result: return
        with conectar() as conn:
            conn.execute("UPDATE categorias SET nome=?,descricao=? WHERE id=?",
                         (d.result["Nome"], d.result["Descrição"] or None, cid))
        self._flash("✓  Categoria atualizada!", C["green"])
        self._refresh_cats()

    def _novo_forn(self):
        d = FormDialog(self, "Novo Fornecedor", [
            ("Nome",     "", "str"),
            ("Email",    "", "str"),
            ("Telefone", "", "str"),
        ])
        if not d.result or not d.result["Nome"]: return
        with conectar() as conn:
            conn.execute("INSERT INTO fornecedores (nome,email,telefone) VALUES (?,?,?)",
                         (d.result["Nome"], d.result["Email"] or None,
                          d.result["Telefone"] or None))
        self._flash(f"✓  Fornecedor '{d.result['Nome']}' criado!", C["green"])
        self._refresh_forn()

    def _edit_forn(self):
        sel = self._forn_tree.selection()
        if not sel: return
        fid = int(sel[0])
        with conectar() as conn:
            f = conn.execute("SELECT * FROM fornecedores WHERE id=?", (fid,)).fetchone()
        d = FormDialog(self, "Editar Fornecedor", [
            ("Nome",     f["nome"],           "str"),
            ("Email",    f["email"] or "",    "str"),
            ("Telefone", f["telefone"] or "", "str"),
        ])
        if not d.result: return
        with conectar() as conn:
            conn.execute("UPDATE fornecedores SET nome=?,email=?,telefone=? WHERE id=?",
                         (d.result["Nome"], d.result["Email"] or None,
                          d.result["Telefone"] or None, fid))
        self._flash("✓  Fornecedor atualizado!", C["green"])
        self._refresh_forn()

    def _toggle_forn(self):
        sel = self._forn_tree.selection()
        if not sel: return
        fid = int(sel[0])
        with conectar() as conn:
            f = conn.execute("SELECT nome,ativo FROM fornecedores WHERE id=?", (fid,)).fetchone()
            novo = 0 if f["ativo"] else 1
            conn.execute("UPDATE fornecedores SET ativo=? WHERE id=?", (novo, fid))
        self._flash(f"{'✓' if novo else '⚠'}  Fornecedor {'ativado' if novo else 'desativado'}.")
        self._refresh_forn()


class PageClientes(PageBase):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        self._toolbar(self, [
            ("+ Novo Cliente",    self._novo),
            ("✎ Editar",          self._editar),
            ("📋 Histórico",       self._historico),
            (None,),
            ("✕ Excluir",         self._excluir, DangerButton),
        ])
        c, b = card(self, "◍  Clientes")
        c.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        frm, self._tree = make_tree(b, [
            ("id",    "ID",       45,  "center"),
            ("nome",  "Nome",     200, "w"),
            ("email", "Email",    200, "w"),
            ("tel",   "Telefone", 140, "w"),
            ("doc",   "CPF/CNPJ", 130, "w"),
            ("desde", "Desde",   100, "w"),
        ])
        frm.pack(fill="both", expand=True)
        self._tree.bind("<Double-1>", lambda e: self._editar())
        self.refresh()

    def refresh(self):
        with conectar() as conn:
            clientes = conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()
        self._tree.delete(*self._tree.get_children())
        for c in clientes:
            self._tree.insert("", "end", iid=str(c["id"]), values=(
                c["id"], c["nome"], c["email"] or "-",
                c["telefone"] or "-", c["cpf_cnpj"] or "-",
                c["criado_em"][:10]))

    def _fields(self, c=None):
        return [
            ("Nome",     c["nome"]          if c else "", "str"),
            ("Email",    c["email"]  or ""  if c else "", "str"),
            ("Telefone", c["telefone"] or "" if c else "", "str"),
            ("Endereço", c["endereco"] or "" if c else "", "str"),
            ("CPF/CNPJ", c["cpf_cnpj"] or "" if c else "", "str"),
        ]

    def _novo(self):
        d = FormDialog(self, "Novo Cliente", self._fields())
        if not d.result or not d.result["Nome"]: return
        try:
            with conectar() as conn:
                conn.execute(
                    "INSERT INTO clientes (nome,email,telefone,endereco,cpf_cnpj) VALUES (?,?,?,?,?)",
                    (d.result["Nome"], d.result["Email"] or None,
                     d.result["Telefone"] or None, d.result["Endereço"] or None,
                     d.result["CPF/CNPJ"] or None))
            self._flash(f"✓  Cliente '{d.result['Nome']}' cadastrado!", C["green"])
            self.refresh()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Email já está em uso.", parent=self)

    def _editar(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selecione", "Clique em um cliente.", parent=self); return
        cid = int(sel[0])
        with conectar() as conn:
            c = conn.execute("SELECT * FROM clientes WHERE id=?", (cid,)).fetchone()
        d = FormDialog(self, "Editar Cliente", self._fields(c))
        if not d.result: return
        try:
            with conectar() as conn:
                conn.execute(
                    "UPDATE clientes SET nome=?,email=?,telefone=?,endereco=?,cpf_cnpj=? WHERE id=?",
                    (d.result["Nome"], d.result["Email"] or None,
                     d.result["Telefone"] or None, d.result["Endereço"] or None,
                     d.result["CPF/CNPJ"] or None, cid))
            self._flash("✓  Cliente atualizado!", C["green"])
            self.refresh()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro", "Email já está em uso.", parent=self)

    def _excluir(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selecione", "Clique em um cliente.", parent=self); return
        cid = int(sel[0])
        with conectar() as conn:
            n = conn.execute("SELECT COUNT(*) FROM pedidos WHERE cliente_id=? AND status='ativo'",
                             (cid,)).fetchone()[0]
            nome = conn.execute("SELECT nome FROM clientes WHERE id=?", (cid,)).fetchone()["nome"]
        if n > 0:
            messagebox.showwarning("Não permitido",
                f"'{nome}' tem {n} pedido(s) ativo(s). Cancele antes.", parent=self)
            return
        if messagebox.askyesno("Excluir Cliente", f"Excluir '{nome}'?", parent=self):
            with conectar() as conn:
                conn.execute("DELETE FROM clientes WHERE id=?", (cid,))
            self._flash(f"⚠  Cliente '{nome}' excluído.", C["amber"])
            self.refresh()

    def _historico(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showinfo("Selecione", "Clique em um cliente.", parent=self); return
        cid = int(sel[0])
        with conectar() as conn:
            c = conn.execute("SELECT * FROM clientes WHERE id=?", (cid,)).fetchone()
            peds = conn.execute("""
                SELECT p.id, p.total, p.forma_pagamento, p.status, p.criado_em,
                       COUNT(pi.id) itens
                FROM pedidos p LEFT JOIN pedido_itens pi ON pi.pedido_id=p.id
                WHERE p.cliente_id=? GROUP BY p.id ORDER BY p.id DESC
            """, (cid,)).fetchall()

        top = tk.Toplevel(self)
        top.title(f"Histórico — {c['nome']}")
        top.configure(bg=C["bg2"])
        top.transient(self)
        top.geometry("640x440")

        hdr = tk.Frame(top, bg=C["bg3"])
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {c['nome']}", bg=C["bg3"], fg=C["green"],
                 font=FONT_TITLE, pady=8).pack(side="left")
        sep(top, "h").pack(fill="x")

        info = tk.Frame(top, bg=C["bg2"], padx=16, pady=8)
        info.pack(fill="x")
        for lbl, val in [("Email", c["email"] or "-"), ("Telefone", c["telefone"] or "-"),
                         ("CPF/CNPJ", c["cpf_cnpj"] or "-"), ("Endereço", c["endereco"] or "-")]:
            r = tk.Frame(info, bg=C["bg2"])
            r.pack(side="left", padx=12)
            tk.Label(r, text=f"{lbl}: ", bg=C["bg2"], fg=C["text_dim"], font=FONT_SM).pack(side="left")
            tk.Label(r, text=val, bg=C["bg2"], fg=C["text"], font=FONT_SM).pack(side="left")

        sep(top, "h").pack(fill="x")
        frm, tree = make_tree(top, [
            ("#",      "#",       50,  "center"),
            ("itens",  "Itens",   50,  "center"),
            ("total",  "Total",   110, "e"),
            ("pgto",   "Pagamento",150,"w"),
            ("data",   "Data",    120, "w"),
            ("status", "Status",  90,  "center"),
        ])
        frm.pack(fill="both", expand=True, padx=8, pady=8)
        total_gasto = 0
        for p in peds:
            tag = {"ativo":"ok","cancelado":"cancel"}.get(p["status"],"dev")
            tree.insert("", "end", tags=(tag,), values=(
                f"#{p['id']}", p["itens"], fmtR(p["total"]),
                p["forma_pagamento"], p["criado_em"][:16], p["status"].upper()))
            if p["status"] == "ativo":
                total_gasto += p["total"]

        bot = tk.Frame(top, bg=C["bg2"], padx=16, pady=8)
        bot.pack(fill="x")
        tk.Label(bot, text=f"Total gasto (ativos): {fmtR(total_gasto)}",
                 bg=C["bg2"], fg=C["green"], font=FONT_BOLD).pack(side="left")
        DarkButton(top, text="Fechar", command=top.destroy).pack(pady=6)


class PageRelatorios(PageBase):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        tabs = ttk.Notebook(self)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)

        for tab_id, title, build_fn in [
            ("vendas",   "  Vendas  ",         self._build_vendas),
            ("margem",   "  Margem  ",         self._build_margem),
            ("estoque",  "  Estoque  ",        self._build_estoque_rep),
            ("metas",    "  Metas  ",          self._build_metas),
        ]:
            frm = tk.Frame(tabs, bg=C["bg"])
            tabs.add(frm, text=title)
            build_fn(frm)

        style = ttk.Style()
        style.configure("TNotebook", background=C["bg"])
        style.configure("TNotebook.Tab", background=C["bg3"], foreground=C["text_dim"],
                        padding=[12, 6], font=FONT_SM)
        style.map("TNotebook.Tab",
            background=[("selected", C["bg2"])],
            foreground=[("selected", C["green"])])

    def _build_vendas(self, parent):
        DarkButton(parent, text="↻ Atualizar", command=lambda: self._refresh_vendas()).pack(
            anchor="ne", padx=12, pady=8)
        self._vend_frame = tk.Frame(parent, bg=C["bg"])
        self._vend_frame.pack(fill="both", expand=True, padx=12)
        self._refresh_vendas()

    def _refresh_vendas(self):
        for w in self._vend_frame.winfo_children():
            w.destroy()
        with conectar() as conn:
            geral = conn.execute(
                "SELECT COUNT(*) n, COALESCE(SUM(total),0) t, COALESCE(SUM(desconto),0) d"
                " FROM pedidos WHERE status='ativo'").fetchone()
            por_pgto = conn.execute("""
                SELECT forma_pagamento, COUNT(*) qtd, SUM(total) total
                FROM pedidos WHERE status='ativo'
                GROUP BY forma_pagamento ORDER BY total DESC""").fetchall()
            top_prods = conn.execute("""
                SELECT pr.nome, SUM(pi.quantidade) qtd, SUM(pi.subtotal) receita
                FROM pedido_itens pi
                JOIN pedidos p ON p.id=pi.pedido_id
                JOIN produtos pr ON pr.id=pi.produto_id
                WHERE p.status='ativo' GROUP BY pr.id ORDER BY receita DESC LIMIT 10""").fetchall()

        mid = tk.Frame(self._vend_frame, bg=C["bg"])
        mid.pack(fill="both", expand=True)

        kf = tk.Frame(mid, bg=C["bg"])
        kf.pack(fill="x", pady=6)
        for lbl, val, color in [
            ("Total Pedidos",  str(geral["n"]),    C["green"]),
            ("Receita Total",  fmtR(geral["t"]),   C["green"]),
            ("Total Descontos",fmtR(geral["d"]),   C["amber"]),
        ]:
            kbox = tk.Frame(kf, bg=C["bg3"], highlightbackground=C["border"], highlightthickness=1)
            kbox.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(kbox, text=lbl, bg=C["bg3"], fg=C["text_dim"],
                     font=FONT_SM, padx=12, pady=4).pack(anchor="w")
            tk.Label(kbox, text=val, bg=C["bg3"], fg=color,
                     font=FONT_LG, padx=12, pady=4).pack(anchor="w")

        bot = tk.Frame(mid, bg=C["bg"])
        bot.pack(fill="both", expand=True, pady=6)

        c1, b1 = card(bot, "Por Forma de Pagamento")
        c1.pack(side="left", fill="both", expand=True, padx=(0, 4))
        frm1, tree1 = make_tree(b1, [
            ("forma", "Forma",    200, "w"),
            ("qtd",   "Pedidos",  80,  "center"),
            ("total", "Total",    120, "e"),
        ])
        frm1.pack(fill="both", expand=True)
        for r in por_pgto:
            tree1.insert("", "end", values=(r["forma_pagamento"], r["qtd"], fmtR(r["total"])))

        c2, b2 = card(bot, "Top Produtos")
        c2.pack(side="right", fill="both", expand=True)
        frm2, tree2 = make_tree(b2, [
            ("nome",    "Produto", 220, "w"),
            ("qtd",     "Qtd",     60,  "center"),
            ("receita", "Receita", 120, "e"),
        ])
        frm2.pack(fill="both", expand=True)
        for r in top_prods:
            tree2.insert("", "end", values=(r["nome"], r["qtd"], fmtR(r["receita"])))

    def _build_margem(self, parent):
        DarkButton(parent, text="↻ Atualizar", command=lambda: self._refresh_margem()).pack(
            anchor="ne", padx=12, pady=8)
        self._marg_frame = tk.Frame(parent, bg=C["bg"])
        self._marg_frame.pack(fill="both", expand=True, padx=12)
        self._refresh_margem()

    def _refresh_margem(self):
        for w in self._marg_frame.winfo_children():
            w.destroy()
        with conectar() as conn:
            rows = conn.execute("""
                SELECT pr.nome,
                       SUM(pi.quantidade) qtd,
                       SUM(pi.subtotal) receita,
                       SUM(pi.quantidade * pr.preco_custo) custo
                FROM pedido_itens pi
                JOIN pedidos p ON p.id=pi.pedido_id
                JOIN produtos pr ON pr.id=pi.produto_id
                WHERE p.status='ativo' GROUP BY pr.id
                ORDER BY (SUM(pi.subtotal)-SUM(pi.quantidade*pr.preco_custo)) DESC""").fetchall()
        c, b = card(self._marg_frame, "Margem de Lucro por Produto")
        c.pack(fill="both", expand=True)
        frm, tree = make_tree(b, [
            ("nome",    "Produto",  240, "w"),
            ("qtd",     "Qtd",       60, "center"),
            ("receita", "Receita",  120, "e"),
            ("custo",   "Custo",    120, "e"),
            ("lucro",   "Lucro",    120, "e"),
            ("marg",    "Margem",    80, "center"),
        ])
        frm.pack(fill="both", expand=True)
        for r in rows:
            lucro = r["receita"] - r["custo"]
            marg  = lucro / r["receita"] * 100 if r["receita"] else 0
            tag   = "ok" if marg >= 20 else ("low" if marg >= 5 else "zero")
            tree.insert("", "end", tags=(tag,), values=(
                r["nome"], r["qtd"], fmtR(r["receita"]),
                fmtR(r["custo"]), fmtR(lucro), f"{marg:.1f}%"))

    def _build_estoque_rep(self, parent):
        DarkButton(parent, text="↻ Atualizar", command=lambda: self._refresh_est_rep()).pack(
            anchor="ne", padx=12, pady=8)
        self._est_frame = tk.Frame(parent, bg=C["bg"])
        self._est_frame.pack(fill="both", expand=True, padx=12)
        self._refresh_est_rep()

    def _refresh_est_rep(self):
        for w in self._est_frame.winfo_children():
            w.destroy()
        with conectar() as conn:
            prods = conn.execute(
                "SELECT nome,sku,estoque,estoque_minimo,preco_venda,preco_custo"
                " FROM produtos WHERE ativo=1 ORDER BY nome").fetchall()
        c, b = card(self._est_frame)
        c.pack(fill="both", expand=True)
        frm, tree = make_tree(b, [
            ("sku",    "SKU",      80,  "w"),
            ("nome",   "Produto",  220, "w"),
            ("estq",   "Estoque",  70,  "center"),
            ("min",    "Mínimo",   60,  "center"),
            ("vv",     "Vl.Venda", 120, "e"),
            ("vc",     "Vl.Custo", 120, "e"),
            ("marg",   "Marg.%",   70,  "center"),
        ])
        frm.pack(fill="both", expand=True)
        tot_v = tot_c = 0
        for p in prods:
            vv = p["preco_venda"] * p["estoque"]
            vc = p["preco_custo"] * p["estoque"]
            tot_v += vv; tot_c += vc
            marg = (vv - vc) / vv * 100 if vv else 0
            tag = "zero" if p["estoque"] == 0 else \
                  ("low" if p["estoque"] <= p["estoque_minimo"] else "ok")
            tree.insert("", "end", tags=(tag,), values=(
                p["sku"] or "-", p["nome"], p["estoque"], p["estoque_minimo"],
                fmtR(vv), fmtR(vc), f"{marg:.1f}%"))
        marg_tot = (tot_v - tot_c) / tot_v * 100 if tot_v else 0
        tk.Label(b, text=f"  Total Venda: {fmtR(tot_v)}   Total Custo: {fmtR(tot_c)}"
                         f"   Margem potencial: {marg_tot:.1f}%",
                 bg=C["bg2"], fg=C["amber"], font=FONT_BOLD,
                 anchor="w", pady=4).pack(fill="x")

    def _build_metas(self, parent):
        top = tk.Frame(parent, bg=C["bg"])
        top.pack(fill="x", padx=12, pady=8)

        c_form, b_form = card(top, "+ Definir / Atualizar Meta")
        c_form.pack(fill="x", pady=(0, 8))
        ff = tk.Frame(b_form, bg=C["bg2"])
        ff.pack(fill="x")

        self._meta_mes  = tk.StringVar(value=str(date.today())[:7])
        self._meta_val  = tk.StringVar()
        tk.Label(ff, text="Mês (AAAA-MM):", bg=C["bg2"], fg=C["text_dim"],
                 font=FONT_SM).pack(side="left")
        DarkEntry(ff, textvariable=self._meta_mes, width=12).pack(side="left", padx=6)
        tk.Label(ff, text="Meta R$:", bg=C["bg2"], fg=C["text_dim"],
                 font=FONT_SM).pack(side="left", padx=(12,4))
        DarkEntry(ff, textvariable=self._meta_val, width=14).pack(side="left")
        DarkButton(ff, text="✓ Salvar Meta",
                   command=self._salvar_meta).pack(side="left", padx=10)

        self._metas_frame = tk.Frame(parent, bg=C["bg"])
        self._metas_frame.pack(fill="both", expand=True, padx=12)
        self._refresh_metas()

    def _salvar_meta(self):
        mes = self._meta_mes.get().strip()
        try: val = float(self._meta_val.get().replace(",","."))
        except:
            messagebox.showerror("Erro", "Valor inválido.", parent=self); return
        if len(mes) != 7 or mes[4] != "-":
            messagebox.showerror("Erro", "Formato inválido. Use AAAA-MM.", parent=self); return
        with conectar() as conn:
            conn.execute("INSERT OR REPLACE INTO metas (mes,valor_meta) VALUES (?,?)", (mes, val))
        self._flash(f"✓  Meta de {fmtR(val)} definida para {mes}!", C["green"])
        self._refresh_metas()

    def _refresh_metas(self):
        for w in self._metas_frame.winfo_children():
            w.destroy()
        with conectar() as conn:
            metas  = conn.execute("SELECT * FROM metas ORDER BY mes DESC").fetchall()
            vendas = conn.execute("""
                SELECT strftime('%Y-%m',criado_em) mes, SUM(total) real
                FROM pedidos WHERE status='ativo' GROUP BY mes""").fetchall()
        v_dict = {v["mes"]: v["real"] for v in vendas}

        c, b = card(self._metas_frame, "Histórico de Metas")
        c.pack(fill="both", expand=True)
        frm, tree = make_tree(b, [
            ("mes",   "Mês",       90,  "w"),
            ("meta",  "Meta",      130, "e"),
            ("real",  "Realizado", 130, "e"),
            ("pct",   "%",         70,  "center"),
            ("barra", "Progresso", 200, "w"),
            ("status","Status",    90,  "center"),
        ])
        frm.pack(fill="both", expand=True)
        for m in metas:
            real = v_dict.get(m["mes"], 0.0)
            pct  = real / m["valor_meta"] * 100 if m["valor_meta"] else 0
            bar_f = min(20, int(pct / 5))
            barra = "█" * bar_f + "░" * (20 - bar_f)
            tag   = "ok" if pct >= 100 else "low"
            tree.insert("", "end", tags=(tag,), values=(
                m["mes"], fmtR(m["valor_meta"]), fmtR(real),
                f"{pct:.1f}%", barra, "ATINGIDA" if pct >= 100 else "em aberto"))


class PageSistema(PageBase):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        outer, b = card(self, "◫  Configurações do Sistema")
        outer.pack(padx=20, pady=20, fill="x")

        campos = [
            ("empresa_nome",      "Nome da Empresa"),
            ("empresa_cnpj",      "CNPJ"),
            ("empresa_telefone",  "Telefone"),
            ("empresa_endereco",  "Endereço"),
            ("alerta_estoque",    "Limite alerta estoque"),
        ]
        self._vars = {}
        for chave, label in campos:
            row = tk.Frame(b, bg=C["bg2"])
            row.pack(fill="x", pady=5)
            tk.Label(row, text=label + ":", bg=C["bg2"], fg=C["text_dim"],
                     font=FONT_SM, width=24, anchor="w").pack(side="left")
            var = tk.StringVar(value=get_config(chave, ""))
            DarkEntry(row, textvariable=var, width=40).pack(side="left")
            self._vars[chave] = var

        sep(b, "h").pack(fill="x", pady=8)
        DarkButton(b, text="✓  Salvar Configurações",
                   command=self._save, bg=C["green3"], fg="#fff",
                   activebackground=C["green2"]).pack(anchor="w")

        info_f = tk.Frame(self, bg=C["bg2"],
                          highlightbackground=C["border"], highlightthickness=1)
        info_f.pack(padx=20, pady=12, fill="x")
        tk.Label(info_f, text="  ◈  Sistema de Estoque v2.0.0  |  Python / Tkinter  |  SQLite",
                 bg=C["bg2"], fg=C["green_dim"], font=FONT_SM,
                 anchor="w", pady=8).pack(fill="x")
        tk.Label(info_f, text=f"  Banco de dados: {DB_PATH}",
                 bg=C["bg2"], fg=C["text_dim"], font=FONT_SM,
                 anchor="w", pady=4).pack(fill="x")

    def _save(self):
        for chave, var in self._vars.items():
            set_config(chave, var.get().strip())
        self._flash("✓  Configurações salvas!", C["green"])
        self.app.update_title()


# ═══════════════════════════════════════════════════════════════════
# APLICAÇÃO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        _fix_fonts()
        apply_dark_style()

        self.title("Sistema de Estoque v2.0")
        self.configure(bg=C["bg"])
        self.geometry("1280x760")
        self.minsize(900, 580)

        self._flash_id = None
        self._build()
        self.update_title()

    def _build(self):
        topbar = tk.Frame(self, bg=C["topbar"], height=40)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        self._lbl_empresa = tk.Label(topbar, text="◈  Sistema de Estoque",
                                     bg=C["topbar"], fg=C["green"],
                                     font=FONT_BOLD, padx=16)
        self._lbl_empresa.pack(side="left")

        tk.Frame(topbar, width=1, bg=C["border"]).pack(side="left", fill="y", pady=6)

        self._flash_label = tk.Label(topbar, text="", bg=C["topbar"],
                                     fg=C["green"], font=FONT_SM, padx=16)
        self._flash_label.pack(side="left", fill="x", expand=True)

        self._lbl_clock = tk.Label(topbar, text="", bg=C["topbar"],
                                   fg=C["text_dim"], font=FONT_SM, padx=12)
        self._lbl_clock.pack(side="right")
        self._tick()

        sep(self, "h", bg=C["border"]).pack(fill="x")

        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._sidebar = tk.Frame(body, bg=C["sidebar"], width=200)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)
        sep(body, "v", bg=C["border"]).pack(side="left", fill="y")

        self._content = tk.Frame(body, bg=C["bg"])
        self._content.pack(side="left", fill="both", expand=True)

        self._pages = {}
        pages = [
            ("dashboard",  "◈  Dashboard",  PageDashboard),
            ("pedidos",    "◉  Pedidos",     PagePedidos),
            ("estoque",    "▣  Estoque",     PageEstoque),
            ("produtos",   "▦  Produtos",    PageProdutos),
            ("clientes",   "◍  Clientes",    PageClientes),
            ("relatorios", "▤  Relatórios",  PageRelatorios),
            ("sistema",    "◫  Sistema",     PageSistema),
        ]

        tk.Label(self._sidebar, text="  NAVEGAÇÃO", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Courier", 9), anchor="w",
                 pady=12, padx=8).pack(fill="x")

        self._nav_btns = {}
        for key, label, PageClass in pages:
            page = PageClass(self._content, self)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[key] = page

            btn = tk.Button(self._sidebar, text=f"  {label}",
                            bg=C["sidebar"], fg=C["text_dim"],
                            activebackground=C["bg3"], activeforeground=C["green"],
                            relief="flat", font=FONT_SM, anchor="w",
                            cursor="hand2", pady=10, padx=8,
                            command=lambda k=key: self.goto(k),
                            bd=0, highlightthickness=0)
            btn.pack(fill="x")
            self._nav_btns[key] = btn

        sep(self._sidebar, "h").pack(fill="x", pady=8)
        tk.Label(self._sidebar, text=f"  v2.0.0", bg=C["sidebar"],
                 fg=C["green_dim"], font=FONT_SM, anchor="w",
                 padx=8, pady=4).pack(fill="x")

        self._current = None
        self.goto("dashboard")

    def goto(self, key):
        if self._current:
            self._nav_btns[self._current].config(
                bg=C["sidebar"], fg=C["text_dim"], highlightthickness=0)
        self._current = key
        btn = self._nav_btns[key]
        btn.config(bg=C["bg3"], fg=C["green"],
                   highlightthickness=2, highlightbackground=C["green3"])
        page = self._pages[key]
        page.lift()
        try: page.refresh()
        except: pass

    def flash(self, msg, color=None):
        if self._flash_id:
            self.after_cancel(self._flash_id)
        self._flash_label.config(text=msg, fg=color or C["green"])
        self._flash_id = self.after(4000, lambda: self._flash_label.config(text=""))

    def update_title(self):
        nome = get_config("empresa_nome", "Sistema de Estoque")
        self.title(f"{nome}  —  v2.0")
        self._lbl_empresa.config(text=f"◈  {nome}")

    def _tick(self):
        self._lbl_clock.config(text=datetime.now().strftime("  %d/%m/%Y  %H:%M:%S  "))
        self.after(1000, self._tick)


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

def main():
    inicializar_banco()
    seed()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
