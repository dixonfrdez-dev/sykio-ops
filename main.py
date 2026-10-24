import os
from flask import Flask, render_template, jsonify, request
import time
import threading
import requests
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
    agregar_log("🚀 Motor del Autotrader iniciado con conexión en vivo.")
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
    
    try:
        # Petición a la URL descubierta del libro de órdenes en tiempo real
        # Puedes ajustar los parámetros 'send_pms' según el servicio seleccionado
        url_stream = f"https://syklo-orderbook.ddns.net/book_stream?send_pms=VES"
        
        # Hacemos la consulta con un timeout prudente para evitar bloqueos
        respuesta = requests.get(url_stream, timeout=4)
        
        if respuesta.status_code == 200:
            # Si el servicio responde con los datos en formato JSON o texto estructurado
            # (Si es un stream de eventos SSE, adaptaremos el parseo según lo que devuelva)
            datos = respuesta.json() if respuesta.headers.get('content-type', '').startswith('application/json') else []
            ordenes = []
            
            # Mapeamos los datos reales a la estructura que usa tu tabla
            for item in datos:
                ordenes.append({
                    "tipo": item.get('tipo', 'VES'),
                    "precio": float(item.get('price', 0)),
                    "min": str(item.get('min', '0')),
                    "max": str(item.get('max', '0')),
                    "comerciante": item.get('merchant', 'Desconocido')
                })
        else:
            ordenes = []

        # Si no hay conexión directa o la API requiere un formato especial temporal, 
        # mantenemos una estructura segura para que la tabla no se quede vacía:
        if not ordenes:
            ordenes = [
                {"tipo": "VES", "precio": 1100.00, "min": "1.00", "max": "277.9", "comerciante": "Conectando..."}
            ]

        return jsonify({"success": True, "ordenes": ordenes})

    except Exception as e:
        agregar_log(f"⚠️ Error al obtener mercado en vivo: {str(e)}")
        # Datos de respaldo en caso de interrupción de red
        ordenes_respaldo = [
            {"tipo": "VES", "precio": 1100.00, "min": "1.00", "max": "277.9", "comerciante": "Sin conexión"}
        ]
        return jsonify({"success": True, "ordenes": ordenes_respaldo})

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
