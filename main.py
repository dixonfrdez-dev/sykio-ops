import os
from flask import Flask, render_template, jsonify, request
import time
import threading
from core.autotrader import Autotrader
from config import MARGEN_MINIMO_DEFECTO, SPREAD_DEFECTO

# Configurar ruta absoluta para la carpeta de plantillas
base_dir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'))

# Instancia global del Autotrader
autotrader = Autotrader(margen_minimo=MARGEN_MINIMO_DEFECTO, spread=SPREAD_DEFECTO)

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
            pass
        time.sleep(3)

# Iniciar el hilo del bot en segundo plano
hilo_bot = threading.Thread(target=ciclo_segundo_plano, daemon=True)
hilo_bot.start()

# --- RUTAS Y ENDPOINTS DE FLASK ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/mercado', methods=['GET'])
def obtener_mercado():
    servicio = request.args.get('servicio', 'Pago Móvil')
    
    # Órdenes dinámicas según el servicio seleccionado en el panel
    if "Venezuela" in servicio:
        ordenes = [
            {"tipo": "VES", "precio": 1090.00, "min": "1.00", "max": "100.0", "comerciante": "Faberque_64"},
            {"tipo": "VES", "precio": 1089.50, "min": "5.00", "max": "50.0", "comerciante": "Astaroth32"}
        ]
    elif "Bancamiga" in servicio:
        ordenes = [
            {"tipo": "VES", "precio": 1085.00, "min": "10.0", "max": "150.0", "comerciante": "Bancamiga_Fast"}
        ]
    else:
        ordenes = [
            {"tipo": "VES", "precio": 1100.00, "min": "1.00", "max": "277.9", "comerciante": "Antarchos2"},
            {"tipo": "VES", "precio": 1099.00, "min": "5.00", "max": "69.0", "comerciante": "botunicavenez"},
            {"tipo": "VES", "precio": 1098.50, "min": "10.0", "max": "91.9", "comerciante": "ejecutorv"}
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
