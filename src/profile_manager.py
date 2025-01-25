"""
Profile Manager for uPNP Control
Trisha's Note: "Making profiles as fun as accounting spreadsheets! 🎵"
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import logging

@dataclass
class KeyBinding:
    key: str  # e.g., "media_volume_up", "ctrl+alt+1"
    action: str  # e.g., "volume_up", "set_input"
    params: Dict  # e.g., {"input": "HDMI1", "step": 2}
    description: str

@dataclass
class DeviceProfile:
    name: str
    device_pattern: str  # Pattern to match device name
    manufacturer_pattern: str  # Pattern to match manufacturer
    key_bindings: List[KeyBinding]
    volume_step: float
    max_volume: int
    
    @classmethod
    def from_dict(cls, data):
        data['key_bindings'] = [
            KeyBinding(**kb) for kb in data.get('key_bindings', [])
        ]
        return cls(**data)

class ProfileManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.profiles_file = os.path.expanduser('~/.upnp_control/profiles.json')
        self.profiles: Dict[str, DeviceProfile] = {}
        self.load_default_profiles()
        self.load_profiles()
        
    def load_default_profiles(self):
        """Load built-in default profiles"""
        denon_profile = DeviceProfile(
            name="Denon Default",
            device_pattern="thebigd|denon",
            manufacturer_pattern="denon",
            key_bindings=[
                KeyBinding(
                    key="media_volume_up",
                    action="volume_up",
                    params={"step": 2},
                    description="Volume Up"
                ),
                KeyBinding(
                    key="media_volume_down",
                    action="volume_down",
                    params={"step": 2},
                    description="Volume Down"
                ),
                KeyBinding(
                    key="ctrl+alt+1",
                    action="set_input",
                    params={"input": "HDMI1"},
                    description="Switch to HDMI 1"
                ),
                KeyBinding(
                    key="ctrl+alt+2",
                    action="set_input",
                    params={"input": "HDMI2"},
                    description="Switch to HDMI 2"
                )
            ],
            volume_step=2,
            max_volume=98
        )
        
        onkyo_profile = DeviceProfile(
            name="Onkyo Default",
            device_pattern="onkyo",
            manufacturer_pattern="onkyo",
            key_bindings=[
                KeyBinding(
                    key="media_volume_up",
                    action="volume_up",
                    params={"step": 2},
                    description="Volume Up"
                ),
                KeyBinding(
                    key="media_volume_down",
                    action="volume_down",
                    params={"step": 2},
                    description="Volume Down"
                ),
                KeyBinding(
                    key="ctrl+shift+s",
                    action="sound_mode",
                    params={"mode": "movie"},
                    description="Movie Sound Mode"
                )
            ],
            volume_step=2,
            max_volume=100
        )
        
        self.profiles = {
            "denon_default": denon_profile,
            "onkyo_default": onkyo_profile
        }
    
    def load_profiles(self):
        """Load user profiles from disk"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    for profile_name, profile_data in data.items():
                        self.profiles[profile_name] = DeviceProfile.from_dict(profile_data)
        except Exception as e:
            self.logger.error(f"Failed to load profiles: {e}")
    
    def save_profiles(self):
        """Save profiles to disk"""
        try:
            os.makedirs(os.path.dirname(self.profiles_file), exist_ok=True)
            with open(self.profiles_file, 'w') as f:
                json.dump({
                    name: asdict(profile)
                    for name, profile in self.profiles.items()
                }, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save profiles: {e}")
    
    def add_profile(self, profile: DeviceProfile):
        """Add or update a profile"""
        self.profiles[profile.name] = profile
        self.save_profiles()
    
    def remove_profile(self, profile_name: str):
        """Remove a profile"""
        if profile_name in self.profiles:
            del self.profiles[profile_name]
            self.save_profiles()
    
    def get_profile_for_device(self, device) -> Optional[DeviceProfile]:
        """Find the best matching profile for a device"""
        import re
        
        for profile in self.profiles.values():
            device_name = getattr(device, 'friendly_name', '').lower()
            manufacturer = getattr(device, 'manufacturer', '').lower()
            
            if (re.search(profile.device_pattern.lower(), device_name) or
                re.search(profile.manufacturer_pattern.lower(), manufacturer)):
                return profile
        
        return None

# Common uPNP actions that can be mapped to keys
AVAILABLE_ACTIONS = {
    "volume_up": "Increase Volume",
    "volume_down": "Decrease Volume",
    "set_input": "Set Input Source",
    "sound_mode": "Change Sound Mode",
    "mute_toggle": "Toggle Mute",
    "power_toggle": "Toggle Power",
    "play_pause": "Play/Pause",
    "next_track": "Next Track",
    "prev_track": "Previous Track"
}
