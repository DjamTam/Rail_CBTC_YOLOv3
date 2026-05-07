from flask import Flask, jsonify, Response
import threading

def create_app(shared_status: dict, status_lock: threading.Lock):
    """
    Créer une application Flask pour exposer le statut en temps réel via REST API
    
    Args:
        shared_status: Dictionnaire partagé contenant le statut actuel
        status_lock: Verrou pour éviter les conditions de course (thread-safety)
        
    Returns:
        Application Flask prête à être lancée
    """
    app = Flask(__name__)

    @app.get("/health")
    def health():
        """
        Endpoint de santé (health check)
        Utilisé pour vérifier si le serveur est opérationnel
        """
        try:
            return jsonify({"status": "ok"})
        except Exception as e:
            print(f"Erreur health: {e}")
            return jsonify({"error": str(e)}), 500

    @app.get("/status")
    def status():
        """
        Endpoint principal: retourne le statut en temps réel de la supervision
        
        Retourne:
        {
            "decision": "SAFE|UNCERTAIN|STOP_REQUEST|COOLDOWN",
            "persons_in_roi": 2,
            "max_confidence": 0.92,
            "fps_avg": 25.3,
            "recent_events": [...]  # Derniers événements enregistrés
        }
        """
        try:
            with status_lock:  # Verrou pour éviter les modifications concurrentes
                # Copier le dictionnaire pour éviter les problèmes de sérialisation JSON
                status_copy = dict(shared_status)
            return jsonify(status_copy)
        except Exception as e:
            print(f"Erreur endpoint status: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.get("/")
    def dashboard():
        """
        Dashboard interactif : affichage en temps réel du système de supervision Rail/CBTC
        Thème Siemens avec design industriel professionnel
        
        Interroge l'endpoint /status toutes les 500 ms pour mettre à jour l'affichage
        Affiche: décision, détections (personnes/voitures), confiance, performance
        """
        html = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Rail/CBTC Supervision — Siemens Dashboard</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    /* Siemens Color Scheme: Professional dark blues and grays with teal accents */
    body {
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      background: linear-gradient(135deg, #0a0f1b 0%, #1a2540 100%);
      color: #e1e8f0;
      padding: 20px;
      min-height: 100vh;
    }
    
    .container {
      max-width: 1200px;
      margin: 0 auto;
    }
    
    /* Header with Siemens branding */
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 32px;
      padding-bottom: 16px;
      border-bottom: 2px solid #00a6d6;
    }
    
    .header-left h1 {
      font-size: 28px;
      color: #00a6d6;
      font-weight: 600;
      margin-bottom: 6px;
    }
    
    .header-left p {
      font-size: 13px;
      color: #8b95aa;
      margin-bottom: 4px;
    }
    
    .header-right {
      text-align: right;
    }
    
    .status-indicator {
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background: #00d48c;
      margin-right: 8px;
      animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    .header-right p {
      font-size: 12px;
      color: #8b95aa;
    }
    
    /* KPI Cards Grid */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin-bottom: 32px;
    }
    
    .kpi-card {
      background: linear-gradient(135deg, #141f35 0%, #1a2945 100%);
      border: 1px solid #2a3d5c;
      border-radius: 12px;
      padding: 24px;
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    
    .kpi-card::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, #00a6d6, #00d48c);
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    
    .kpi-card:hover {
      border-color: #00a6d6;
      box-shadow: 0 8px 24px rgba(0, 166, 214, 0.15);
    }
    
    .kpi-label {
      font-size: 13px;
      color: #8b95aa;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 12px;
      font-weight: 500;
    }
    
    .kpi-value {
      font-size: 36px;
      font-weight: 700;
      color: #e1e8f0;
      margin-bottom: 8px;
    }
    
    .kpi-unit {
      font-size: 12px;
      color: #8b95aa;
    }
    
    /* Decision Badge - Status Colors */
    .decision-badge {
      display: inline-block;
      padding: 8px 16px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border: 2px solid;
      transition: all 0.3s ease;
    }
    
    .badge-safe {
      background: rgba(0, 212, 140, 0.15);
      border-color: #00d48c;
      color: #00d48c;
      box-shadow: inset 0 0 8px rgba(0, 212, 140, 0.1);
    }
    
    .badge-uncertain {
      background: rgba(255, 193, 7, 0.15);
      border-color: #ffc107;
      color: #ffc107;
      box-shadow: inset 0 0 8px rgba(255, 193, 7, 0.1);
    }
    
    .badge-stop {
      background: rgba(255, 87, 87, 0.15);
      border-color: #ff5757;
      color: #ff5757;
      box-shadow: inset 0 0 8px rgba(255, 87, 87, 0.1);
      animation: pulse-danger 1s infinite;
    }
    
    @keyframes pulse-danger {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.7; }
    }
    
    .badge-cooldown {
      background: rgba(100, 150, 255, 0.15);
      border-color: #6496ff;
      color: #6496ff;
      box-shadow: inset 0 0 8px rgba(100, 150, 255, 0.1);
    }
    
    /* Event History Section */
    .events-section {
      background: linear-gradient(135deg, #141f35 0%, #1a2945 100%);
      border: 1px solid #2a3d5c;
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
    }
    
    .events-header {
      font-size: 16px;
      font-weight: 600;
      color: #00a6d6;
      margin-bottom: 16px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    
    .event-item {
      display: grid;
      grid-template-columns: 80px 120px 1fr;
      gap: 16px;
      padding: 12px;
      margin-bottom: 10px;
      background: rgba(10, 15, 27, 0.4);
      border-left: 3px solid #00a6d6;
      border-radius: 4px;
      font-size: 13px;
    }
    
    .event-badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 4px;
      font-weight: 600;
      font-size: 11px;
      text-align: center;
      text-transform: uppercase;
    }
    
    .event-safe { background: rgba(0, 212, 140, 0.2); color: #00d48c; }
    .event-uncertain { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
    .event-stop { background: rgba(255, 87, 87, 0.2); color: #ff5757; }
    .event-cooldown { background: rgba(100, 150, 255, 0.2); color: #6496ff; }
    
    .event-time {
      color: #8b95aa;
      font-size: 12px;
    }
    
    .event-details {
      color: #c4cde0;
      display: flex;
      gap: 16px;
    }
    
    .event-empty {
      color: #8b95aa;
      font-style: italic;
      padding: 20px;
      text-align: center;
    }
    
    /* Footer with API links */
    .footer {
      border-top: 1px solid #2a3d5c;
      padding-top: 16px;
      font-size: 12px;
      color: #8b95aa;
      text-align: center;
    }
    
    .footer a {
      color: #00a6d6;
      text-decoration: none;
      margin: 0 8px;
    }
    
    .footer a:hover {
      text-decoration: underline;
      color: #00d48c;
    }
    
    /* Siemens branding footer text */
    .siemens-mark {
      font-size: 11px;
      color: #555;
      margin-top: 8px;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
      .header {
        flex-direction: column;
        text-align: left;
        align-items: flex-start;
      }
      
      .header-right {
        text-align: left;
        margin-top: 12px;
      }
      
      .event-item {
        grid-template-columns: 1fr;
      }
      
      .kpi-value {
        font-size: 28px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <!-- Header with Siemens Branding -->
    <div class="header">
      <div class="header-left">
        <h1>🚆 Rail/CBTC Supervision</h1>
        <p>Système de Supervision Intelligent — Détection Temps Réel</p>
      </div>
      <div class="header-right">
        <div>
          <span class="status-indicator"></span>
          <p id="serverStatus">Connecté</p>
        </div>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-grid">
      <!-- Decision Card -->
      <div class="kpi-card">
        <div class="kpi-label">État Décision</div>
        <div class="kpi-value">
          <span id="decisionBadge" class="decision-badge badge-safe">SAFE</span>
        </div>
        <div class="kpi-unit">État opérationnel du système</div>
      </div>

      <!-- Persons Card -->
      <div class="kpi-card">
        <div class="kpi-label">Personnes dans la ROI</div>
        <div class="kpi-value" id="personsCount">0</div>
        <div class="kpi-unit">Détections en zone de supervision</div>
      </div>

      <!-- Cars Card -->
      <div class="kpi-card">
        <div class="kpi-label">Véhicules dans la ROI</div>
        <div class="kpi-value" id="carsCount">0</div>
        <div class="kpi-unit">Voitures détectées en ROI</div>
      </div>

      <!-- Confidence Card -->
      <div class="kpi-card">
        <div class="kpi-label">Confiance Max</div>
        <div class="kpi-value" id="confidence">0.00</div>
        <div class="kpi-unit">Score de fiabilité le plus élevé</div>
      </div>

      <!-- FPS Card -->
      <div class="kpi-card">
        <div class="kpi-label">Performance (FPS)</div>
        <div class="kpi-value" id="fps">0.0</div>
        <div class="kpi-unit">Images par seconde (moyenne)</div>
      </div>

      <!-- Frames Processed Card -->
      <div class="kpi-card">
        <div class="kpi-label">Images Traitées</div>
        <div class="kpi-value" id="frameCount">0</div>
        <div class="kpi-unit">Nombre total de frames</div>
      </div>
    </div>

    <!-- Recent Events -->
    <div class="events-section">
      <div class="events-header">📋 Historique des Événements (5 derniers)</div>
      <div id="eventList">
        <div class="event-empty">En attente de données...</div>
      </div>
    </div>

    <!-- Footer -->
    <div class="footer">
      Mise à jour automatique toutes les <strong>500 ms</strong>
      <br />
      Endpoints API: <a href="/health">/health</a> · <a href="/status">/status</a>
      <div class="siemens-mark">Rail/CBTC Supervision • Powered by Siemens Mobility • YOLOv3 Detection</div>
    </div>
  </div>

  <script>
    /**
     * Détermine la classe CSS du badge de décision
     */
    function getBadgeClass(decision) {
      const decisionMap = {
        'SAFE': 'badge-safe',
        'UNCERTAIN': 'badge-uncertain',
        'STOP_REQUEST': 'badge-stop',
        'COOLDOWN': 'badge-cooldown'
      };
      return decisionMap[decision] || 'badge-uncertain';
    }

    /**
     * Détermine la classe CSS du badge d'événement
     */
    function getEventBadgeClass(event) {
      const eventMap = {
        'SAFE': 'event-safe',
        'UNCERTAIN': 'event-uncertain',
        'STOP_REQUEST': 'event-stop',
        'COOLDOWN': 'event-cooldown'
      };
      return eventMap[event] || 'event-uncertain';
    }

    /**
     * Formate un timestamp Unix en heure lisible
     */
    function formatTime(timestamp) {
      const date = new Date(timestamp * 1000);
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    /**
     * Met à jour le tableau de bord via l'endpoint /status
     */
    async function updateDashboard() {
      try {
        const response = await fetch('/status', { cache: 'no-store' });
        const data = await response.json();

        // Mise à jour des valeurs
        const decision = data.decision || 'SAFE';
        const persons = data.persons_in_roi || 0;
        const cars = data.cars_in_roi || 0;
        const confidence = (data.max_confidence || 0).toFixed(2);
        const fps = (data.fps_avg || 0).toFixed(1);
        const frameCount = data.frame_count || 0;

        // Mise à jour du badge de décision
        const decisionBadge = document.getElementById('decisionBadge');
        decisionBadge.textContent = decision;
        decisionBadge.className = 'decision-badge ' + getBadgeClass(decision);

        // Mise à jour des valeurs KPI
        document.getElementById('personsCount').textContent = persons;
        document.getElementById('carsCount').textContent = cars;
        document.getElementById('confidence').textContent = confidence;
        document.getElementById('fps').textContent = fps;
        document.getElementById('frameCount').textContent = frameCount;

        // Mise à jour du statut serveur
        document.getElementById('serverStatus').textContent = 'Connecté';

        // Mise à jour de l'historique des événements
        if (data.recent_events && data.recent_events.length > 0) {
          const eventList = document.getElementById('eventList');
          const recentEvents = data.recent_events.slice(-5).reverse(); // 5 derniers événements
          
          eventList.innerHTML = recentEvents.map(evt => {
            const timeStr = formatTime(evt.ts || Date.now() / 1000);
            const eventBadge = evt.event || 'UNKNOWN';
            const badgeClass = getEventBadgeClass(eventBadge);
            
            return `<div class="event-item">
              <span class="event-badge ${badgeClass}">${eventBadge}</span>
              <span class="event-time">${timeStr}</span>
              <div class="event-details">
                <span>👤 ${evt.persons_in_roi || 0}</span>
                <span>🎯 ${(evt.max_confidence || 0).toFixed(2)}</span>
              </div>
            </div>`;
          }).join('');
        }

      } catch (error) {
        console.error('Erreur de connexion au serveur:', error);
        document.getElementById('serverStatus').textContent = 'Déconnecté';
      }
    }

    // Mise à jour initiale et actualisations périodiques
    updateDashboard();
    setInterval(updateDashboard, 500);
  </script>
</body>
</html>"""
        return Response(html, mimetype="text/html")

    return app
