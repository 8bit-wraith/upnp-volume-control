#!/bin/bash
# 🎵 Denon Volume Control Packet Capture
# Trisha says: "Let's audit those sound waves!" 

# Number of packets to capture
PACKETS=25

echo "🎤 Starting capture for $PACKETS packets..."
sudo tcpdump -i en0 -c $PACKETS -w /tmp/denon_control.pcap 'host 192.168.192.187 and port 60006' &
TCPDUMP_PID=$!

echo "🎚️ Adjust the volume while capture is running..."
wait $TCPDUMP_PID

echo "📊 Analyzing volume control packets..."
sudo tcpdump -r /tmp/denon_control.pcap -A -n | grep -A 4 -B 4 'Volume'

echo "✨ Capture complete! Check out those beautiful SOAP packets!"
