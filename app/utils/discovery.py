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

    def get_all_ips(self):
        """Get all non-loopback IP addresses."""
        ips = []
        try:
            # Method 1: Connect to internet (finds default route interface)
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                ips.append(ip)
        except Exception:
            pass
        
        try:
            # Method 2: Hostname resolution
            hostname = socket.gethostname()
            _, _, host_ips = socket.gethostbyname_ex(hostname)
            for ip in host_ips:
                if not ip.startswith("127.") and ip not in ips:
                    ips.append(ip)
        except Exception:
            pass
            
        if not ips:
            return ["127.0.0.1"]
        return ips

    def start(self):
        try:
            self.zeroconf = Zeroconf()
            ips = self.get_all_ips()
            
            # Service type: _http._tcp.local.
            # Service name: sensor-master._http._tcp.local.
            service_type = "_http._tcp.local."
            service_name = f"{self.name}.{service_type}"
            
            logger.info(f"Starting mDNS service announcement: {service_name} on {ips}:{self.port}")
            
            # Convert IPs to bytes
            addresses = [socket.inet_aton(ip) for ip in ips]
            
            self.info = ServiceInfo(
                service_type,
                service_name,
                addresses=addresses,
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
