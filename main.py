import os
from flask import Flask, render_template, jsonify, request
import time
import threading
from core.autotrader import Autotrader
from config import MARGEN_MINIMO_DEFECTO, SPREAD_DEFECTO

base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))


# Instancia global del Autotrader
autotrader = Autotrader(margen_minimo=MARGEN_MINIMO_DEFECTO)

# Historial de eventos visuales (Logs)
HISTORIAL_LOGS = []

def agregar_log(mensaje):
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {mensaje}"
    HISTORIAL_LOGS.insert(0, log_entry)
    if len(HISTORIAL_LOGS) > 30:
        HISTORIAL_LOGS.pop()

def ciclo_segundo_plano():
    """Hilo continuo para el bot"""
    agregar_log("🚀 Motor del Autotrader iniciado.")
    while True:
        if autotrader.activo:
            # Aquí va el ciclo principal de actualización de precios de tu autotrader
            pass
        time.sleep(3)

# Iniciar el hilo del bot en segundo plano
hilo_bot = threading.Thread(target=ciclo_segundo_plano, daemon=True)
hilo_bot.start()

# --- RUTAS Y ENDPOINTS DE FLASK ---

@app.route('/')
def index():
    # Carga directamente el archivo templates/index.html
    return render_template('index.html')

@app.route('/api/mercado', methods=['GET'])
def obtener_mercado():
    # Reemplaza esta lista con las órdenes reales que obtiene tu bot
    ordenes = [
        {"trader": "Trader_Alpha", "precio": 1069.50, "limite": "$50 - $1000", "es_mia": False},
        {"trader": "Tú (dixonfrdez)", "precio": 1069.05, "limite": "$10 - $500", "es_mia": True},
        {"trader": "Trader_Beta", "precio": 1068.80, "limite": "$20 - $300", "es_mia": False},
    ]
    return jsonify({"success": True, "ordenes": ordenes})

@app.route('/api/logs', methods=['GET'])
def obtener_logs():
    return jsonify({
        "success": True,
        "logs": HISTORIAL_LOGS,
        "activo": autotrader.activo
    })

@app.route('/api/toggle', methods=['POST'])
def toggle_bot():
    autotrader.activo = not autotrader.activo
    estado = "Reanudado" if autotrader.activo else "Pausado"
    agregar_log(f"🎮 Bot {estado} manualmente.")
    return jsonify({"success": True, "activo": autotrader.activo})

if __name__ == '__main__':
    app.run(debug=True)
