"""
Device Profiles for uPNP Volume Control
Trisha's Note: "Making dB behave, but keeping all our friends! 🎚️"
"""

import logging
import time
from dataclasses import dataclass
from typing import Optional, Callable, Dict, List, Any
import threading
from xml.etree import ElementTree
import requests
import math

logger = logging.getLogger(__name__)

@dataclass
class DeviceEvent:
    """Event data for device state changes"""
    type: str
    value: any

class DeviceProfile:
    """Base class for device profiles"""
    def __init__(self, friendly_name=None, manufacturer="Unknown", model=None):
        self.friendly_name = friendly_name
        self.manufacturer = manufacturer
        self.model = model
        self.volume_step = 2
        self.max_volume = 100
        self.min_volume = 0
        self._callbacks: Dict[str, List[Callable]] = {}
        self._last_volume = None
        self._last_volume_time = 0
        self._volume_lock = threading.Lock()
        
    def on_event(self, event_type: str, callback: Callable):
        """Register callback for event type"""
        if event_type not in self._callbacks:
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)
        
    def _notify(self, event_type: str, value: any):
        """Notify callbacks of event"""
        if event_type in self._callbacks:
            event = DeviceEvent(event_type, value)
            for callback in self._callbacks[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
                    
    def get_rendering_control(self, device=None) -> Optional[object]:
        """Get RenderingControl service from device or its children"""
        try:
            logger.debug("🔍 Looking for RenderingControl service")
            if device is None:
                logger.error("❌ Device is None!")
                return None
                
            logger.debug(f"📱 Device: {device}")
            
            # Check device's services
            if hasattr(device, 'services'):
                logger.debug(f"🔌 Services: {device.services}")
                for service in device.services:
                    logger.debug(f"  Service: {service}")
                    logger.debug(f"  Attributes: {dir(service)}")
                    if hasattr(service, 'service_type'):
                        logger.debug(f"  Service type: {service.service_type}")
                        if 'RenderingControl' in service.service_type:
                            logger.debug("✅ Found RenderingControl service")
                            return service
            else:
                logger.debug("❌ Device has no services attribute")
                
            # Check embedded devices
            if hasattr(device, 'devices'):
                logger.debug(f"👶 Child devices: {device.devices}")
                for child in device.devices:
                    logger.debug(f"  Child: {child}")
                    if hasattr(child, 'services'):
                        logger.debug(f"  Child services: {child.services}")
                        for service in child.services:
                            logger.debug(f"    Service: {service}")
                            logger.debug(f"    Attributes: {dir(service)}")
                            if hasattr(service, 'service_type'):
                                logger.debug(f"    Service type: {service.service_type}")
                                if 'RenderingControl' in service.service_type:
                                    logger.debug("✅ Found RenderingControl in child device")
                                    return service
            else:
                logger.debug("❌ Device has no child devices")
                
            logger.error("❌ No RenderingControl service found")
            return None
            
        except Exception as e:
            logger.error(f"Error getting RenderingControl service: {e}")
            return None

    def get_volume(self, device) -> Optional[int]:
        """Get current volume as percentage (0-100)"""
        try:
            logger.debug(f"🎚️ Getting volume for device: {device}")
            service = self.get_rendering_control(device)
            if not service:
                logger.error("❌ No RenderingControl service found")
                return None
                
            logger.debug(f"🔌 Using service: {service}")
            response = service.GetVolume(InstanceID=0, Channel='Master')
            logger.debug(f"📡 GetVolume response: {response}")
            
            if not response or 'CurrentVolume' not in response:
                logger.error("❌ Invalid GetVolume response")
                return None
                
            current_volume = response['CurrentVolume']
            logger.debug(f"🔊 Raw volume value: {current_volume}")
            
            if current_volume is None:
                logger.warning("🤔 Device returned None volume, defaulting to 0")
                return 0
                
            # Convert to float if string
            if isinstance(current_volume, str):
                current_volume = float(current_volume)
                
            # Convert dB to percentage
            volume_percent = self._db_to_percent(current_volume)
            logger.debug(f"🔊 Current volume: {volume_percent}%")
            return volume_percent
            
        except Exception as e:
            logger.error(f"Error getting volume: {e}", exc_info=True)
            return None
            
    def set_volume(self, device, volume: int) -> bool:
        """Set volume on device"""
        try:
            rendering_control = self.get_rendering_control(device)
            if rendering_control:
                # Set volume using RenderingControl service
                rendering_control.SetVolume(
                    InstanceID=0,
                    Channel='Master',
                    DesiredVolume=volume
                )
                return True
                
            logger.error("No RenderingControl service found")
            return False
            
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
            
    def set_volume_relative(self, device, change: int) -> bool:
        """Change volume by relative amount (-100 to +100)"""
        try:
            # Get current volume
            current = self.get_volume(device)
            if current is None:
                logger.error("❌ Could not get current volume")
                return False
                
            # Calculate new volume
            new_volume = max(0, min(100, current + change))
            logger.debug(f"🔊 Adjusting volume: {current}% -> {new_volume}%")
            
            # Set new volume
            return self.set_volume(device, new_volume)
            
        except Exception as e:
            logger.error(f"Error setting relative volume: {e}")
            return False
            
    def subscribe_to_events(self, device):
        """Subscribe to device events"""
        try:
            # Debug device info
            logger.debug("="*50)
            logger.debug(f"🎮 Device info for {device.friendly_name}")
            logger.debug("="*50)
            logger.debug(f"  Location: {device.location}")
            logger.debug(f"  Type: {device.device_type}")
            logger.debug("\n  Services:")
            
            # Find RenderingControl service
            rendering_control = self.get_rendering_control(device)
            if not rendering_control:
                logger.warning("RenderingControl service not found")
                return
                
            # Log service info
            logger.debug("-"*40)
            logger.debug(f"    📡 Service: {rendering_control.name}")
            logger.debug(f"       Type: {rendering_control.service_type}")
            
            # Some devices use different attribute names
            event_url = None
            if hasattr(rendering_control, 'eventSubURL'):
                event_url = rendering_control.eventSubURL
                logger.debug(f"       Event URL: {event_url}")
            elif hasattr(rendering_control, 'event_sub_url'):
                event_url = rendering_control.event_sub_url
                logger.debug(f"       Event URL: {event_url}")
            else:
                logger.debug("       No event URL found")
                return
                
            # Manual event subscription
            base_url = device.location.rsplit('/', 1)[0]  # Remove last part of URL
            event_url = f"{base_url}{event_url}"
            logger.debug(f"Subscribing to events at: {event_url}")
            
            # Generate callback URL (using local IP)
            callback_url = "http://192.168.192.187:8080/events"
            
            # Subscription headers
            headers = {
                'NT': 'upnp:event',
                'CALLBACK': f'<{callback_url}>',
                'TIMEOUT': f'Second-{self._subscription_timeout}'
            }
            
            # Send SUBSCRIBE request
            try:
                response = requests.request('SUBSCRIBE', event_url, headers=headers)
                if response.status_code == 200:
                    logger.info(f"✅ Successfully subscribed to events for {device.friendly_name}")
                    # Store subscription info for renewal
                    self._subscription_sid = response.headers.get('SID')
                    logger.debug(f"Subscription ID: {self._subscription_sid}")
                else:
                    logger.error(f"Failed to subscribe: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
            
        except Exception as e:
            logger.error(f"Error in event subscription: {e}")
            
    def play_pause(self, device) -> bool:
        """Toggle play/pause"""
        try:
            if hasattr(device, 'AVTransport'):
                device.AVTransport.Pause(InstanceID=0)
                return True
            return False
        except Exception as e:
            logger.error(f"Error toggling play/pause: {e}")
            return False
            
    @staticmethod
    def safe_get_attr(device, attr, default=""):
        """Safely get device attribute"""
        try:
            return getattr(device, attr, default)
        except Exception:
            return default

class DenonProfile(DeviceProfile):
    """Profile for Denon devices"""
    
    def __init__(self, friendly_name=None, model=None):
        super().__init__(friendly_name, "Denon", model)
        self.max_volume = 98  # Denon max is usually 98
        self.volume_step = 2
        self._volume_debounce_ms = 250
        self._callbacks: Dict[str, Callable] = {}
        self._subscription_timeout = 300  # 5 minutes
        self._subscription_sid = None
        
    @classmethod
    def matches(cls, device) -> bool:
        """Check if device is a Denon device"""
        try:
            logger.debug(f"🔍 Checking device match for: {device}")
            
            # Check device type
            if hasattr(device, 'device_type'):
                logger.debug(f"📱 Device type: {device.device_type}")
                if 'denon' in device.device_type.lower():
                    logger.debug("✅ Matched Denon device type")
                    return True
                    
            # Check services for RenderingControl
            if hasattr(device, 'services'):
                for service in device.services:
                    if hasattr(service, 'service_type'):
                        logger.debug(f"🔌 Service type: {service.service_type}")
                        if 'RenderingControl' in service.service_type:
                            logger.debug("✅ Found RenderingControl service")
                            return True
                            
            # Check manufacturer
            if hasattr(device, 'manufacturer'):
                logger.debug(f"🏭 Manufacturer: {device.manufacturer}")
                if 'denon' in device.manufacturer.lower():
                    logger.debug("✅ Matched Denon manufacturer")
                    return True
                    
            # Check friendly name
            if hasattr(device, 'friendly_name'):
                logger.debug(f"📝 Friendly name: {device.friendly_name}")
                if 'denon' in device.friendly_name.lower():
                    logger.debug("✅ Matched Denon friendly name")
                    return True
                    
            logger.debug("❌ No Denon match found")
            return False
            
        except Exception as e:
            logger.error(f"Error matching device: {e}")
            return False
            
    def _raw_to_percent(self, raw_value: float) -> float:
        """Convert raw value (0-98) to percentage (0-100)"""
        try:
            # Denon uses 0-98 scale
            MIN_VOL = 0
            MAX_VOL = 98
            
            # Clamp input
            raw_value = max(MIN_VOL, min(MAX_VOL, raw_value))
            
            # Convert using logarithmic scale for more natural volume perception
            normalized = raw_value / MAX_VOL
            # Use modified log curve to give better control in typical listening range
            percent = 100 * (math.log(1 + normalized * 9) / math.log(10))
            
            logger.debug(f"🎚️ Raw to percent conversion: {raw_value:.1f} -> {percent:.1f}%")
            return percent
            
        except Exception as e:
            logger.error(f"Error converting raw to percent: {e}")
            return 0
            
    def _percent_to_raw(self, percent: float) -> float:
        """Convert percentage (0-100) to raw value (0-98)"""
        try:
            # Denon uses 0-98 scale
            MIN_VOL = 0
            MAX_VOL = 98
            
            # Clamp input to 0-100 range
            percent = max(0, min(100, percent))
            
            # Convert using inverse of our modified log curve
            normalized = (math.pow(10, percent/100) - 1) / 9
            raw_value = normalized * MAX_VOL
            
            # Round to nearest 0.5 as Denon expects
            raw_value = round(raw_value * 2) / 2
            raw_value = max(MIN_VOL, min(MAX_VOL, raw_value))
            
            logger.debug(f"🔢 Percent to raw conversion: {percent:.1f}% -> {raw_value:.1f}")
            return raw_value
            
        except Exception as e:
            logger.error(f"Error converting percent to raw: {e}")
            return MIN_VOL
            
    def get_volume(self, device) -> Optional[int]:
        """Get current volume as percentage (0-100)"""
        try:
            logger.debug(f"🎚️ Getting volume for device: {device}")
            service = self.get_rendering_control(device)
            if not service:
                logger.error("❌ No RenderingControl service found")
                return None
                
            logger.debug(f"🔌 Using service: {service}")
            response = service.GetVolume(InstanceID=0, Channel='Master')
            logger.debug(f"📡 GetVolume response: {response}")
            
            if not response or 'CurrentVolume' not in response:
                logger.error("❌ Invalid GetVolume response")
                return None
                
            current_volume = response['CurrentVolume']
            logger.debug(f"🔊 Raw volume value: {current_volume}")
            
            if current_volume is None:
                logger.warning("🤔 Device returned None volume, defaulting to 0")
                return 0
                
            # Convert to float if string
            if isinstance(current_volume, str):
                current_volume = float(current_volume)
                
            # Convert raw value to percentage
            volume_percent = self._raw_to_percent(current_volume)
            logger.debug(f"🔊 Current volume: {volume_percent}%")
            return volume_percent
            
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return None
            
    def set_volume(self, device, volume: float) -> bool:
        """Set volume using percentage (0-100)"""
        retries = 3
        while retries > 0:
            try:
                service = self.get_rendering_control(device)
                if not service:
                    logger.error("❌ No RenderingControl service found")
                    return False
                    
                # Get current volume before change
                response = service.GetVolume(InstanceID=0, Channel='Master')
                current_raw = float(response['CurrentVolume']) if response and 'CurrentVolume' in response else None
                logger.debug(f"🎚️ Current raw volume before change: {current_raw}")
                    
                # Convert percentage to raw value
                raw_volume = self._percent_to_raw(volume)
                
                # Only send if actually changing
                if current_raw is not None and abs(current_raw - raw_volume) < 0.1:
                    logger.debug(f"⏭️ Skipping volume set - already at {raw_volume}")
                    return True
                    
                logger.debug(f"🔊 Setting volume: {volume}% -> raw {raw_volume}")
                service.SetVolume(InstanceID=0, Channel='Master', DesiredVolume=raw_volume)
                
                # Verify the change
                time.sleep(0.1)  # Give device time to process
                response = service.GetVolume(InstanceID=0, Channel='Master')
                new_raw = float(response['CurrentVolume']) if response and 'CurrentVolume' in response else None
                logger.debug(f"✅ Volume after change: {new_raw} (target was {raw_volume})")
                
                return True
                
            except Exception as e:
                retries -= 1
                if retries > 0:
                    logger.warning(f"⚠️ Volume control retry ({retries} left): {e}")
                    time.sleep(0.5)  # Wait before retry
                else:
                    logger.error(f"❌ Error setting volume: {e}")
                    return False
            
    def _handle_event(self, event):
        """Handle device events"""
        try:
            logger.debug(f"📥 Received event: {event}")
            
            if hasattr(event, 'LastChange'):
                # Parse volume changes
                if 'Volume' in event.LastChange:
                    try:
                        volume_raw = float(event.LastChange['Volume'])
                        volume_percent = self._raw_to_percent(volume_raw)
                        logger.debug(f"🔊 Event volume: {volume_raw} -> {volume_percent}%")
                        self._notify("volume_changed", volume_percent)
                    except (ValueError, TypeError) as e:
                        logger.error(f"Error parsing volume from event: {e}")
                    
                # Parse other changes (power, input, etc)
                if 'PowerState' in event.LastChange:
                    self._notify("power_changed", event.LastChange['PowerState'] == 'ON')
                    
                if 'Input' in event.LastChange:
                    self._notify("input_changed", event.LastChange['Input'])
                    
        except Exception as e:
            logger.error(f"Error handling event: {e}")

class SonosProfile(DeviceProfile):
    """Profile for Sonos devices"""
    def __init__(self, friendly_name=None, model=None):
        super().__init__(friendly_name, "Sonos", model)
        self.max_volume = 100
        self.volume_step = 2
        
    @classmethod
    def matches(cls, device):
        """Check if device is a Sonos device"""
        try:
            manufacturer = cls.safe_get_attr(device, 'manufacturer', "").lower()
            friendly_name = cls.safe_get_attr(device, 'friendly_name', "").lower()
            return "sonos" in manufacturer or "sonos" in friendly_name
        except Exception:
            return False
            
    def set_volume(self, device, volume: int) -> bool:
        """Set volume level"""
        try:
            # Sonos uses GroupRenderingControl for synchronized volume
            if hasattr(device, 'GroupRenderingControl'):
                device.GroupRenderingControl.SetGroupVolume(
                    InstanceID=0,
                    DesiredVolume=volume
                )
                self._notify("volume_changed", volume)
                return True
            return super().set_volume(device, volume)
        except Exception as e:
            logger.error(f"Error setting Sonos group volume: {e}")
            return super().set_volume(device, volume)

class YamahaProfile(DeviceProfile):
    """Profile for Yamaha devices"""
    def __init__(self, friendly_name=None, model=None):
        super().__init__(friendly_name, "Yamaha", model)
        self.max_volume = 100
        self.volume_step = 0.5  # Yamaha often uses 0.5 dB steps
        
    @classmethod
    def matches(cls, device):
        """Check if device is a Yamaha device"""
        try:
            manufacturer = cls.safe_get_attr(device, 'manufacturer', "").lower()
            friendly_name = cls.safe_get_attr(device, 'friendly_name', "").lower()
            return "yamaha" in manufacturer or "yamaha" in friendly_name
        except Exception:
            return False

# List of available device profiles
DEVICE_PROFILES = [
    DenonProfile,
    SonosProfile,
    YamahaProfile
]

def get_device_profile(device) -> Optional[DeviceProfile]:
    """Get appropriate profile for device"""
    try:
        # Try to match device to a profile
        for profile_class in DEVICE_PROFILES:
            if profile_class.matches(device):
                return profile_class(
                    friendly_name=DeviceProfile.safe_get_attr(device, 'friendly_name'),
                    model=DeviceProfile.safe_get_attr(device, 'modelName')
                )
                
        # If no match, return None instead of a generic profile
        logger.warning(f"No matching profile for device: {device.friendly_name}")
        return None
        
    except Exception as e:
        logger.error(f"Error creating device profile: {e}")
        return None
