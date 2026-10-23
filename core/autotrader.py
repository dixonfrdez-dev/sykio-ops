from services.telegram_bot import enviar_alerta

class Autotrader:
    def __init__(self, margen_minimo, spread):
        self.margen_minimo = margen_minimo
        self.spread = spread
        self.ultima_tasa = None
        self.activo = True

    def evaluar_mercado(self, tasa_mercado):
        if not self.activo:
            return None

        tasa_propuesta = tasa_mercado + self.spread
        
        # Filtro de seguridad
        if tasa_propuesta < self.margen_minimo:
            tasa_propuesta = self.margen_minimo
            enviar_alerta(f"⚠️ *Alerta de Seguridad*: Tasa fija al límite seguro ({self.margen_minimo})")

        # Notificar solo si hay cambio real
        if tasa_propuesta != self.ultima_tasa:
            self.ultima_tasa = tasa_propuesta
            enviar_alerta(f"🤖 *Cambio Detectado*\n• Mercado: {tasa_mercado}\n• Tu Tasa: *{tasa_propuesta}*")

        return tasa_propuesta
