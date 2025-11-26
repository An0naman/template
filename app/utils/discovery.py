import socket
import logging
from zeroconf import ServiceInfo, Zeroconf

logger = logging.getLogger(__name__)

class ServiceAnnouncer:
    def __init__(self, port=5001, name="sensor-master"):
        self.port = port
        self.name = name
        self.zeroconf = None
        self.info = None

    def get_local_ip(self):
        """Try to determine the local IP address that is reachable from the network."""
        try:
            # This doesn't actually connect, but helps find the interface used for routing
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        try:
            self.zeroconf = Zeroconf()
            local_ip = self.get_local_ip()
            
            # Service type: _http._tcp.local.
            # Service name: sensor-master._http._tcp.local.
            service_type = "_http._tcp.local."
            service_name = f"{self.name}.{service_type}"
            
            logger.info(f"Starting mDNS service announcement: {service_name} on {local_ip}:{self.port}")
            
            self.info = ServiceInfo(
                service_type,
                service_name,
                addresses=[socket.inet_aton(local_ip)],
                port=self.port,
                properties={'version': '1.0.0', 'type': 'sensor-master'},
                server=f"{self.name}.local.",
            )
            
            self.zeroconf.register_service(self.info)
            logger.info("mDNS service registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to start mDNS service: {e}")

    def stop(self):
        if self.zeroconf and self.info:
            logger.info("Stopping mDNS service announcement...")
            self.zeroconf.unregister_service(self.info)
            self.zeroconf.close()
            self.zeroconf = None
            self.info = None
