"""
Keyboard Event Listener
Trisha says: "Time to tickle those ivories! 🎹"
"""

import logging
from pynput import keyboard
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class KeyboardListener:
    """Listen for keyboard events"""
    
    def __init__(self, volume_controller):
        """Initialize the keyboard listener"""
        self.volume_controller = volume_controller
        self._listener: Optional[keyboard.Listener] = None
        
    def on_press(self, key):
        """Handle key press events"""
        try:
            if key == keyboard.Key.media_volume_up:
                logger.info("🔊 Volume Up key pressed")
                # Always suppress volume keys when we have a controller
                self.volume_controller.handle_volume_up()
                return False
                    
            elif key == keyboard.Key.media_volume_down:
                logger.info("🔉 Volume Down key pressed")
                # Always suppress volume keys when we have a controller
                self.volume_controller.handle_volume_down()
                return False
                    
            elif key == keyboard.Key.media_volume_mute:
                logger.info("🔇 Mute key pressed")
                # Always suppress volume keys when we have a controller
                self.volume_controller.handle_mute_toggle()
                return False
                    
            # Let other keys pass through
            return True
            
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
            # On error, let OS handle it
            return True
            
    def start(self):
        """Start listening for keyboard events"""
        if not self._listener:
            logger.info("🎹 Starting keyboard listener...")
            self._listener = keyboard.Listener(on_press=self.on_press)
            self._listener.start()
            
    def stop(self):
        """Stop listening for keyboard events"""
        if self._listener:
            logger.info("👋 Stopping keyboard listener...")
            self._listener.stop()
            self._listener = None
