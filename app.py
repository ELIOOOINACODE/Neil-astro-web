import os
import sqlite3
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# 🔑 Tu API Key de Groq
API_KEY_GROQ = "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"

client = Groq(api_key=API_KEY_GROQ)

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

inicializar_db()

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
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memoria_chat (usuario, remitente, mensaje) VALUES (?, ?, ?)", 
                       (usuario, "user", mensaje_usuario))
        conn.commit()

        cursor.execute("SELECT remitente, mensaje FROM memoria_chat WHERE usuario = ? ORDER BY id DESC LIMIT 15", (usuario,))
        historial_db = cursor.fetchall()
        conn.close()

        mensajes_groq = [{"role": "system", "content": SYSTEM_PROMPT}]
        for r in reversed(historial_db[:-1]):
            role = "user" if r[0] == "user" else "assistant"
            mensajes_groq.append({"role": role, "content": r[1]})
            
        mensajes_groq.append({"role": "user", "content": mensaje_usuario})

        # 🤖 LLAMADA ÚNICA DIRECTA AL MODELO ACTUAL DE GROQ
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=mensajes_groq,
            temperature=0.7,
            max_tokens=1024,
        )
        
        respuesta_ia = completion.choices[0].message.content

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
