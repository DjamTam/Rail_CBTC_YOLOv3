from src.decision import SafetyDecision
import time
import logging

# Configure logging for terminal output
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_confirm_frames():
    """
    Teste la logique de confirmation avec N frames consécutives
    
    Scénario:
    1. Pas de détection → SAFE/UNCERTAIN
    2. 1 détection → UNCERTAIN
    3. 2 détections → UNCERTAIN
    4. 3 détections (seuil atteint) → STOP_REQUEST
    """
    logger.info("🧪 Test: Confirmation Frames (confirm_frames=3, cooldown=0)")
    d = SafetyDecision(confirm_frames=3, cooldown_seconds=0.0)
    
    # Aucune alerte avant le seuil
    result1 = d.update(False)
    logger.info(f"  Frame 0 (No detection) → {result1}")
    assert result1 in ("SAFE", "UNCERTAIN")
    
    result2 = d.update(True)
    logger.info(f"  Frame 1 (Detection #1) → {result2}")
    assert result2 == "UNCERTAIN"  # 1ère détection
    
    result3 = d.update(True)
    logger.info(f"  Frame 2 (Detection #2) → {result3}")
    assert result3 == "UNCERTAIN"  # 2e détection
    
    # Au 3e détection → alerte!
    result4 = d.update(True)
    logger.info(f"  Frame 3 (Detection #3) → {result4} ✅ Alert triggered!")
    assert result4 == "STOP_REQUEST"
    logger.info("✓ Test passed: Confirmation logic works correctly\n")

def test_cooldown():
    """
    Teste la logique du cooldown (délai entre alertes)
    
    Scénario:
    1. 1 détection → UNCERTAIN
    2. 2 détections (seuil) → STOP_REQUEST
    3. 3 détections (cooldown actif) → COOLDOWN
    4. Attendre 2.1 secondes
    5. 4 détections (cooldown écoulé) → STOP_REQUEST
    """
    logger.info("🧪 Test: Cooldown Logic (confirm_frames=2, cooldown=2.0s)")
    d = SafetyDecision(confirm_frames=2, cooldown_seconds=2.0)
    
    # Première accumulation
    result1 = d.update(True)
    logger.info(f"  Frame 1 (Detection #1) → {result1}")
    assert result1 == "UNCERTAIN"
    
    result2 = d.update(True)
    logger.info(f"  Frame 2 (Detection #2) → {result2} ✅ First alert!")
    assert result2 == "STOP_REQUEST"  # Alerte première!
    
    # Toujours détection mais cooldown actif
    result3 = d.update(True)
    logger.info(f"  Frame 3 (Detection during cooldown) → {result3} ⏳ Cooldown active")
    assert result3 == "COOLDOWN"  # Attendre...
    
    # Attendre que le cooldown expire
    logger.info("  ⏱️  Waiting 2.0 seconds for cooldown to expire...")
    time.sleep(2.0)
    
    # Nouvelle alerte possible
    result4 = d.update(True)
    logger.info(f"  Frame 4 (Detection after cooldown) → {result4} ✅ Second alert!")
    assert result4 == "STOP_REQUEST"  # Alerte deuxième!
    logger.info("✓ Test passed: Cooldown logic works correctly\n")
