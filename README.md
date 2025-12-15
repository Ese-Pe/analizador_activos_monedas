# 🪙 Crypto Swing Trading System

Sistema automatizado de análisis técnico para swing trading en criptomonedas, deployado en Render.com.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

## 🎯 Características

- ✅ Análisis automatizado de top 50-100 criptomonedas
- ✅ Indicadores técnicos: EMA(7/25), RSI(14), MACD(12/26/9), ATR
- ✅ Sistema de scoring multi-factor (7.5+ mínimo)
- ✅ Alertas Telegram automáticas
- ✅ Scheduler integrado con APScheduler
- ✅ Health checks para Render
- ✅ APIs gratuitas (CoinGecko)
- ✅ $0/mes de costo

## 📊 Parámetros del Sistema

| Parámetro | Valor |
|-----------|-------|
| Stop Loss | 2.5% |
| Target 1 | 10% |
| Target 2 | 20% |
| Score mínimo | 7.5/10 |
| Market cap mínimo | $100M |
| Coins analizadas | 25 tradeable |
| Schedule | Miércoles 21:00 + Domingo 18:00 CET |

## 📁 Estructura del Proyecto

```
analizador_activos_monedas/
├── app.py                      # Flask app + scheduler
├── render.yaml                 # Configuración Render
├── requirements.txt            # Dependencias
├── .gitignore                 
├── README.md                  
├── DEPLOYMENT_GUIDE.md        # Guía paso a paso
├── src/
│   ├── __init__.py
│   ├── data_collector.py      # CoinGecko API
│   ├── technical_analyzer.py  # Indicadores técnicos
│   ├── scoring_selector.py    # Sistema de scoring
│   └── telegram_notifier.py   # Notificaciones
└── data/                      # Datos generados (git-ignored)
    └── .gitkeep
```

## 🚀 Quick Start

### 1. Clonar repositorio

```bash
git clone https://github.com/tu-usuario/analizador_activos_monedas.git
cd analizador_activos_monedas
```

### 2. Configurar Telegram Bot

1. Busca **@BotFather** en Telegram
2. Crea bot: `/newbot`
3. Guarda el **TOKEN**
4. Obtén **CHAT_ID**: `https://api.telegram.org/bot<TOKEN>/getUpdates`

### 3. Deploy en Render

1. Ve a [render.com](https://render.com)
2. **New** → **Web Service**
3. Conecta tu repo de GitHub
4. Añade variables de entorno:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
5. Click **Create Web Service**

¡Listo! El sistema se ejecutará automáticamente.

## 🔌 Endpoints API

| Endpoint | Descripción |
|----------|-------------|
| `/` | Información del sistema |
| `/health` | Health check |
| `/status` | Estado último análisis |
| `/analyze` | Trigger manual |
| `/test` | Test Telegram |

**Ejemplos:**

```bash
# Ver status
curl https://tu-servicio.onrender.com/status

# Trigger análisis
curl https://tu-servicio.onrender.com/analyze

# Test Telegram
curl https://tu-servicio.onrender.com/test
```

## ⏰ Schedule Automático

- **Miércoles 21:00 CET**: Análisis principal semanal
- **Domingo 18:00 CET**: Actualización

Recibirás reportes automáticos en Telegram.

## 📊 Sistema de Scoring

### Fórmula:

```
Final Score = (
    Momentum × 0.35 +
    Volume × 0.25 +
    Technical × 0.25 +
    Risk × 0.15
) × Market Cap Multiplier
```

### Market Cap Multiplier:

- **>$10B**: ×1.1 (BTC, ETH)
- **$1-10B**: ×1.0
- **$100M-1B**: ×0.95
- **<$100M**: Excluido

## 🔧 Configuración

### Cambiar horarios

Edita `app.py`:

```python
scheduler.add_job(
    func=run_crypto_analysis,
    trigger=CronTrigger(day_of_week='wed', hour=21, minute=0),
    # Cambiar según necesites
)
```

### Ajustar parámetros

Edita `src/scoring_selector.py`:

```python
MIN_SCORE = 7.5  # Score mínimo
MIN_MARKET_CAP = 100_000_000  # $100M
```

### Cambiar stop loss / targets

Edita `src/scoring_selector.py`, método `calculate_levels()`:

```python
stop_loss = price * 0.975  # -2.5%
target_1 = price * 1.10    # +10%
target_2 = price * 1.20    # +20%
```

## 🐛 Troubleshooting

### Servicio no arranca

- Verifica logs en Render dashboard
- Revisa `requirements.txt` correcto
- Comprueba variables de entorno

### No llegan notificaciones

- Usa `/test` endpoint
- Verifica secrets en Render
- Revisa logs del servicio

### Rate Limiting (429)

- Aumenta `REQUEST_DELAY` en `data_collector.py`
- Reduce coins procesadas de 25 a 20

## 💰 Costos

| Servicio | Costo |
|----------|-------|
| Render.com (Free) | $0/mes |
| CoinGecko API | $0/mes |
| Telegram | $0/mes |
| **TOTAL** | **$0/mes** 🎉 |

**Nota:** Render Free se pausa tras 15 min sin actividad pero se reactiva automáticamente.

## 📈 Roadmap

- [ ] Dashboard web con histórico
- [ ] Backtesting engine
- [ ] Más indicadores (Bollinger, Ichimoku)
- [ ] Integración con exchanges
- [ ] Paper trading automático

## ⚠️ Disclaimer

Sistema para **fines educativos** únicamente.

- ❌ No es asesoramiento financiero
- ⚠️ Alto riesgo - Las criptomonedas son volátiles
- ✅ DYOR (Do Your Own Research)
- ✅ Solo invierte lo que puedas perder

## 📝 Licencia

MIT License

## 🙏 Créditos

- [CoinGecko](https://www.coingecko.com/) - API gratuita
- [Render](https://render.com/) - Hosting gratuito
- [APScheduler](https://apscheduler.readthedocs.io/) - Scheduling

---

**Good luck trading! 🚀📈**
