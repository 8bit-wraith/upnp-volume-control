"""
Event Server for uPNP Events
Trisha says: "Time to get this party started! 🎉"
"""

import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from xml.etree import ElementTree
from typing import Optional, Callable, Dict

logger = logging.getLogger(__name__)

class EventHandler(BaseHTTPRequestHandler):
    """Handle uPNP event callbacks"""
    
    callback: Optional[Callable] = None
    
    def do_NOTIFY(self):
        """Handle NOTIFY requests from uPNP devices"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            event_body = self.rfile.read(content_length).decode('utf-8')
            logger.debug(f"📥 Received event: {event_body}")
            
            # Parse the event XML
            root = ElementTree.fromstring(event_body)
            
            # Find LastChange element
            last_change = root.find('.//LastChange')
            if last_change is not None and last_change.text:
                # Parse LastChange XML
                change_data = ElementTree.fromstring(last_change.text)
                
                # Look for volume changes
                volume = change_data.find('.//Volume')
                if volume is not None:
                    try:
                        volume_val = float(volume.get('val', '0'))
                        logger.debug(f"🔊 Volume change event: {volume_val}")
                        if self.callback:
                            self.callback({'Volume': volume_val})
                    except ValueError:
                        logger.error("Invalid volume value in event")
            
            # Send response
            self.send_response(200)
            self.end_headers()
            
        except Exception as e:
            logger.error(f"Error handling event: {e}")
            self.send_response(500)
            self.end_headers()

class EventServer:
    """HTTP server for handling uPNP events"""
    
    def __init__(self, port: int = 8080):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        
    def start(self, callback: Callable):
        """Start the event server"""
        try:
            # Set the callback
            EventHandler.callback = callback
            
            # Create and start the server
            self.server = HTTPServer(('', self.port), EventHandler)
            logger.info(f"🚀 Starting event server on port {self.port}")
            
            # Run in a separate thread
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True  # Don't prevent program from exiting
            self.server_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start event server: {e}")
            
    def stop(self):
        """Stop the event server"""
        if self.server:
            logger.info("Stopping event server")
            self.server.shutdown()
            self.server.server_close()
