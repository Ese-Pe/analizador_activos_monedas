# 🚀 Guía de Deployment en Render.com

Guía paso a paso para deployar el sistema en Render.com sin violar términos de GitHub.

---

## ✅ Pre-requisitos

- [ ] Cuenta de GitHub
- [ ] Cuenta de Render.com (gratuita)
- [ ] Bot de Telegram configurado

---

## 📋 PASO 1: Subir a GitHub

### 1.1 Crear repositorio

1. Ve a [github.com](https://github.com) → **"New repository"**
2. Nombre: `analizador_activos_monedas`
3. Público/Privado según prefieras
4. **NO** añadir README (ya lo tenemos)
5. **Create repository**

### 1.2 Subir archivos

**Estructura completa:**

```
analizador_activos_monedas/
├── app.py
├── render.yaml
├── requirements.txt
├── .gitignore
├── README.md
├── DEPLOYMENT_GUIDE.md
├── src/
│   ├── __init__.py
│   ├── data_collector.py
│   ├── technical_analyzer.py
│   ├── scoring_selector.py
│   └── telegram_notifier.py
└── data/
    └── .gitkeep
```

**Opción A - Desde navegador:**

Para cada archivo:
1. **Add file** → **Create new file**
2. Nombre (ej: `app.py` o `src/data_collector.py`)
3. Pegar contenido
4. **Commit new file**

**Opción B - Desde terminal:**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/analizador_activos_monedas.git
git branch -M main
git push -u origin main
```

---

## 🤖 PASO 2: Configurar Telegram

### 2.1 Crear Bot

1. Telegram → Busca **@BotFather**
2. Envía: `/newbot`
3. Nombre: `Crypto Swing Trading`
4. Username: `tu_crypto_bot` (termina en `bot`)
5. **Copia TOKEN**: `123456789:ABCdef...`

### 2.2 Obtener Chat ID

**Chat personal:**
```
1. Envía /start a tu bot
2. Abre: https://api.telegram.org/bot<TOKEN>/getUpdates
3. Busca: "chat":{"id":123456789}
```

**Grupo:**
```
1. Crea grupo y añade bot
2. Envía mensaje en grupo
3. Misma URL de arriba
4. Chat ID será negativo: -987654321
```

---

## 🌐 PASO 3: Deploy en Render

### 3.1 Crear cuenta

1. [render.com](https://render.com) → **Get Started**
2. Regístrate con GitHub (recomendado)
3. Autoriza acceso a repositorios

### 3.2 Crear Web Service

1. Dashboard → **New +** → **Web Service**
2. Selecciona `analizador_activos_monedas`
3. Render auto-detecta `render.yaml`

**Configuración:**

| Campo | Valor |
|-------|-------|
| Name | crypto-swing-trading |
| Region | Frankfurt |
| Build Command | pip install -r requirements.txt |
| Start Command | python app.py |

### 3.3 Variables de Entorno

**IMPORTANTE:** Añade antes de deploy:

1. Scroll a **Environment Variables**
2. **Add Environment Variable**

| Key | Value |
|-----|-------|
| `TELEGRAM_BOT_TOKEN` | Tu token de BotFather |
| `TELEGRAM_CHAT_ID` | Tu chat ID |

### 3.4 Deploy

1. **Create Web Service**
2. Espera 3-5 minutos (verás logs)
3. Estado: **Live** ✅

URL: `https://crypto-swing-trading-XXXX.onrender.com`

---

## ✅ PASO 4: Verificar

### 4.1 Health Check

```
https://tu-servicio.onrender.com/health
```

Respuesta esperada:
```json
{
  "status": "healthy",
  "scheduler": true
}
```

### 4.2 Test Telegram

```
https://tu-servicio.onrender.com/test
```

Deberías recibir mensaje en Telegram.

### 4.3 Análisis Manual

```
https://tu-servicio.onrender.com/analyze
```

En 2-3 min recibirás reporte completo.

### 4.4 Ver Status

```
https://tu-servicio.onrender.com/status
```

---

## 📊 PASO 5: Monitoreo

### En Render Dashboard:

- **Logs:** Ver en tiempo real
- **Metrics:** CPU/Memoria
- **Events:** Historial deploys

### Schedule automático:

- Miércoles 21:00 CET
- Domingo 18:00 CET

---

## 🔧 Ajustes Post-Deploy

### Cambiar horarios

Edita `app.py` en GitHub:

```python
# Línea ~70
day_of_week='wed', hour=21  # Modificar
```

Commit → Render redeploya automáticamente.

### Ajustar parámetros

Edita `src/scoring_selector.py`:

```python
MIN_SCORE = 7.5  # Cambiar
stop_loss = price * 0.975  # Cambiar %
```

---

## ⚠️ Troubleshooting

### Build falla

- Verifica `requirements.txt` en raíz
- Revisa logs en Render

### Servicio pausado

- Normal en free tier (15 min inactividad)
- Se reactiva automáticamente

### No llegan mensajes

1. Verifica variables en Render
2. Usa endpoint `/test`
3. Revisa logs

### Rate Limiting (429)

Edita `src/data_collector.py`:

```python
REQUEST_DELAY = 4.0  # Aumentar de 3.0
```

---

## ✅ Checklist Final

- [ ] Repo en GitHub con todos archivos
- [ ] Bot Telegram configurado
- [ ] Servicio deployado en Render
- [ ] Variables configuradas
- [ ] Health check OK
- [ ] Test Telegram OK
- [ ] Análisis manual exitoso
- [ ] Schedule verificado

**¡Listo! Sistema funcionando automáticamente.** 🎉

---

**¿Problemas?** Revisa logs en Render Dashboard o abre issue en GitHub.

**Good luck! 🚀📈**
