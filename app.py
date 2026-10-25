import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app) # Permite que tu página web de GitHub Pages se conecte

# 🔑 Tu API Key de Groq
API_KEY_GROQ = "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"

# Inicializamos el cliente de Groq
client = Groq(api_key=API_KEY_GROQ)

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

    # 💌 Saludo personalizado
    usuario_lower = usuario.lower()
    if "damián" in usuario_lower or "damian" in usuario_lower:
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

    try:
        # 1. Guardar mensaje del usuario en SQLite
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memoria_chat (usuario, remitente, mensaje) VALUES (?, ?, ?)", 
                       (usuario, "user", mensaje_usuario))
        conn.commit()

        # 2. Recuperar últimos 15 mensajes del usuario para la memoria
        cursor.execute("SELECT remitente, mensaje FROM memoria_chat WHERE usuario = ? ORDER BY id DESC LIMIT 15", (usuario,))
        historial_db = cursor.fetchall()
        conn.close()

        # Reconstruir el historial en formato de Groq
        mensajes_groq = [{"role": "system", "content": SYSTEM_PROMPT}]
        for r in reversed(historial_db[:-1]):
            role = "user" if r[0] == "user" else "assistant"
            mensajes_groq.append({"role": role, "content": r[1]})
            
        mensajes_groq.append({"role": "user", "content": mensaje_usuario})

        # 🤖 Lista de modelos compatibles para intentar en orden (Respaldo inteligente)
        modelos_disponibles = [
            "llama-3.3-70b-versatile",
            "llama-3.3-70b-specdec"
        ]
        
        respuesta_ia = None
        ultimo_error = None

        for modelo_nombre in modelos_disponibles:
            try:
                completion = client.chat.completions.create(
                    model=modelo_nombre,
                    messages=mensajes_groq,
                    temperature=0.7,
                    max_tokens=1024,
                )
                respuesta_ia = completion.choices[0].message.content
                if respuesta_ia:
                    break # ¡Si logró responder, sale del bucle de inmediato!
            except Exception as err_m:
                ultimo_error = err_m
                continue

        if not respuesta_ia:
            raise Exception(f"No se pudo conectar con ningún modelo: {ultimo_error}")

        # 3. Guardar la respuesta de Neil en la memoria SQLite
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memoria_chat (usuario, remitente, mensaje) VALUES (?, ?, ?)", 
                       (usuario, "model", respuesta_ia))
        conn.commit()
        conn.close()

        return jsonify({"respuesta": respuesta_ia})

    except Exception as e:
        print(f"Error detallado con Groq: {e}")
        return jsonify({"respuesta": f"¡Uy! El tren estelar tuvo un pequeño bache: {str(e)} 🚂💨"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
