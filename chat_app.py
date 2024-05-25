import streamlit as st
import sqlite3
import hashlib

# Configuração do Banco de Dados
def create_tables():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    
    # Tabela de usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    
    # Tabela de conversas
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            FOREIGN KEY (user1_id) REFERENCES users (id),
            FOREIGN KEY (user2_id) REFERENCES users (id)
        )
    ''')
    
    # Tabela de mensagens
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

create_tables()

# Funções para Cadastro, Login e Gerenciamento de Mensagens
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hash_password(password)))
    conn.commit()
    conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_user_by_username(username):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()
    return users

def create_conversation(user1_id, user2_id):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('INSERT INTO conversations (user1_id, user2_id) VALUES (?, ?)', (user1_id, user2_id))
    conn.commit()
    conversation_id = c.lastrowid
    conn.close()
    return conversation_id

def get_conversation(user1_id, user2_id):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('''
        SELECT * FROM conversations 
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    ''', (user1_id, user2_id, user2_id, user1_id))
    conversation = c.fetchone()
    conn.close()
    return conversation

def add_message(conversation_id, user_id, message):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages (conversation_id, user_id, message) VALUES (?, ?, ?)', (conversation_id, user_id, message))
    conn.commit()
    conn.close()

def get_messages(conversation_id):
    conn = sqlite3.connect('chat.db')
    c = conn.cursor()
    c.execute('SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp', (conversation_id,))
    messages = c.fetchall()
    conn.close()
    return messages

# Interface com Streamlit
# Variáveis de sessão para controle de login e conversa
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = None

def login():
    st.title('Login')
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = authenticate_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.success("Logged in successfully!")
        else:
            st.error("Invalid username or password")

def register():
    st.title('Register')
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if get_user_by_username(username):
            st.error("Username already taken")
        else:
            add_user(username, password)
            st.success("Registered successfully! Please login.")

def chat():
    st.title('Chat Application')
    
    # Seleção de usuário para iniciar uma conversa
    users = get_all_users()
    user_dict = {user[1]: user[0] for user in users if user[0] != st.session_state.user_id}
    
    if user_dict:
        recipient = st.selectbox("Select a user to chat with", list(user_dict.keys()))
        
        if st.button("Start Chat"):
            recipient_user_id = user_dict[recipient]
            conversation = get_conversation(st.session_state.user_id, recipient_user_id)
            if not conversation:
                conversation_id = create_conversation(st.session_state.user_id, recipient_user_id)
            else:
                conversation_id = conversation[0]
            st.session_state.conversation_id = conversation_id
    else:
        st.warning("No other users available to chat with.")
        return

    # Mostrar as mensagens da conversa
    if st.session_state.conversation_id:
        messages = get_messages(st.session_state.conversation_id)
        for msg in messages:
            user = get_user_by_id(msg[2])
            st.write(f"[{msg[4]}] {user[1]}: {msg[3]}")
        
        # Caixa de entrada de mensagem
        message = st.text_area("Message")
        if st.button("Send"):
            if message:
                add_message(st.session_state.conversation_id, st.session_state.user_id, message)
                st.experimental_rerun()
            else:
                st.error("Please enter a message")
    else:
        st.info("Start a chat with a user to see the messages.")

# Controle de fluxo da aplicação
if st.session_state.logged_in:
    chat()
else:
    st.sidebar.title("Menu")
    choice = st.sidebar.radio("Go to", ("Login", "Register"))
    if choice == "Login":
        login()
    else:
        register()
