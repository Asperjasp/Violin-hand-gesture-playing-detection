#!/usr/bin/env python3
"""
Demo interactivo del MIDI Controller.
Prueba el controlador MIDI sin necesidad de cámara.

Ejecutar: python -m scripts.midi_demo
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import Config
from src.music.midi_controller import MIDIController
from src.music.note_mapper import NoteMapper


def play_scale(controller: MIDIController, mapper: NoteMapper, string: int = 2):
    """Tocar una escala en una cuerda."""
    string_names = {1: "E", 2: "A", 3: "D", 4: "G"}
    print(f"\n🎵 Escala en cuerda {string_names[string]}:")
    
    for finger in range(5):
        note = mapper.get_note(string=string, position=1, finger_count=finger)
        info = mapper.get_note_info(string=string, position=1, finger_count=finger)
        
        print(f"  Dedo {finger}: {info.note_name} (MIDI {note})")
        controller.note_on(note)
        time.sleep(0.4)
        controller.note_off(note)
        time.sleep(0.1)


def play_open_strings(controller: MIDIController, mapper: NoteMapper):
    """Tocar las cuatro cuerdas abiertas."""
    print("\n🎻 Cuerdas abiertas (G → D → A → E):")
    
    for string in [4, 3, 2, 1]:  # G, D, A, E
        note = mapper.get_note(string=string, position=1, finger_count=0)
        info = mapper.get_note_info(string=string, position=1, finger_count=0)
        
        print(f"  Cuerda {info.string}: {info.note_name}")
        controller.note_on(note)
        time.sleep(0.5)
        controller.note_off(note)
        time.sleep(0.2)


def play_twinkle(controller: MIDIController):
    """Tocar Twinkle Twinkle Little Star en A."""
    print("\n⭐ Twinkle Twinkle Little Star:")
    
    # A A E E F# F# E - D D C# C# B B A
    melody = [
        (69, 0.4), (69, 0.4),  # A A
        (76, 0.4), (76, 0.4),  # E E
        (78, 0.4), (78, 0.4),  # F# F#
        (76, 0.8),             # E
        (74, 0.4), (74, 0.4),  # D D
        (73, 0.4), (73, 0.4),  # C# C#
        (71, 0.4), (71, 0.4),  # B B
        (69, 0.8),             # A
    ]
    
    for note, duration in melody:
        controller.note_on(note)
        time.sleep(duration)
        controller.note_off(note)
        time.sleep(0.05)


def interactive_mode(controller: MIDIController, mapper: NoteMapper):
    """Modo interactivo para probar notas."""
    print("\n🎮 MODO INTERACTIVO")
    print("="*40)
    print("Comandos:")
    print("  s1-s4    : Seleccionar cuerda (1=E, 2=A, 3=D, 4=G)")
    print("  f0-f4    : Dedo (0=abierta, 1-4=dedos)")
    print("  p1-p3    : Posición")
    print("  play     : Tocar nota actual")
    print("  scale    : Tocar escala en cuerda actual")
    print("  open     : Tocar cuerdas abiertas")
    print("  twinkle  : Tocar Twinkle Twinkle")
    print("  q        : Salir")
    print("="*40)
    
    string = 2   # A string
    finger = 0
    position = 1
    
    while True:
        # Mostrar estado actual
        info = mapper.get_note_info(string, position, finger)
        print(f"\n📍 Actual: Cuerda {info.string}, Pos {position}, Dedo {finger} → {info.note_name}")
        
        cmd = input("Comando: ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd.startswith('s') and len(cmd) == 2:
            string = int(cmd[1])
            string = max(1, min(4, string))
        elif cmd.startswith('f') and len(cmd) == 2:
            finger = int(cmd[1])
            finger = max(0, min(4, finger))
        elif cmd.startswith('p') and len(cmd) == 2:
            position = int(cmd[1])
            position = max(1, min(3, position))
        elif cmd == 'play':
            note = mapper.get_note(string, position, finger)
            print(f"  🎵 Tocando: {info.note_name}")
            controller.note_on(note)
            time.sleep(0.5)
            controller.note_off(note)
        elif cmd == 'scale':
            play_scale(controller, mapper, string)
        elif cmd == 'open':
            play_open_strings(controller, mapper)
        elif cmd == 'twinkle':
            play_twinkle(controller)


def main():
    print("\n" + "🎹"*20)
    print("   MIDI CONTROLLER DEMO")
    print("🎹"*20)
    
    config = Config()
    
    print(f"\n🔌 Configurando MIDI...")
    print(f"   Puerto: {config.midi.port_name}")
    print(f"   Instrumento: {config.midi.program} (Violin)")
    
    try:
        controller = MIDIController(config)
        mapper = NoteMapper(config)
        
        print("\n📋 MENÚ PRINCIPAL")
        print("  1. Tocar cuerdas abiertas")
        print("  2. Tocar escala en A")
        print("  3. Tocar Twinkle Twinkle")
        print("  4. Modo interactivo")
        print("  5. Salir")
        
        while True:
            choice = input("\nOpción: ").strip()
            
            if choice == '1':
                play_open_strings(controller, mapper)
            elif choice == '2':
                play_scale(controller, mapper, string=2)
            elif choice == '3':
                play_twinkle(controller)
            elif choice == '4':
                interactive_mode(controller, mapper)
            elif choice == '5':
                break
        
        controller.close()
        print("\n✅ Demo finalizado")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Para usar MIDI necesitas:")
        print("   1. Instalar: pip install python-rtmidi")
        print("   2. En Linux: sudo modprobe snd-virmidi")
        print("   3. Conectar un sintetizador/DAW al puerto MIDI")


if __name__ == "__main__":
    main()
