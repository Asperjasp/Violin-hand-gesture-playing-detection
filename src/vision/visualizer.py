"""
Violin Visualizer - Renderiza un violín virtual que muestra el estado actual.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class VisualizerState:
    """Estado actual del visualizador."""
    string_selected: Optional[int] = None  # 1-4 (E, A, D, G)
    position: int = 1  # 1-3
    finger_count: int = 0  # 0-4
    bow_active: bool = False
    current_note: Optional[str] = None
    midi_note: Optional[int] = None


class ViolinVisualizer:
    """
    Renderiza un violín virtual sobre el frame de video.
    
    Muestra visualmente:
    - Las 4 cuerdas del violín
    - Cuál cuerda está seleccionada
    - Los dedos presionados
    - La posición actual
    - La nota que suena
    """
    
    # Colores (BGR)
    COLORS = {
        'background': (40, 40, 40),
        'violin_body': (60, 80, 120),      # Marrón rojizo
        'fingerboard': (30, 30, 30),        # Negro
        'string_normal': (180, 180, 180),   # Gris
        'string_active': (0, 255, 255),     # Amarillo
        'string_playing': (0, 255, 0),      # Verde
        'finger_inactive': (100, 100, 100), # Gris
        'finger_active': (0, 200, 255),     # Naranja
        'bow_inactive': (80, 80, 80),       # Gris oscuro
        'bow_active': (0, 255, 0),          # Verde
        'text': (255, 255, 255),            # Blanco
        'note_display': (0, 200, 255),      # Naranja
        'position_1': (100, 255, 100),      # Verde claro
        'position_2': (100, 200, 255),      # Naranja claro
        'position_3': (255, 100, 100),      # Azul claro
    }
    
    # Nombres de cuerdas
    STRING_NAMES = {1: 'E', 2: 'A', 3: 'D', 4: 'G'}
    
    # Nombres de notas MIDI
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    def __init__(
        self,
        width: int = 300,
        height: int = 400,
        position: Tuple[int, int] = (20, 20)
    ):
        """
        Inicializa el visualizador.
        
        Args:
            width: Ancho del panel del violín
            height: Alto del panel del violín
            position: Posición (x, y) donde dibujar el panel
        """
        self.width = width
        self.height = height
        self.position = position
        self.state = VisualizerState()
        
        # Dimensiones internas
        self.fingerboard_x = 50
        self.fingerboard_width = 200
        self.fingerboard_y = 80
        self.fingerboard_height = 250
        
        # Posiciones de las cuerdas (x relativo al panel)
        self.string_positions = {
            4: 80,   # G
            3: 120,  # D
            2: 160,  # A
            1: 200,  # E
        }
        
        # Posiciones de los trastes/posiciones
        self.position_lines = {
            1: 120,  # 1st position
            2: 180,  # 2nd position
            3: 240,  # 3rd position
        }
    
    def update_state(
        self,
        gestures: Dict,
        note_info: Optional[object] = None
    ) -> None:
        """
        Actualiza el estado del visualizador.
        
        Args:
            gestures: Diccionario con información de gestos
            note_info: Información de la nota (opcional)
        """
        self.state.bow_active = gestures.get('bow_active', False)
        self.state.string_selected = gestures.get('string', None)
        self.state.position = gestures.get('position', 1)
        self.state.finger_count = gestures.get('finger_count', 0)
        
        if note_info:
            self.state.current_note = getattr(note_info, 'note_name', None)
            self.state.midi_note = getattr(note_info, 'midi_note', None)
    
    def render(self, frame: np.ndarray) -> np.ndarray:
        """
        Renderiza el visualizador sobre el frame.
        
        Args:
            frame: Frame de video (BGR)
            
        Returns:
            Frame con el visualizador dibujado
        """
        # Crear panel del visualizador
        panel = self._create_panel()
        
        # Dibujar componentes
        self._draw_fingerboard(panel)
        self._draw_strings(panel)
        self._draw_position_indicator(panel)
        self._draw_fingers(panel)
        self._draw_bow_indicator(panel)
        self._draw_note_display(panel)
        self._draw_info_text(panel)
        
        # Overlay del panel sobre el frame
        x, y = self.position
        frame = self._overlay_panel(frame, panel, x, y)
        
        return frame
    
    def _create_panel(self) -> np.ndarray:
        """Crea el panel base del visualizador."""
        panel = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        panel[:] = self.COLORS['background']
        
        # Borde del panel
        cv2.rectangle(panel, (0, 0), (self.width-1, self.height-1), (80, 80, 80), 2)
        
        # Título
        cv2.putText(
            panel, "VIOLIN",
            (self.width // 2 - 40, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7,
            self.COLORS['text'], 2
        )
        
        return panel
    
    def _draw_fingerboard(self, panel: np.ndarray) -> None:
        """Dibuja el diapasón del violín."""
        # Cuerpo del diapasón
        cv2.rectangle(
            panel,
            (self.fingerboard_x, self.fingerboard_y),
            (self.fingerboard_x + self.fingerboard_width, 
             self.fingerboard_y + self.fingerboard_height),
            self.COLORS['fingerboard'],
            -1
        )
        
        # Borde
        cv2.rectangle(
            panel,
            (self.fingerboard_x, self.fingerboard_y),
            (self.fingerboard_x + self.fingerboard_width, 
             self.fingerboard_y + self.fingerboard_height),
            self.COLORS['violin_body'],
            2
        )
        
        # Líneas de posición (trastes)
        for pos, y in self.position_lines.items():
            color = self.COLORS[f'position_{pos}'] if pos == self.state.position else (60, 60, 60)
            cv2.line(
                panel,
                (self.fingerboard_x + 5, y),
                (self.fingerboard_x + self.fingerboard_width - 5, y),
                color,
                1 if pos != self.state.position else 2
            )
            
            # Número de posición
            cv2.putText(
                panel, f"{pos}",
                (self.fingerboard_x - 20, y + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                color, 1
            )
    
    def _draw_strings(self, panel: np.ndarray) -> None:
        """Dibuja las 4 cuerdas."""
        for string_num, x in self.string_positions.items():
            # Determinar color
            if self.state.bow_active and self.state.string_selected == string_num:
                color = self.COLORS['string_playing']
                thickness = 3
            elif self.state.string_selected == string_num:
                color = self.COLORS['string_active']
                thickness = 2
            else:
                color = self.COLORS['string_normal']
                thickness = 1
            
            # Dibujar cuerda
            cv2.line(
                panel,
                (x, self.fingerboard_y - 10),
                (x, self.fingerboard_y + self.fingerboard_height + 10),
                color,
                thickness
            )
            
            # Nombre de la cuerda
            name = self.STRING_NAMES[string_num]
            text_color = color if self.state.string_selected == string_num else (120, 120, 120)
            cv2.putText(
                panel, name,
                (x - 5, self.fingerboard_y - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                text_color, 1
            )
    
    def _draw_position_indicator(self, panel: np.ndarray) -> None:
        """Dibuja indicador de posición actual."""
        pos = self.state.position
        y = self.position_lines.get(pos, 120)
        
        # Zona de posición (rectángulo semitransparente)
        overlay = panel.copy()
        y_start = y - 30 if pos > 1 else self.fingerboard_y
        y_end = y + 30 if pos < 3 else self.fingerboard_y + self.fingerboard_height
        
        cv2.rectangle(
            overlay,
            (self.fingerboard_x, y_start),
            (self.fingerboard_x + self.fingerboard_width, y_end),
            self.COLORS[f'position_{pos}'],
            -1
        )
        
        # Mezclar con transparencia
        alpha = 0.2
        cv2.addWeighted(overlay, alpha, panel, 1 - alpha, 0, panel)
    
    def _draw_fingers(self, panel: np.ndarray) -> None:
        """Dibuja los dedos presionados."""
        if self.state.string_selected is None:
            return
        
        string_x = self.string_positions.get(self.state.string_selected, 160)
        pos = self.state.position
        base_y = self.position_lines.get(pos, 120) - 20
        
        # Dibujar círculos para cada dedo
        finger_spacing = 25
        
        for finger in range(1, 5):
            y = base_y + (finger * finger_spacing)
            
            if finger <= self.state.finger_count:
                # Dedo presionado
                color = self.COLORS['finger_active']
                cv2.circle(panel, (string_x, y), 10, color, -1)
                cv2.circle(panel, (string_x, y), 10, (255, 255, 255), 1)
            else:
                # Dedo no presionado (solo contorno)
                color = self.COLORS['finger_inactive']
                cv2.circle(panel, (string_x, y), 8, color, 1)
            
            # Número del dedo
            cv2.putText(
                panel, str(finger),
                (string_x - 4, y + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.3,
                (255, 255, 255) if finger <= self.state.finger_count else color,
                1
            )
    
    def _draw_bow_indicator(self, panel: np.ndarray) -> None:
        """Dibuja indicador del arco."""
        bow_y = self.height - 50
        
        # Arco (línea horizontal)
        if self.state.bow_active:
            color = self.COLORS['bow_active']
            cv2.rectangle(panel, (60, bow_y), (self.width - 60, bow_y + 10), color, -1)
            text = "PLAYING"
        else:
            color = self.COLORS['bow_inactive']
            cv2.rectangle(panel, (60, bow_y), (self.width - 60, bow_y + 10), color, 2)
            text = "READY"
        
        # Texto del estado del arco
        cv2.putText(
            panel, text,
            (self.width // 2 - 35, bow_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            color, 1
        )
    
    def _draw_note_display(self, panel: np.ndarray) -> None:
        """Dibuja la nota actual."""
        note_y = 50
        
        if self.state.bow_active and self.state.current_note:
            # Nota grande
            cv2.putText(
                panel, self.state.current_note,
                (self.width // 2 - 25, note_y),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                self.COLORS['note_display'], 2
            )
        else:
            cv2.putText(
                panel, "---",
                (self.width // 2 - 20, note_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (80, 80, 80), 1
            )
    
    def _draw_info_text(self, panel: np.ndarray) -> None:
        """Dibuja información adicional."""
        info_y = self.fingerboard_y + self.fingerboard_height + 25
        
        # String info
        string_name = self.STRING_NAMES.get(self.state.string_selected, "-")
        cv2.putText(
            panel, f"String: {string_name}",
            (20, info_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4,
            self.COLORS['text'], 1
        )
        
        # Position info
        cv2.putText(
            panel, f"Pos: {self.state.position}",
            (120, info_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4,
            self.COLORS['text'], 1
        )
        
        # Finger info
        cv2.putText(
            panel, f"Fingers: {self.state.finger_count}",
            (200, info_y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.4,
            self.COLORS['text'], 1
        )
    
    def _overlay_panel(
        self,
        frame: np.ndarray,
        panel: np.ndarray,
        x: int,
        y: int
    ) -> np.ndarray:
        """Superpone el panel sobre el frame."""
        h, w = panel.shape[:2]
        frame_h, frame_w = frame.shape[:2]
        
        # Asegurar que el panel cabe en el frame
        if x + w > frame_w:
            w = frame_w - x
        if y + h > frame_h:
            h = frame_h - y
        
        if w > 0 and h > 0:
            # Mezclar con cierta transparencia
            alpha = 0.85
            roi = frame[y:y+h, x:x+w]
            blended = cv2.addWeighted(panel[:h, :w], alpha, roi, 1-alpha, 0)
            frame[y:y+h, x:x+w] = blended
        
        return frame


class HandVisualizerOverlay:
    """
    Overlay adicional para mostrar la detección de manos
    con información de lo que está haciendo cada mano.
    """
    
    def __init__(self):
        self.colors = {
            'left_hand': (255, 100, 100),   # Azul
            'right_hand': (100, 255, 100),  # Verde
            'pinch': (0, 255, 255),          # Amarillo
            'text_bg': (0, 0, 0),
        }
    
    def render(
        self,
        frame: np.ndarray,
        hands: list,
        gestures: dict
    ) -> np.ndarray:
        """
        Renderiza información sobre las manos detectadas.
        
        Args:
            frame: Frame de video
            hands: Lista de HandLandmarks detectados
            gestures: Diccionario con gestos reconocidos
        """
        for hand in hands:
            if hand.handedness == "Right":
                self._draw_right_hand_info(frame, hand, gestures)
            else:
                self._draw_left_hand_info(frame, hand, gestures)
        
        return frame
    
    def _draw_right_hand_info(
        self,
        frame: np.ndarray,
        hand,
        gestures: dict
    ) -> None:
        """Dibuja información de la mano derecha (control del arco)."""
        h, w = frame.shape[:2]
        
        # Posición del wrist
        wrist_x = int(hand.wrist[0] * w)
        wrist_y = int(hand.wrist[1] * h)
        
        # Información a mostrar
        bow_status = "BOW: ON" if gestures.get('bow_active') else "BOW: OFF"
        string_num = gestures.get('string', 0)
        string_name = {1: 'E', 2: 'A', 3: 'D', 4: 'G'}.get(string_num, '-')
        
        info_text = f"RIGHT HAND | {bow_status} | String: {string_name}"
        
        # Dibujar fondo del texto
        text_size = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.rectangle(
            frame,
            (wrist_x - 10, wrist_y - 60),
            (wrist_x + text_size[0] + 10, wrist_y - 35),
            self.colors['text_bg'],
            -1
        )
        
        # Texto
        cv2.putText(
            frame, info_text,
            (wrist_x, wrist_y - 45),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            self.colors['right_hand'], 1
        )
        
        # Indicador de pinch
        if gestures.get('bow_active'):
            thumb = hand.thumb_tip
            index = hand.index_tip
            thumb_px = (int(thumb[0] * w), int(thumb[1] * h))
            index_px = (int(index[0] * w), int(index[1] * h))
            
            cv2.circle(frame, thumb_px, 8, self.colors['pinch'], -1)
            cv2.circle(frame, index_px, 8, self.colors['pinch'], -1)
            cv2.line(frame, thumb_px, index_px, self.colors['pinch'], 2)
    
    def _draw_left_hand_info(
        self,
        frame: np.ndarray,
        hand,
        gestures: dict
    ) -> None:
        """Dibuja información de la mano izquierda (control del tono)."""
        h, w = frame.shape[:2]
        
        # Posición del wrist
        wrist_x = int(hand.wrist[0] * w)
        wrist_y = int(hand.wrist[1] * h)
        
        # Información
        position = gestures.get('position', 1)
        fingers = gestures.get('finger_count', 0)
        
        info_text = f"LEFT HAND | Pos: {position} | Fingers: {fingers}"
        
        # Fondo
        text_size = cv2.getTextSize(info_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
        cv2.rectangle(
            frame,
            (wrist_x - 10, wrist_y - 60),
            (wrist_x + text_size[0] + 10, wrist_y - 35),
            self.colors['text_bg'],
            -1
        )
        
        # Texto
        cv2.putText(
            frame, info_text,
            (wrist_x, wrist_y - 45),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5,
            self.colors['left_hand'], 1
        )
