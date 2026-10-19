import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.genai as genai

app = Flask(__name__)
CORS(app)  # Permite que tu página web de GitHub Pages se comunique con este servidor

# Configurar la API Key de Gemini desde las variables de entorno de Render
GEMINI_API_KEY = os.environ.get("MI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 🗄️ Configuración de la Base de Datos SQLite (La libretita de memoria de Neil)
DB_NAME = "neil_estacion.db"

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
        return jsonify({"status": "ERROR", "mensaje" : "Falta el nombre estelar."}), 400

    return jsonify({"status": "OK", "mensaje": f"Bienvenido a la estación, {usuario}"})

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    usuario = data.get("usuario", "Viajero")
    mensaje_usuario = data.get("mensaje", "")

    if not mensaje_usuario:
        return jsonify({"respuesta": "¡Uy! No escuché bien tu mensaje, ¿me lo repites? 🚂"})

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # 1. Guardar el mensaje del usuario en la base de datos
        cursor.execute("INSERT INTO memoria_chat (usuario, remitente, mensaje) VALUES (?, ?, ?)", 
                       (usuario, "user", mensaje_usuario))
        conn.commit()

        # 2. Recuperar el historial reciente de este usuario (últimos 15 mensajes para tener contexto)
        cursor.execute("SELECT remitente, mensaje FROM memoria_chat WHERE usuario = ? ORDER BY id DESC LIMIT 15", (usuario,))
        historial_db = cursor.fetchall()
        conn.close()

        # Reconstruir el historial para Gemini (orden cronológico)
        chat_history = [{"role": "user" if r[0] == "user" else "model", "parts": [r[1]]} for r in reversed(historial_db[:-1])]

        # Inicializar el modelo con el prompt del sistema y la memoria de la conversación
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=SYSTEM_PROMPT
        )
        
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(mensaje_usuario)
        respuesta_ia = response.text

        # 3. Guardar la respuesta de Neil en la base de datos
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memoria_chat (usuario, remitente, mensaje) VALUES (?, ?, ?)", 
                       (usuario, "model", respuesta_ia))
        conn.commit()
        conn.close()

        return jsonify({"respuesta": respuesta_ia})

    except Exception as e:
        print(f"Error en el chat: {e}")
        return jsonify({"respuesta": "¡Ay! Se me descarriló un vagón de ideas por un segundito. 🚂💨 ¿Me lo dices otra vez?"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)