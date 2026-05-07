from src.decision import SafetyDecision
import time

def test_confirm_frames():
    """
    Teste la logique de confirmation avec N frames consécutives
    
    Scénario:
    1. Pas de détection → SAFE/UNCERTAIN
    2. 1 détection → UNCERTAIN
    3. 2 détections → UNCERTAIN
    4. 3 détections (seuil atteint) → STOP_REQUEST
    """
    d = SafetyDecision(confirm_frames=3, cooldown_seconds=0.0)
    
    # Aucune alerte avant le seuil
    assert d.update(False) in ("SAFE", "UNCERTAIN")
    assert d.update(True) == "UNCERTAIN"  # 1ère détection
    assert d.update(True) == "UNCERTAIN"  # 2e détection
    
    # Au 3e détection → alerte!
    assert d.update(True) == "STOP_REQUEST"

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
    d = SafetyDecision(confirm_frames=2, cooldown_seconds=2.0)
    
    # Première accumulation
    assert d.update(True) == "UNCERTAIN"
    assert d.update(True) == "STOP_REQUEST"  # Alerte première!
    
    # Toujours détection mais cooldown actif
    assert d.update(True) == "COOLDOWN"  # Attendre...
    
    # Attendre que le cooldown expire
    time.sleep(2.0)
    
    # Nouvelle alerte possible
    assert d.update(True) == "STOP_REQUEST"  # Alerte deuxième!
