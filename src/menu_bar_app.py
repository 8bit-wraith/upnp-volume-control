"""
Menu Bar App for uPNP Volume Control
Trisha's Note: "Fix first, party later! 🔧"
"""

import rumps
import threading
import logging
from upnp_volume_control import UPNPVolumeController
from settings_window import SettingsWindow
from PyQt6.QtWidgets import QApplication
import sys
import os
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UPNPMenuBarApp(rumps.App):
    def __init__(self):
        logger.info("🎸 Starting uPNP Volume Control...")
        
        # Initialize controller first
        self.controller = UPNPVolumeController()
        self.current_volume = None
        self.plaid_mode = False
        self.plaid_thread = None
        
        # Initialize menu items
        self.device_menu = rumps.MenuItem("🔌 Devices")
        self.volume_display = rumps.MenuItem("Volume: --")
        self.speed_display = rumps.MenuItem("Status: --")
        
        # Create initial menu structure
        menu_items = [
            self.volume_display,
            self.speed_display,
            self.device_menu,
            None,  # Separator
            rumps.MenuItem("⚙️ Settings", callback=self.show_settings),
            rumps.MenuItem("🔄 Refresh", callback=self.refresh_devices),
            None,  # Separator
            rumps.MenuItem("👋 Quit", callback=self.quit_app)
        ]
        
        # Initialize rumps app
        super().__init__(
            name="uPNP Control",
            title="🎵",  # Default icon
            quit_button=None,
            menu=menu_items
        )
        
        # Register callbacks
        self.controller.on_volume_change(self.on_volume_change)
        self.controller.on_device_change(self.on_device_change)
        
        # Create Qt application for settings window
        if not QApplication.instance():
            self.qt_app = QApplication(sys.argv)
        else:
            self.qt_app = QApplication.instance()
            
        self.settings_window = None
        
        # Start device discovery
        logger.info("🔍 Starting device discovery...")
        self.refresh_devices()
        
        logger.info("🎵 App initialization complete!")

    def get_speed_status(self, volume):
        """Get speed status with a rockabilly twist"""
        if volume == 0:
            return "Status: Cool as a Cucumber 🥒"
        elif volume < 33:
            return "Status: Warming Up 🌡️"
        elif volume < 67:
            return "Status: Getting Hot 🔥"
        elif volume < 90:
            return "Status: Too Hot to Handle! 🎸"
        else:
            return "Status: PSYCHOBILLY FREAKOUT! 🔥🎸🔥"

    def get_volume_icon(self, volume):
        """Get appropriate volume icon based on level"""
        if volume == 0:
            return "🔇"
        elif volume < 33:
            return "🔈"
        elif volume < 67:
            return "🔉"
        else:
            return "🔊"
            
    def get_volume_bar(self, volume):
        """Create a fancy volume visualization"""
        # Spinal Tap inspired - goes to 11! 
        segments = 11
        filled = int((volume / 100.0) * segments)
        
        # Unicode block elements for a smooth gradient
        bars = "▁▂▃▄▅▆▇█"
        
        # Create the volume bar
        bar = ""
        for i in range(segments):
            if i < filled:
                # Calculate which block element to use for smoother gradient
                block_idx = int((i / filled) * (len(bars) - 1))
                bar += bars[block_idx]
            else:
                bar += "▁"  # Empty bar
                
        # Add heat indicators for maximum volume
        if volume >= 90:
            bar = "🔥" + bar + "🎸"
        elif volume >= 67:
            bar = "🎸" + bar + "🔥"
                
        return bar
        
    def toggle_plaid_mode(self, volume):
        """Toggle heat mode animation"""
        if volume >= 90 and not self.plaid_mode:
            self.plaid_mode = True
            if self.plaid_thread is None or not self.plaid_thread.is_alive():
                self.plaid_thread = threading.Thread(target=self._plaid_animation)
                self.plaid_thread.daemon = True
                self.plaid_thread.start()
        elif volume < 90:
            self.plaid_mode = False
            
    def _plaid_animation(self):
        """Run heat mode animation"""
        heat_patterns = ["🔥", "🎸", "⚡"]
        pattern_idx = 0
        
        while self.plaid_mode:
            if self.controller.current_device:
                device_name = self.controller.current_device.friendly_name
                self.title = f"{heat_patterns[pattern_idx]} {device_name} {heat_patterns[pattern_idx]}"
                pattern_idx = (pattern_idx + 1) % len(heat_patterns)
                time.sleep(0.3)
        
    def on_volume_change(self, volume):
        """Handle volume changes from device"""
        self.current_volume = volume
        self.update_display()
        self.toggle_plaid_mode(volume)
        
    def on_device_change(self, device):
        """Handle device changes"""
        if device:
            self.update_display()
            
    def update_display(self):
        """Update all display elements"""
        if self.current_volume is not None and self.controller.current_device:
            # Update volume display in menu
            volume_bar = self.get_volume_bar(self.current_volume)
            volume_icon = self.get_volume_icon(self.current_volume)
            self.volume_display.title = f"Volume: {volume_icon} {self.current_volume}% {volume_bar}"
            
            # Update speed status
            self.speed_display.title = self.get_speed_status(self.current_volume)
            
            # Update menu bar icon/title if not in heat mode
            if not self.plaid_mode:
                device_name = self.controller.current_device.friendly_name
                if self.current_volume == 100:
                    # Easter egg for maximum volume!
                    self.title = f"🤘 {device_name} 🎸"
                else:
                    self.title = f"{volume_icon} {device_name}"
        
    def refresh_devices(self, sender=None):
        """Refresh the list of available devices"""
        try:
            logger.info("🔄 Refreshing devices...")
            
            # Clear existing device menu items
            if hasattr(self.device_menu, '_items'):
                for item in list(self.device_menu._items):
                    self.device_menu.remove(item)
            
            # Refresh devices
            self.controller.refresh_devices()
            
            # Add device menu items
            devices_found = False
            for device in self.controller.devices.keys():
                devices_found = True
                item = rumps.MenuItem(
                    device,
                    callback=lambda x: self.select_device(x.title)
                )
                self.device_menu.add(item)
                
            if not devices_found:
                logger.info("😢 No devices found")
                self.device_menu.add(rumps.MenuItem("No devices found"))
                
        except Exception as e:
            logger.error(f"💥 Failed to refresh devices: {e}")
            if hasattr(self.device_menu, '_items'):
                for item in list(self.device_menu._items):
                    self.device_menu.remove(item)
            self.device_menu.add(rumps.MenuItem("Error refreshing devices"))
        
    def select_device(self, device_name):
        """Select a device"""
        if self.controller.select_device(device_name):
            # Update checkmarks
            for item in self.device_menu.values():
                item._menuitem.setState_(bool(item.title == device_name))
                
            # Get initial volume
            volume = self.controller.get_current_volume()
            if volume is not None:
                self.on_volume_change(volume)
        
    def show_settings(self, _):
        """Show settings window"""
        try:
            # Get list of devices
            devices = [device for device, _ in self.controller.devices.values()]
            
            # Create settings window
            self.settings_window = SettingsWindow(devices)
            self.settings_window.show()
            
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
            
    def apply_settings(self, settings):
        """Apply settings changes"""
        if 'default_device' in settings:
            self.select_device(settings['default_device'])
            
    def quit_app(self, sender=None):
        """Quit the application"""
        self.plaid_mode = False  # Stop heat animation
        if self.plaid_thread:
            self.plaid_thread.join(timeout=1.0)
        self.controller.stop_keyboard_listener()
        rumps.quit_application()

    def run(self):
        """Run the app"""
        try:
            # Start the controller
            self.controller.start()
            
            # Log startup
            logger.info("🎵 App initialization complete!")
            
            # Run the app
            super().run()
            
        except Exception as e:
            logger.error(f"💥 Failed to start app: {e}")

def main():
    """
    Start the menu bar app
    
    Trisha's Note: "Time to make some noise! 🎸"
    """
    try:
        # Ensure we're in the right directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the app
        logger.info("🚀 Launching uPNP Volume Control...")
        app = UPNPMenuBarApp()
        app.run()
    except Exception as e:
        logger.error(f"💥 Failed to start app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
