#!/usr/bin/env python3
"""
🎭 AyeCompress - The Consciousness-Aware Compressor
Trisha says: "Let's make those logs as tight as a balanced ledger!"
"""
import re
import sys
from typing import Dict, List, Tuple

class AyeCompress:
    def __init__(self):
        # Control character markers
        self.MARKERS = {
            'timestamp': '\x01',  # SOH - Start of Heading
            'ipaddr': '\x02',     # STX - Start of Text
            'repeated': '\x03',   # ETX - End of Text
            'soap_start': '\x04', # EOT - End of Transmission
            'volume': '\x05',     # ENQ - Enquiry
            'caps_cmd': '\x06',   # ACK - Acknowledge
        }
        
        self.patterns = {
            'timestamp': r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}',
            'ipaddr': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            'soap': r'<.*?>.*?</.*?>',
            'spaces': r'    +',  # Match 4 or more spaces
            'caps_words': r'\b[A-Z]{3,}\b'  # Words with 3+ caps
        }
        
        self.seen_patterns: Dict[str, int] = {}         
        self.caps_commands = {}  # Store CAPS words as commands
        
    def compress(self, text: str) -> str:
        """Compress text using control characters as markers"""
        # Convert 4-space indents to tabs
        text = re.sub(self.patterns['spaces'], '\t', text)
        
        # Replace CAPS words with command markers
        def caps_replace(match):
            word = match.group(0)
            if word not in self.caps_commands:
                self.caps_commands[word] = len(self.caps_commands)
            return f"{self.MARKERS['caps_cmd']}{self.caps_commands[word]:02x}"
            
        text = re.sub(self.patterns['caps_words'], caps_replace, text)
        
        # Replace timestamps with marker + incremental ID
        text = self._compress_pattern(text, 'timestamp', self.patterns['timestamp'])
        
        # Replace IP addresses
        text = self._compress_pattern(text, 'ipaddr', self.patterns['ipaddr'])
        
        # Compress SOAP messages
        text = self._compress_soap(text)
        
        return text
        
    def _compress_pattern(self, text: str, marker_name: str, pattern: str) -> str:
        """Replace patterns with markers and IDs"""
        marker = self.MARKERS[marker_name]
        
        def replace_func(match):
            content = match.group(0)
            if content not in self.seen_patterns:
                self.seen_patterns[content] = len(self.seen_patterns)
            return f"{marker}{self.seen_patterns[content]:02x}"
            
        return re.sub(pattern, replace_func, text)
        
    def _compress_soap(self, text: str) -> str:
        """Smart compression for SOAP messages"""
        # Find volume values
        volume_pattern = r'<CurrentVolume>(\d+)</CurrentVolume>'
        text = re.sub(volume_pattern, 
                     lambda m: f"{self.MARKERS['volume']}{int(m.group(1)):02x}",
                     text)
        return text

def main():
    compressor = AyeCompress()
    
    # Read from stdin if no file provided
    input_text = sys.stdin.read()
    
    # Compress
    compressed = compressor.compress(input_text)
    
    # Output with stats
    original_size = len(input_text.encode('utf-8'))
    compressed_size = len(compressed.encode('utf-8'))
    ratio = (1 - compressed_size/original_size) * 100
    
    print(f"✨ Compressed! {original_size} -> {compressed_size} bytes ({ratio:.1f}% smaller)")
    print(compressed)

if __name__ == "__main__":
    main()
