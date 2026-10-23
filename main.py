from flask import Flask, render_template_string, jsonify, request
import time
import threading
from core.autotrader import Autotrader
from config import MARGEN_MINIMO_DEFECTO, SPREAD_DEFECTO

app = Flask(__name__)

# Instancia global del Autotrader
autotrader = Autotrader(margen_minimo=MARGEN_MINIMO_DEFECTO, spread=SPREAD_DEFECTO)

# Historial de eventos visuales
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
            # Tasa de mercado de prueba/referencia (conectarás tu API real aquí)
            tasa_mercado = 1069.00
            tasa_propuesta = autotrader.evaluar_mercado(tasa_mercado)
            
            if tasa_propuesta:
                agregar_log(f"🔍 Mercado: {tasa_mercado} | Tu Oferta: {tasa_propuesta}")
        else:
            agregar_log("⏸️ Autotrader pausado.")
        time.sleep(30)

# Iniciar hilo en segundo plano
hilo = threading.Thread(target=ciclo_segundo_plano, daemon=True)
hilo.start()

# --- RUTAS WEB ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, margen=autotrader.margen_minimo, spread=autotrader.spread)

@app.route('/api/estado')
def api_estado():
    return jsonify({
        'mercado': 1069.00,
        'propuesta': autotrader.ultima_tasa or 1069.05,
        'activo': autotrader.activo,
        'logs': HISTORIAL_LOGS
    })

@app.route('/api/config', methods=['POST'])
def api_config():
    data = request.json
    autotrader.margen_minimo = float(data['margen'])
    autotrader.spread = float(data['spread'])
    agregar_log(f"⚙️ Configuración actualizada: Piso={autotrader.margen_minimo}, Spread={autotrader.spread}")
    return jsonify({'ok': True})

@app.route('/api/toggle', methods=['POST'])
def api_toggle():
    autotrader.activo = not autotrader.activo
    estado_str = "Reanudado" if autotrader.activo else "Pausado"
    agregar_log(f"🎮 Bot {estado_str} manualmente.")
    return jsonify({'activo': autotrader.activo})

# Plantilla HTML integrada para la WebApp móvil
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Syklo Autotrader Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 15px; }
        .card { background: #1e293b; border-radius: 12px; padding: 15px; margin-bottom: 15px; border: 1px solid #334155; }
        .title { font-size: 1.2rem; font-weight: bold; color: #38bdf8; display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        .stat { background: #0f172a; padding: 10px; border-radius: 8px; text-align: center; }
        .stat-val { font-size: 1.4rem; font-weight: bold; color: #10b981; }
        .btn { background: #0284c7; color: white; border: none; padding: 10px 15px; border-radius: 8px; width: 100%; font-size: 1rem; font-weight: bold; margin-top: 5px; cursor: pointer; }
        .btn-danger { background: #ef4444; }
        .logs { background: #000; color: #38bdf8; font-family: monospace; font-size: 0.8rem; height: 140px; overflow-y: auto; padding: 10px; border-radius: 8px; }
        input[type=number] { width: 100%; padding: 8px; background: #0f172a; border: 1px solid #334155; color: white; border-radius: 6px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="card">
        <div class="title">
            <span>⚡ Syklo Autotrader</span>
            <span id="status">🟢 Activo</span>
        </div>
        <div class="grid">
            <div class="stat"><div>Mercado</div><div class="stat-val" id="tasa-mercado">--</div></div>
            <div class="stat"><div>Tu Oferta</div><div class="stat-val" id="tasa-propuesta">--</div></div>
        </div>
    </div>

    <div class="card">
        <div class="title">⚙️ Ajustes</div>
        <label>Piso Mínimo (VES):</label>
        <input type="number" id="margen-min" step="5" value="{{ margen }}">
        <br><br>
        <label>Spread (+VES):</label>
        <input type="number" id="spread" step="0.01" value="{{ spread }}">
        <button class="btn" onclick="guardarAjustes()" style="margin-top:10px;">💾 Guardar</button>
    </div>

    <div class="card">
        <div class="title">🎮 Controles</div>
        <button id="btn-toggle" class="btn btn-danger" onclick="toggleBot()">⏸️ Pausar Bot</button>
    </div>

    <div class="card">
        <div class="title">📜 Logs en Vivo</div>
        <div class="logs" id="logs">Cargando...</div>
    </div>

    <script>
        function cargarDatos() {
            fetch('/api/estado').then(r => r.json()).then(data => {
                document.getElementById('tasa-mercado').innerText = data.mercado;
                document.getElementById('tasa-propuesta').innerText = data.propuesta;
                document.getElementById('status').innerText = data.activo ? '🟢 Activo' : '🔴 Pausado';
                document.getElementById('btn-toggle').innerText = data.activo ? '⏸️ Pausar Bot' : '▶️ Reanudar Bot';
                document.getElementById('logs').innerHTML = data.logs.join('<br>');
            });
        }
        function guardarAjustes() {
            fetch('/api/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({margen: document.getElementById('margen-min').value, spread: document.getElementById('spread').value})
            }).then(() => alert('¡Guardado con éxito!'));
        }
        function toggleBot() {
            fetch('/api/toggle', {method: 'POST'}).then(() => cargarDatos());
        }
        setInterval(cargarDatos, 3000);
        cargarDatos();
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
