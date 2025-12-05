#!/usr/bin/env python3
"""
Script de prueba para testear componentes individuales.
Ejecutar: python -m scripts.test_components
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_config():
    """Probar carga de configuración."""
    print("\n" + "="*50)
    print("🔧 TEST: Configuración")
    print("="*50)
    
    from src.utils.config import Config
    
    config = Config()
    print(f"✓ Camera device: {config.camera.device_id}")
    print(f"✓ MIDI port: {config.midi.port_name}")
    print(f"✓ MIDI velocity: {config.midi.velocity}")
    print(f"✓ Database path: {config.database.path}")
    print(f"✓ Pinch threshold: {config.thresholds.pinch_epsilon}")
    
    return config


def test_note_mapper(config):
    """Probar el mapeo de notas."""
    print("\n" + "="*50)
    print("🎵 TEST: Note Mapper")
    print("="*50)
    
    from src.music.note_mapper import NoteMapper
    
    mapper = NoteMapper(config)
    
    # Probar cuerdas abiertas
    print("\nCuerdas abiertas:")
    strings = {1: "E", 2: "A", 3: "D", 4: "G"}
    for string_num, string_name in strings.items():
        note = mapper.get_note(string=string_num, position=1, finger_count=0)
        info = mapper.get_note_info(string=string_num, position=1, finger_count=0)
        print(f"  {string_name} string (#{string_num}): MIDI {note} = {info.note_name}")
    
    # Probar dedos en cuerda A
    print("\nCuerda A con diferentes dedos (1ª posición):")
    for finger in range(5):
        info = mapper.get_note_info(string=2, position=1, finger_count=finger)
        finger_name = "Abierta" if finger == 0 else f"Dedo {finger}"
        print(f"  {finger_name}: MIDI {info.midi_note} = {info.note_name}")
    
    # Probar posiciones
    print("\nCuerda A, dedo 1, diferentes posiciones:")
    for pos in range(1, 4):
        info = mapper.get_note_info(string=2, position=pos, finger_count=1)
        print(f"  Posición {pos}: MIDI {info.midi_note} = {info.note_name}")
    
    return mapper


def test_midi_controller(config):
    """Probar el controlador MIDI."""
    print("\n" + "="*50)
    print("🎹 TEST: MIDI Controller")
    print("="*50)
    
    try:
        from src.music.midi_controller import MIDIController
        
        controller = MIDIController(config)
        
        print(f"\n✓ Puertos MIDI disponibles:")
        ports = controller.get_available_ports()
        if ports:
            for i, port in enumerate(ports):
                print(f"  [{i}] {port}")
        else:
            print("  (Ninguno - se creará puerto virtual)")
        
        # Tocar una escala simple
        print("\n🎵 Tocando escala de A mayor...")
        notes = [69, 71, 73, 74, 76, 78, 80, 81]  # A major scale
        
        for note in notes:
            controller.note_on(note)
            time.sleep(0.3)
            controller.note_off(note)
            time.sleep(0.1)
        
        print("✓ Escala completada")
        
        controller.close()
        return True
        
    except Exception as e:
        print(f"✗ Error MIDI: {e}")
        print("  (Instala python-rtmidi y configura un puerto MIDI virtual)")
        return False


def test_gesture_recognizer(config):
    """Probar el reconocedor de gestos con datos simulados."""
    print("\n" + "="*50)
    print("🖐️ TEST: Gesture Recognizer")
    print("="*50)
    
    from src.vision.gesture_recognizer import GestureRecognizer
    from src.vision.hand_detector import HandLandmarks
    
    recognizer = GestureRecognizer(config)
    
    # Crear mano simulada
    def create_mock_hand(handedness, thumb_tip, index_tip, extended_fingers):
        """Crear landmarks simulados."""
        landmarks = [(0.5, 0.5, 0.0)] * 21
        landmarks[4] = thumb_tip   # Thumb tip
        landmarks[8] = index_tip   # Index tip
        
        # Simular dedos extendidos
        pip_y = 0.5
        for i, (tip_idx, pip_idx) in enumerate([(8, 6), (12, 10), (16, 14), (20, 18)]):
            if i < extended_fingers:
                landmarks[tip_idx] = (0.5, pip_y - 0.1, 0.0)  # Extended
            else:
                landmarks[tip_idx] = (0.5, pip_y + 0.1, 0.0)  # Curled
            landmarks[pip_idx] = (0.5, pip_y, 0.0)
        
        return HandLandmarks(landmarks=landmarks, handedness=handedness, confidence=0.95)
    
    # Test 1: Mano derecha con pinch (tocar nota)
    print("\n1. Mano derecha con pinch + 2 dedos:")
    right_hand = create_mock_hand(
        handedness="Right",
        thumb_tip=(0.5, 0.5, 0.0),
        index_tip=(0.51, 0.51, 0.0),  # Muy cerca = pinch
        extended_fingers=2
    )
    gestures = recognizer.recognize([right_hand])
    print(f"   Bow active: {gestures['bow_active']} (esperado: True)")
    print(f"   String: {gestures['string']} (esperado: 2 = A)")
    
    # Test 2: Mano derecha sin pinch
    print("\n2. Mano derecha sin pinch + 3 dedos:")
    right_hand = create_mock_hand(
        handedness="Right",
        thumb_tip=(0.3, 0.5, 0.0),
        index_tip=(0.7, 0.3, 0.0),  # Lejos = no pinch
        extended_fingers=3
    )
    gestures = recognizer.recognize([right_hand])
    print(f"   Bow active: {gestures['bow_active']} (esperado: False)")
    print(f"   String: {gestures['string']} (esperado: 3 = D)")
    
    # Test 3: Ambas manos
    print("\n3. Ambas manos (tocar A en 2ª posición):")
    right_hand = create_mock_hand(
        handedness="Right",
        thumb_tip=(0.5, 0.5, 0.0),
        index_tip=(0.51, 0.51, 0.0),
        extended_fingers=2  # A string
    )
    left_hand = create_mock_hand(
        handedness="Left",
        thumb_tip=(0.5, 0.5, 0.0),  # Mid Y = 2nd position
        index_tip=(0.5, 0.3, 0.0),
        extended_fingers=0
    )
    gestures = recognizer.recognize([right_hand, left_hand])
    print(f"   Bow: {gestures['bow_active']}, String: {gestures['string']}, Position: {gestures['position']}")
    
    return recognizer


def test_database(config):
    """Probar el sistema de base de datos."""
    print("\n" + "="*50)
    print("💾 TEST: Database & Logger")
    print("="*50)
    
    from src.database.logger import PerformanceLogger
    
    logger = PerformanceLogger(config)
    
    # Iniciar sesión
    print("\n1. Iniciando sesión de práctica...")
    session = logger.start_session()
    print(f"   ✓ Session ID: {session.id}")
    
    # Simular algunas notas
    print("\n2. Registrando notas...")
    test_notes = [
        (69, {"string": 2, "position": 1, "finger_count": 0, "pitch_offset": 0}),
        (71, {"string": 2, "position": 1, "finger_count": 1, "pitch_offset": 0}),
        (73, {"string": 2, "position": 1, "finger_count": 2, "pitch_offset": 0}),
        (69, {"string": 2, "position": 1, "finger_count": 0, "pitch_offset": 0}),
    ]
    
    for midi_note, gestures in test_notes:
        logger.log_note(midi_note, gestures)
        time.sleep(0.15)  # Simular tiempo entre notas
        print(f"   ✓ Logged note: {midi_note}")
    
    # Finalizar sesión
    print("\n3. Finalizando sesión...")
    final_session = logger.end_session()
    
    if final_session:
        print(f"   ✓ Total notas: {final_session.total_notes}")
        print(f"   ✓ Notas únicas: {final_session.unique_notes}")
        if final_session.duration_minutes:
            print(f"   ✓ Duración: {final_session.duration_minutes:.2f} min")
    
    # Obtener estadísticas
    print("\n4. Estadísticas de la sesión:")
    stats = logger.get_session_stats(session.id)
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    return logger


def run_all_tests():
    """Ejecutar todas las pruebas."""
    print("\n" + "🎻"*25)
    print("   VIOLIN AUTO-PLAYING - TEST SUITE")
    print("🎻"*25)
    
    # 1. Config
    config = test_config()
    
    # 2. Note Mapper
    test_note_mapper(config)
    
    # 3. Gesture Recognizer
    test_gesture_recognizer(config)
    
    # 4. Database
    test_database(config)
    
    # 5. MIDI (puede fallar si no hay puerto)
    test_midi_controller(config)
    
    print("\n" + "="*50)
    print("✅ TESTS COMPLETADOS")
    print("="*50)


if __name__ == "__main__":
    run_all_tests()
