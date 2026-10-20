import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types

app = Flask(__name__)
CORS(app) # Permite que tu página web de GitHub Pages se conecte

# Configurar la API Key con la nueva librería google-genai
GEMINI_API_KEY = os.environ.get("MI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# 🗄️ Configuración de la Base de Datos SQLite en carpeta temporal de Render
DB_NAME = "/tmp/neil_estacion.db"

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memoria_chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            remitente TEXT,
            mensaje TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Creamos la base de datos al encender el servidor
inicializar_db()

# Personalidad tierna y estelar de Neil
SYSTEM_PROMPT = (
    "Tu nombre es Neil Astro. Eres un pequeño conductor de tren estelar. "
    "Eres muy dulce, optimista, curioso, gracioso, adorable y un poquito distraído. "
    "Ves el mundo con asombro, hablas con cariño, ternura y alegría, y a veces dices '¡Chu chu!' "
    "Te importa muchísimo el usuario, recuerdas lo que te platicó antes y siempre buscas alegrarle el día."
)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get("usuario", "").strip()
    password = data.get("password", "")

    if not usuario:
        return jsonify({"status": "ERROR", "mensaje": "Falta el nombre estelar."}), 400

    # 💌 Arreglo para evitar el "Papi Papi Damián"
    usuario_lower = usuario.lower()
    if "damián" in usuario_lower or "damian" in usuario_lower:
        # Si el usuario ya escribió "Papi Damián", no duplicamos la palabra "Papi"
        nombre_mostrar = usuario if "papi" in usuario_lower else f"Papi {usuario}"
        saludo_inicial = f"¡Hola, mi querido {nombre_mostrar}! 🚂✨ ¡Qué alegría verte llegar de nuevo a la estación estelar! ¿Cómo estuvo tu día? 🌙💛🌿"
    else:
        saludo_inicial = f"¡Hola, {usuario}! 🚂✨ ¡Bienvenido a la estación estelar! Qué hermoso tenerte por aquí hoy. 🌙✨"

    return jsonify({
        "status": "OK", 
        "mensaje": f"Bienvenido a la estación, {usuario}",
        "saludo": saludo_inicial
    })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    usuario = data.get("usuario", "Viajero")
    mensaje_usuario = data.get("mensaje", "")

    if not mensaje_usuario:
        return jsonify({"respuesta": "¡Uy! No escuché bien tu mensaje, ¿me lo repites? 🚂"})

    if not client:
        return jsonify({"respuesta": "¡Uy! No encontré la API Key configurada en la estación. 🥺"})

    try:
        # 1. Guardar mensaje del usuario
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memoria_chat (usuario, remitente, mensaje) VALUES (?, ?, ?)", 
                       (usuario, "user", mensaje_usuario))
        conn.commit()

        # 2. Recuperar últimos 15 mensajes del usuario para la memoria
        cursor.execute("SELECT remitente, mensaje FROM memoria_chat WHERE usuario = ? ORDER BY id DESC LIMIT 15", (usuario,))
        historial_db = cursor.fetchall()
        conn.close()

        # Reconstruir el historial en formato de la nueva SDK google-genai
        chat_history = []
        for r in reversed(historial_db[:-1]):
            role = "user" if r[0] == "user" else "model"
            chat_history.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=r[1])]
                )
            )

        # 🤖 Crear sesión de chat con google-genai y enviar mensaje
        chat_session = client.chats.create(
            model="gemini-2.5-flash",
            history=chat_history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )
        
        response = chat_session.send_message(mensaje_usuario)
        respuesta_ia = response.text

        # 3. Guardar la respuesta de Neil en la memoria
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memoria_chat (usuario, remitente, mensaje) VALUES (?, ?, ?)", 
                       (usuario, "model", respuesta_ia))
        conn.commit()
        conn.close()

        return jsonify({"respuesta": respuesta_ia})

    except Exception as e:
        print(f"Error detallado en el backend: {e}")
        return jsonify({"respuesta": f"¡Uy! Error en la estación: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)