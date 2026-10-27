// =========================================================================
// app.js - Syklo Ops Mobile (PWA con iframe integrado)
// =========================================================================

let botActive = false;
let monitorInterval = null;
let previousState = new Map();

const CONFIG = {
  pollIntervalMs: 10000,
  minAdjustPercent: 0.01,
  maxAdjustPercent: 2.0,
  telegramApi: 'https://api.telegram.org/bot'
};

// ------------------------------------------------------------------
// INICIO
// ------------------------------------------------------------------
window.addEventListener('load', () => {
  botActive = localStorage.getItem('botActive') === 'true';
  updateBotStatusUI();

  document.getElementById('trader-name').value = localStorage.getItem('traderName') || '';
  document.getElementById('telegram-token').value = localStorage.getItem('telegramToken') || '';
  document.getElementById('telegram-chatid').value = localStorage.getItem('telegramChatId') || '';

  document.getElementById('toggle-bot').addEventListener('click', toggleBot);
  document.getElementById('save-config').addEventListener('click', saveConfig);
  document.getElementById('toggle-syklo').addEventListener('click', toggleSyklo);

  if (botActive) startMonitoring();
});

// ------------------------------------------------------------------
// CONTROL DEL BOT
// ------------------------------------------------------------------
function toggleBot() {
  botActive = !botActive;
  localStorage.setItem('botActive', botActive);
  updateBotStatusUI();
  if (botActive) startMonitoring();
  else stopMonitoring();
}

function updateBotStatusUI() {
  document.getElementById('bot-status').textContent = botActive ? '🟢 ACTIVO' : '🔴 PAUSADO';
}

function startMonitoring() {
  if (monitorInterval) clearInterval(monitorInterval);
  monitorInterval = setInterval(pollMarket, CONFIG.pollIntervalMs);
  pollMarket();
}

function stopMonitoring() {
  if (monitorInterval) clearInterval(monitorInterval);
  monitorInterval = null;
}

function saveConfig() {
  localStorage.setItem('traderName', document.getElementById('trader-name').value.trim());
  localStorage.setItem('telegramToken', document.getElementById('telegram-token').value.trim());
  localStorage.setItem('telegramChatId', document.getElementById('telegram-chatid').value.trim());
  addLog('✅ Configuración guardada');
}

// ------------------------------------------------------------------
// SYKLO EN IFRAME
// ------------------------------------------------------------------
function toggleSyklo() {
  const wrap = document.getElementById('syklo-frame-wrap');
  wrap.style.display = wrap.style.display === 'none' ? 'block' : 'none';
}

// ------------------------------------------------------------------
// MONITOREO DEL MERCADO (lee el DOM del iframe)
// ------------------------------------------------------------------
function pollMarket() {
  const iframe = document.getElementById('syklo-frame');
  if (!iframe) return;

  let iframeDoc;
  try {
    iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
  } catch (e) {
    addLog('⚠️ No puedo leer el iframe (Syklo bloquea el acceso)');
    return;
  }

  const tbody = iframeDoc.querySelector('#book-table tbody');
  if (!tbody) {
    addLog('⏳ Esperando tabla de ofertas...');
    return;
  }

  const current = new Map();
  for (const row of tbody.getElementsByTagName('tr')) {
    const d = parseOfferRow(row);
    if (d) current.set(d.key, d);
  }

  const myName = localStorage.getItem('traderName');

  // Detectar cambios
  for (const [key, offer] of current.entries()) {
    const old = previousState.get(key);
    if (!old) {
      addLog(`✅ Nuevo: ${offer.trader} en ${offer.method} (${offer.type}) tasa ${offer.rate}`);
      sendTelegram('✅ Nuevo en ' + offer.method, offer.trader + ' entró con tasa ' + offer.rate);
    } else {
      if (Math.abs(offer.rate - old.rate) > 0.0001) {
        addLog(`🔄 Tasa: ${offer.trader} ${old.rate} ➔ ${offer.rate}`);
        sendTelegram('🔄 Tasa (' + offer.type + ') - ' + offer.method, offer.trader + ': ' + old.rate + ' ➔ ' + offer.rate);
      }
      if (Math.abs(offer.max - old.max) > 0.01) {
        const diff = (offer.max - old.max).toFixed(2);
        addLog(`📈 Capacidad: ${offer.trader} ${old.max} ➔ ${offer.max}`);
        sendTelegram('📈 Capacidad (' + offer.type + ') - ' + offer.method, offer.trader + ': ' + old.max + ' ➔ ' + offer.max + ' (' + (diff > 0 ? '+' : '') + diff + ')');
      }
    }
  }

  // Detectar salidas
  for (const [key, old] of previousState.entries()) {
    if (!current.has(key)) {
      addLog(`❌ Salió: ${old.trader} de ${old.method}`);
      sendTelegram('❌ Salió de ' + old.method, old.trader + ' salió (estaba en ' + old.rate + ')');
    }
  }

  previousState = current;

  // Auto-ajuste de mi oferta
  if (botActive && myName) autoAdjustMyOffer(myName, current);
}

