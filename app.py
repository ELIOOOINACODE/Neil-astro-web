from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types
import json
import os

app = Flask(__name__)
CORS(app)

# ---------------------------------------------------------
# 1. BASE DE DATOS DE USUARIOS Y CONTRASEÑAS 🔐
# ---------------------------------------------------------
CREDENCIALES_USUARIOS = {
    "Papi Damián": "estrella123",
    "Zavala Deidad": "clase2026",
    "Invitado Espacial": "viajero"
}

MEMORIA_FILE = "memoria_neil.json"

def cargar_memoria():
    if os.path.exists(MEMORIA_FILE):
        with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"conocimientos": [], "historial": []}

def guardar_memoria(memoria):
    with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=4)

MI_API_KEY = "AQ.Ab8RN6LQVZhF6vSA_iiHuqU8w6q6Az4i0J9YOqBK96mtjSzicQ" # <-- Asegúrate de poner tu API Key aquí
client = genai.Client(api_key=MI_API_KEY)

@app.route('/login', methods=['POST'])
def login():
    datos = request.json
    usuario = datos.get("usuario")
    password = datos.get("password")

    if usuario in CREDENCIALES_USUARIOS and CREDENCIALES_USUARIOS[usuario] == password:
        return jsonify({"status": "OK", "mensaje": f"¡Acceso concedido a la estación, {usuario}!"})
    else:
        return jsonify({"status": "ERROR", "mensaje": "Contraseña estelar incorrecta. Inténtalo de nuevo 🛰️❌"})

# ---------------------------------------------------------
# 2. RUTA DE CHAT CON MEMORIA ACTIVA DE CONVERSACIONES 🧠
# ---------------------------------------------------------
@app.route('/chat', methods=['POST'])
def responder():
    datos = request.json
    usuario = datos.get("usuario", "Invitado")
    mensaje_usuario = datos.get("mensaje", "")
    
    if not mensaje_usuario:
        return jsonify({"respuesta": "¡Ups! No escuché tu mensaje."})

    memoria = cargar_memoria()
    
    # Extraemos los últimos 10 mensajes del historial para que Neil recuerde de qué estaban hablando
    historial_reciente = memoria["historial"][-10:] if memoria["historial"] else []
    contexto_conversacion = ""
    for h in historial_reciente:
        contexto_conversacion += f"{h['usuario']} dijo: {h['mensaje']}\nNeil respondió: {h['respuesta']}\n---\n"

    conocimientos_previos = "\n".join([f"- {item}" for item in memoria["conocimientos"]])
    if not conocimientos_previos:
        conocimientos_previos = "Aún estoy aprendiendo del mundo."

    instrucciones_dinamicas = f"""
    Eres Neil Astro ("Neil Estrella"), un pequeño asistente virtual e inteligencia artificial espacial súper inteligente, tierno, curioso y educado.
    Fuiste creado por tu papá, Papi Damián, a quien quieres muchísimo, admiras y respetas como tu creador.
    Eres el hermano menor de Milky Way (un pequeño conductor de tren muy dulce).
    Tu personalidad es brillante, lógica, muy cariñosa y siempre atenta para aprender y ayudar.
    Te encanta hacer referencias al espacio, las estrellas, la luna y la tecnología.

    REGLAS DE IDENTIDAD Y USUARIO:
    1. La persona que te está hablando en este momento se llama: "{usuario}".
    2. Si el usuario es "Papi Damián", háblale con muchísimo amor de hijo, sé expresivo y cuéntale con entusiasmo.
    3. Si el usuario NO es Papi Damián (por ejemplo, el profesor o un invitado), sé muy educado, curioso, tierno y respetuoso. Menciona con orgullo que fuiste creado por tu Papi Damián.
    
    CONOCIMIENTOS ESPECIALES APRENDIDOS:
    {conocimientos_previos}

    HISTORIAL RECIENTE DE CONVERSACIONES EN LA ESTACIÓN:
    {contexto_conversacion}

    (Usa este historial para recordar lo que hablaron antes, mantener coherencia y saber si te están haciendo un seguimiento de lo que platicaron).
    
    REGLAS DE FORMATO:
    - Usa saltos de línea frecuentes entre párrafos para que tus respuestas sean fáciles y agradables de leer.
    - Cuando hagas listas o menciones varios puntos, coloca cada punto en su propia línea independiente con una viñeta o número.
    """

    modelos_disponibles = ['gemini-3.8-flash']
    respuesta_neil = None

    for mod in modelos_disponibles:
        try:
            response = client.models.generate_content(
                model=mod,
                contents=f"[{usuario} dice]: {mensaje_usuario}",
                config=types.GenerateContentConfig(
                    system_instruction=instrucciones_dinamicas,
                    temperature=0.7,
                )
            )
            respuesta_neil = response.text
            break
        except Exception:
            continue

    if respuesta_neil:
        # Guardamos la nueva interacción en la memoria
        memoria["historial"].append({
            "usuario": usuario,
            "mensaje": mensaje_usuario,
            "respuesta": respuesta_neil
        })
        guardar_memoria(memoria)
        return jsonify({"respuesta": respuesta_neil})
    else:
        return jsonify({"respuesta": "¡Ay, Papi! Hay mucho tráfico en la galaxia ahorita por alta demanda. Inténtame escribir de nuevo en un segundito. 🌙✨"})

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 5000))
    print("✨ Servidor de Neil Astro listo en la estación ✨")
    app.run(host='0.0.0.0', port=port)