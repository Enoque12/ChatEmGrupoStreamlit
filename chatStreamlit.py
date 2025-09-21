import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# ==============================
# Funções de Banco de Dados
# ==============================
def init_db():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        senha_hash TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        remetente TEXT,
        mensagem TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

def cadastrar_usuario(username, senha):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    try:
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (username, senha_hash) VALUES (?, ?)", (username, senha_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def autenticar_usuario(username, senha):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    cursor.execute("SELECT * FROM usuarios WHERE username=? AND senha_hash=?", (username, senha_hash))
    user = cursor.fetchone()
    conn.close()
    return user is not None

def salvar_mensagem(remetente, mensagem):
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mensagens (remetente, mensagem, timestamp) VALUES (?, ?, ?)",
                   (remetente, mensagem, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def carregar_mensagens():
    conn = sqlite3.connect("chat.db")
    cursor = conn.cursor()
    cursor.execute("SELECT remetente, mensagem, timestamp FROM mensagens ORDER BY id ASC")
    mensagens = cursor.fetchall()
    conn.close()
    return mensagens

# ==============================
# Interface Streamlit
# ==============================
init_db()

st.set_page_config(page_title="Chat em Grupo", layout="centered")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

# Login / Cadastro
if not st.session_state.usuario:
    aba = st.sidebar.radio("Menu", ["Login", "Cadastro"])

    if aba == "Login":
        st.title("🔑 Login")
        username = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar"):
            if autenticar_usuario(username, senha):
                st.session_state.usuario = username
                st.success(f"Bem-vindo, {username}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    elif aba == "Cadastro":
        st.title("🆕 Cadastro")
        new_user = st.text_input("Novo usuário")
        new_pass = st.text_input("Senha", type="password")
        if st.button("Cadastrar"):
            if cadastrar_usuario(new_user, new_pass):
                st.success("Usuário cadastrado com sucesso! Faça login.")
            else:
                st.error("Nome de usuário já existe.")

# Chat
else:
    st.title("💬 Chat em Grupo | Desenvolvido pelo Grupo 4")
    st.write(f"Usuário logado: **{st.session_state.usuario}**")
    if st.button("Sair"):
        st.session_state.usuario = None
        st.rerun()

    # 🔄 Auto-refresh a cada 3 segundos
    st_autorefresh(interval=3000, key="chatrefresh")

    # Mostrar mensagens
    mensagens = carregar_mensagens()
    for remetente, mensagem, timestamp in mensagens:
        if remetente == st.session_state.usuario:
            st.markdown(f"<div style='text-align: right; background-color:#000000; padding:8px; border-radius:10px; margin:5px;'>"
                        f"<b>{remetente}</b>: {mensagem}<br><small>{timestamp}</small></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align: left; background-color:#000000; padding:8px; border-radius:10px; margin:5px;'>"
                        f"<b>{remetente}</b>: {mensagem}<br><small>{timestamp}</small></div>", unsafe_allow_html=True)

    # Campo para enviar nova mensagem
    with st.form(key="form_mensagem", clear_on_submit=True):
        msg = st.text_input("Digite sua mensagem:")
        enviar = st.form_submit_button("Enviar")
        if enviar and msg.strip():
            salvar_mensagem(st.session_state.usuario, msg)
            st.rerun()
