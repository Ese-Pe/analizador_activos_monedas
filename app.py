"""
Crypto Swing Trading System - Flask App for Render.com
Main application with scheduler and health checks
"""

import os
import logging
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
from datetime import datetime
import pytz

# Import analysis modules
from src.data_collector import CoinGeckoDataAgent
from src.technical_analyzer import TechnicalAnalyzer
from src.scoring_selector import ScoringSelector
from src.telegram_notifier import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Global variables for status tracking
last_run = {"time": None, "status": "Never run", "signals": 0}


def run_crypto_analysis():
    """Execute the complete crypto analysis pipeline"""
    global last_run
    
    try:
        logger.info("🚀 Starting Crypto Analysis Pipeline")
        start_time = datetime.now()
        
        # Agent 1: Data Collection
        data_agent = CoinGeckoDataAgent(top_n=100)
        crypto_data = data_agent.collect_data()
        
        if not crypto_data['coins']:
            logger.error("No coin data collected")
            last_run = {
                "time": start_time.isoformat(),
                "status": "Failed - No data",
                "signals": 0
            }
            return
        
        # Agent 2: Technical Analysis
        analyzer = TechnicalAnalyzer()
        technical_data = analyzer.analyze_all(crypto_data)
        
        if not technical_data['analyzed_coins']:
            logger.error("No coins analyzed")
            last_run = {
                "time": start_time.isoformat(),
                "status": "Failed - Analysis error",
                "signals": 0
            }
            return
        
        # Agent 3: Scoring & Selection
        selector = ScoringSelector()
        top_signals = selector.select_top_opportunities(technical_data)
        
        # Agent 4: Send Notifications
        telegram = TelegramNotifier()
        
        # Load data for reporting
        import json
        with open('data/selected_cryptos.json', 'r') as f:
            data = json.load(f)
        
        telegram.send_analysis_report(data)
        
        # Send high-score alerts
        for signal in top_signals:
            telegram.send_high_score_alert(signal)
        
        # Update status
        duration = (datetime.now() - start_time).total_seconds()
        last_run = {
            "time": start_time.isoformat(),
            "status": "Success",
            "signals": len(top_signals),
            "duration_seconds": round(duration, 2)
        }
        
        logger.info(f"✅ Analysis complete! {len(top_signals)} signals found in {duration:.1f}s")
        
    except Exception as e:
        logger.error(f"❌ Error in analysis pipeline: {e}", exc_info=True)
        last_run = {
            "time": datetime.now().isoformat(),
            "status": f"Failed - {str(e)}",
            "signals": 0
        }


# Initialize scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone('Europe/Madrid'))

# Schedule jobs: # Todos los días a las 9:30 AM CET
scheduler.add_job(
    func=run_crypto_analysis,
    trigger=CronTrigger(hour=9, minute=30, timezone='Europe/Madrid'),
    id='daily_analysis',
    name='Daily Crypto Analysis',
    replace_existing=True
)

# Keep-alive ping cada 10 minutos para evitar que Render pause el servicio
scheduler.add_job(
    func=lambda: logger.info("⏰ Keep-alive ping"),
    trigger='interval',
    minutes=10,
    id='keep_alive',
    name='Keep Alive'
)

# Start scheduler
scheduler.start()
logger.info("✅ Scheduler started successfully")

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())


@app.route('/')
def home():
    """Home endpoint with system info"""
    return jsonify({
        "service": "Crypto Swing Trading System",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "/": "This info page",
            "/health": "Health check",
            "/status": "Last run status",
            "/analyze": "Trigger manual analysis",
            "/test": "Test Telegram connection"
        }
    })


@app.route('/health')
def health():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scheduler": scheduler.running
    }), 200


@app.route('/status')
def status():
    """Get status of last analysis run"""
    return jsonify({
        "last_run": last_run,
        "scheduled_jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    })


@app.route('/analyze')
def analyze():
    """Manually trigger analysis"""
    try:
        # Run analysis in background
        scheduler.add_job(
            func=run_crypto_analysis,
            trigger='date',
            id='manual_trigger',
            name='Manual Analysis',
            replace_existing=True
        )
        return jsonify({
            "status": "Analysis triggered",
            "message": "Analysis started in background. Check /status for results."
        }), 202
    except Exception as e:
        logger.error(f"Error triggering analysis: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/test')
def test_telegram():
    """Test Telegram connection"""
    try:
        telegram = TelegramNotifier()
        success = telegram.send_message("✅ Test message from Crypto Trading System")
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Test message sent to Telegram"
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to send message - check logs"
            }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    # Get port from environment (Render provides this)
    port = int(os.environ.get('PORT', 10000))
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False
    )