function parseOfferRow(row) {
  try {
    let type = row.classList.contains('row-ask') ? 'sell' : row.classList.contains('row-bid') ? 'buy' : null;
    if (!type) return null;
    const cells = row.getElementsByTagName('td');
    if (cells.length < 5) return null;

    let method = (cells[0].textContent || '')
      .replace(/s*(.*?)/g, '')
      .replace(/[🌀-🧿]|[☀-⛿]|[✀-➿]/gu, '')
      .replace(/\b(VE|VES|USDC|liquidity)\b|🇨🇴|🇻🇪|-/gi, '')
      .trim();

    let trader = (cells[4].textContent || '').replace('✅', '').trim().split('.')[0].trim();
    if (!method || !trader) return null;

    return {
      key: trader + '|' + method + '|' + type,
      trader,
      method,
      rate: parseFloat(cells[1].textContent.replace(/,/g, '')),
      max: parseFloat(cells[3].textContent.replace(/,/g, '')),
      type
    };
  } catch (e) {
    return null;
  }
}

// ------------------------------------------------------------------
// AUTO-AJUSTE DE MI OFERTA
// ------------------------------------------------------------------
function autoAdjustMyOffer(myName, marketMap) {
  const mine = [];
  for (const offer of marketMap.values()) {
    if (offer.trader === myName) mine.push(offer);
  }
  if (!mine.length) return;

  for (const my of mine) {
    let bestRival = null;
    for (const offer of marketMap.values()) {
      if (offer.method !== my.method || offer.type !== my.type || offer.trader === myName) continue;
      if (bestRival === null) bestRival = offer.rate;
      else {
        if (my.type === 'buy' && offer.rate > bestRival) bestRival = offer.rate;
        if (my.type === 'sell' && offer.rate < bestRival) bestRival = offer.rate;
      }
    }
    if (bestRival === null) continue;

    const diffPercent = ((my.rate - bestRival) / bestRival) * 100;
    const isLosing = (my.type === 'buy' && my.rate < bestRival) || (my.type === 'sell' && my.rate > bestRival);

    if (isLosing && Math.abs(diffPercent) >= CONFIG.minAdjustPercent) {
      const adjustPercent = Math.min(Math.abs(diffPercent) + 0.01, CONFIG.maxAdjustPercent);
      const newRate = my.type === 'buy'
        ? my.rate * (1 + adjustPercent / 100)
        : my.rate * (1 - adjustPercent / 100);

      addLog(`🤖 Auto-Ajuste: ${my.method} ${my.rate} ➔ ${newRate.toFixed(4)}`);
      sendTelegram('🤖 Auto-Ajuste (' + my.type + ') - ' + my.method, 'Ajusté mi tasa de ' + my.rate + ' a ' + newRate.toFixed(4) + ' para competir con ' + bestRival);

      // NOTA: la actualización real de la tasa requiere el endpoint interno de Syklo.
      // Por ahora solo registramos la intención. Cuando tengas la URL de update, se integra aquí.
    }
  }
}

// ------------------------------------------------------------------
// LOG Y TELEGRAM
// ------------------------------------------------------------------
function addLog(text) {
  const log = document.getElementById('log');
  const entry = document.createElement('div');
  entry.className = 'log-entry';
  entry.textContent = '[' + new Date().toLocaleTimeString('es-VE') + '] ' + text;
  log.prepend(entry);
}

async function sendTelegram(title, message) {
  const token = localStorage.getItem('telegramToken');
  const chatId = localStorage.getItem('telegramChatId');
  if (!token || !chatId) return;

  try {
    await fetch(CONFIG.telegramApi + token + '/sendMessage', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: '<b>' + title + '</b>
' + message,
        parse_mode: 'HTML'
      })
    });
  } catch (err) {
    console.error('Error Telegram:', err);
  }
}
