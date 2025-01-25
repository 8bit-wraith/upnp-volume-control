#!/usr/bin/env python3
"""
uPNP Volume Control
Trisha's Note: Let's make it chatty! 🗣️
"""

import logging
import upnpclient
import time
from typing import Optional, Dict
import threading
from pynput import keyboard
from device_profiles import get_device_profile, DeviceEvent
from keyboard_listener import KeyboardListener
from event_server import EventServer
import os
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set default to DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Make upnpclient more verbose
upnpclient_logger = logging.getLogger('upnpclient')
upnpclient_logger.setLevel(logging.DEBUG)
requests_logger = logging.getLogger('urllib3')
requests_logger.setLevel(logging.DEBUG)

class UPNPVolumeController:
    def __init__(self):
        """Initialize the controller"""
        self.logger = logging.getLogger(__name__)
        
        self.devices = {}
        self.current_device = None
        self.current_profile = None
        self._volume_callbacks = []
        self._device_callbacks = []
        self.keyboard_listener = None
        self.event_server = EventServer(port=8080)
        self.last_used_device = None
        
        # Load last used device from settings
        self.settings_file = os.path.expanduser('~/.config/upnp-volume-control/settings.json')
        self.load_settings()
        
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.last_used_device = settings.get('last_used_device')
                    self.logger.debug(f"📝 Loaded last used device: {self.last_used_device}")
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            
    def save_settings(self):
        """Save settings to file"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump({
                    'last_used_device': self.last_used_device
                }, f)
            self.logger.debug(f"💾 Saved last used device: {self.last_used_device}")
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            
    def on_volume_change(self, callback):
        """Register callback for volume changes"""
        self._volume_callbacks.append(callback)
        
    def on_device_change(self, callback):
        """Register callback for device changes"""
        self._device_callbacks.append(callback)
        
    def _notify_volume_change(self, volume: float) -> None:
        """Notify volume change"""
        try:
            if self._volume_callbacks:
                for callback in self._volume_callbacks:
                    try:
                        callback(volume)
                    except Exception as e:
                        self.logger.error(f"❌ Volume callback error: {e}")
        except Exception as e:
            self.logger.error(f"❌ Volume callback error: {e}")

    def _notify_device_change(self):
        """Notify device change callbacks"""
        for callback in self._device_callbacks:
            try:
                callback(self.current_device)
            except Exception as e:
                self.logger.error(f"Error in device callback: {e}")
    
    def _ensure_device_connected(self) -> bool:
        """Ensure device is connected, attempt reconnect if needed"""
        if not (self.current_device and self.current_profile):
            try:
                self.logger.info("🔄 Attempting to reconnect to device...")
                self.refresh_devices()
                if not (self.current_device and self.current_profile):
                    self.logger.error("❌ Couldn't reconnect to device")
                    return False
            except Exception as e:
                self.logger.error(f"❌ Device reconnection error: {e}")
                return False
        return True

    def start(self):
        """Start the controller"""
        self.logger.info("🎸 Starting uPNP Volume Control...")
        self.refresh_devices()
        self.logger.info("⌨️ Starting keyboard listener...")
        self.keyboard_listener = KeyboardListener(self)
        self.keyboard_listener.start()
        
    def refresh_devices(self):
        """Refresh the list of devices"""
        self.logger.info("🔄 Refreshing devices...")
        try:
            devices = upnpclient.discover(timeout=3)
            valid_devices = []
            
            for device in devices:
                try:
                    profile = get_device_profile(device)
                    if profile:
                        self.devices[device.friendly_name] = (device, profile)
                        valid_devices.append(device.friendly_name)
                        
                        # Start event server if needed
                        if not self.event_server:
                            self.event_server.start(self._handle_device_event)
                            
                        # Subscribe to events
                        profile.subscribe_to_events(device)
                except Exception as e:
                    self.logger.error(f"Error setting up device {device.friendly_name}: {e}")
                    
            self.logger.info(f"Found {len(valid_devices)} valid uPNP devices")
            
            # Set current device to first valid device
            if valid_devices and not self.current_device:
                self.current_device = valid_devices[0]
                self.current_profile = self.devices[self.current_device][1]
                
        except Exception as e:
            self.logger.error(f"Error discovering devices: {e}")
            
    def _handle_device_event(self, event_data):
        """Handle events from devices"""
        try:
            if 'Volume' in event_data:
                self.logger.debug(f"🔊 Volume event: {event_data['Volume']}")
                # Update UI or handle volume change
        except Exception as e:
            self.logger.error(f"Error handling device event: {e}")
            
    def select_device(self, device_name: str) -> bool:
        """Select a device by name"""
        if device_name in self.devices:
            device_info = self.devices[device_name]
            self.current_device = device_info[0]
            self.current_profile = device_info[1]
            
            # Subscribe to device events
            self.current_profile.on_event("volume_changed", 
                lambda event: self._notify_volume_change(event.value))
            self.current_profile.on_event("input_changed",
                lambda event: self.logger.info(f"Input changed to: {event.value}"))
            self.current_profile.on_event("power_changed",
                lambda event: self.logger.info(f"Power {'on' if event.value else 'off'}"))
                
            # Start event subscription
            self.current_profile.subscribe_to_events(self.current_device)
            
            self._notify_device_change()
            return True
        return False
        
    def get_current_volume(self) -> Optional[int]:
        """Get current volume"""
        if self.current_device and self.current_profile:
            return self.current_profile.get_volume(self.current_device)
        return None
        
    def volume_up(self) -> bool:
        """Increase volume"""
        try:
            if not (self.current_device and self.current_profile):
                self.logger.warning("🤔 No active device for volume control")
                return False
                
            current = self.get_current_volume()
            if current is None:
                self.logger.error("❌ Couldn't get current volume")
                return False
                
            # Use smaller percentage-based step
            step = 2  # 2% step for finer control
            new_volume = min(100, current + step)
            
            try:
                if self.current_profile.set_volume(self.current_device, new_volume):
                    self.logger.info(f"🔊 Volume increased to {new_volume}%")
                    self._notify_volume_change(new_volume)
                    return True
                else:
                    self.logger.error("❌ Failed to set volume")
                    return False
            except Exception as e:
                self.logger.error(f"❌ Volume control error: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.error(f"💥 Critical volume control error: {str(e)}")
            # Don't let the app die
            return False
        
    def volume_down(self) -> bool:
        """Decrease volume"""
        try:
            if not self._ensure_device_connected():
                return False
                
            current = self.get_current_volume()
            if current is None:
                self.logger.error("❌ Couldn't get current volume")
                return False
                
            # Use smaller percentage-based step
            step = 2  # 2% step for finer control
            new_volume = max(0, current - step)
            
            try:
                if self.current_profile.set_volume(self.current_device, new_volume):
                    self.logger.info(f"🔉 Volume decreased to {new_volume}%")
                    self._notify_volume_change(new_volume)
                    return True
                else:
                    self.logger.error("❌ Failed to set volume")
                    if not self._ensure_device_connected():  # Try reconnect
                        return False
                    return self.volume_down()  # Retry after reconnect
            except Exception as e:
                self.logger.error(f"❌ Volume control error: {e}")
                if not self._ensure_device_connected():  # Try reconnect
                    return False
                return self.volume_down()  # Retry after reconnect
                
        except Exception as e:
            self.logger.error(f"💥 Critical volume control error: {str(e)}")
            return False
        
    def set_volume(self, volume: int) -> bool:
        """Set absolute volume"""
        if self.current_device and self.current_profile:
            if self.current_profile.set_volume(self.current_device, volume):
                self.logger.info(f"🔊 Volume set to {volume}%")
                return True
        return False
        
    def play_pause(self) -> bool:
        """Toggle play/pause"""
        if self.current_device and self.current_profile:
            return self.current_profile.play_pause(self.current_device)
        return False
        
    def handle_volume_up(self) -> bool:
        """Handle volume up key press"""
        try:
            self.logger.info("⬆️ Volume Up key pressed")
            
            # Try last used device first
            if self.last_used_device and self.last_used_device in self.devices:
                device, profile = self.devices[self.last_used_device]
                # Try relative volume first
                try:
                    if profile.set_volume_relative(device, +2):
                        return True
                except:
                    pass
                    
                # Fall back to regular volume control
                current = profile.get_volume(device)
                if current is not None:
                    if profile.set_volume(device, min(100, current + 2)):
                        self.last_used_device = device.friendly_name
                        self.save_settings()
                        return True
                    
            # Refresh devices if needed
            if not self.devices:
                self.refresh_devices()
                
            # Try other devices
            for device_name, (device, profile) in self.devices.items():
                try:
                    # Try relative volume first
                    if profile.set_volume_relative(device, +2):
                        self.last_used_device = device_name
                        self.save_settings()
                        return True
                except:
                    # Fall back to regular volume control
                    try:
                        current = profile.get_volume(device)
                        if current is not None:
                            if profile.set_volume(device, min(100, current + 2)):
                                self.last_used_device = device_name
                                self.save_settings()
                                return True
                    except:
                        continue
                    
            self.logger.warning("😕 No working volume control found")
            return False
            
        except Exception as e:
            self.logger.error(f"💥 Error handling volume up: {e}")
            return False
            
    def handle_volume_down(self) -> bool:
        """Handle volume down key press"""
        try:
            self.logger.info("⬇️ Volume Down key pressed")
            
            # Try last used device first
            if self.last_used_device and self.last_used_device in self.devices:
                device, profile = self.devices[self.last_used_device]
                # Try relative volume first
                try:
                    if profile.set_volume_relative(device, -2):
                        return True
                except:
                    pass
                    
                # Fall back to regular volume control
                current = profile.get_volume(device)
                if current is not None:
                    if profile.set_volume(device, max(0, current - 2)):
                        self.last_used_device = device.friendly_name
                        self.save_settings()
                        return True
                    
            # Refresh devices if needed
            if not self.devices:
                self.refresh_devices()
                
            # Try other devices
            for device_name, (device, profile) in self.devices.items():
                try:
                    # Try relative volume first
                    if profile.set_volume_relative(device, -2):
                        self.last_used_device = device_name
                        self.save_settings()
                        return True
                except:
                    # Fall back to regular volume control
                    try:
                        current = profile.get_volume(device)
                        if current is not None:
                            if profile.set_volume(device, max(0, current - 2)):
                                self.last_used_device = device_name
                                self.save_settings()
                                return True
                    except:
                        continue
                    
            self.logger.warning("😕 No working volume control found")
            return False
            
        except Exception as e:
            self.logger.error(f"💥 Error handling volume down: {e}")
            return False
            
    def handle_mute_toggle(self) -> bool:
        """Handle mute toggle key press"""
        try:
            self.logger.info("Mute toggle key pressed")
            
            # Try last used device first
            if self.last_used_device and self.last_used_device in self.devices:
                device, profile = self.devices[self.last_used_device]
                if profile.toggle_mute(device):
                    return True
                    
            # Try other devices
            for device_id, (device, profile) in self.devices.items():
                if profile.toggle_mute(device):
                    self.last_used_device = device_id
                    self.save_settings()
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Error handling mute toggle: {e}")
            return False
            
    def on_key_event(self, key):
        """Handle keyboard volume key events"""
        try:
            if key == keyboard.Key.media_volume_up:
                self.logger.info("Volume Up key pressed")
                self.handle_volume_up()
            elif key == keyboard.Key.media_volume_down:
                self.logger.info("Volume Down key pressed")
                self.handle_volume_down()
            elif key == keyboard.Key.media_play_pause:
                self.logger.info("Play/Pause key pressed")
                self.play_pause()
        except Exception as e:
            self.logger.error(f"Key event error: {e}")
            
    def start_keyboard_listener(self):
        """Start keyboard event listener"""
        if not self.keyboard_listener:
            self.logger.info("🎧 Starting keyboard listener...")
            self.keyboard_listener = KeyboardListener(on_key_event=self.on_key_event)
            self.keyboard_listener.start()
            
    def stop_keyboard_listener(self):
        """Stop keyboard event listener"""
        if self.keyboard_listener:
            self.logger.info("👋 Stopping keyboard listener...")
            self.keyboard_listener.stop()
            self.keyboard_listener = None

def main():
    """
    Main application entry point
    
    Let the multi-device party begin! 🎉
    """
    logging.basicConfig(level=logging.INFO)
    controller = UPNPVolumeController()
    controller.start()
    
    # Example usage: register a callback for volume changes
    def on_volume_change(volume):
        print(f"Volume changed to: {volume}")
    controller.on_volume_change(on_volume_change)
    
    # Example usage: increase volume
    controller.volume_up()
    
    # Example usage: decrease volume
    controller.volume_down()
    
    # Example usage: set absolute volume
    controller.set_volume(50)
    
    # Example usage: toggle play/pause
    controller.play_pause()
    
    # Keep the program running
    while True:
        time.sleep(1)
        
if __name__ == "__main__":
    main()
