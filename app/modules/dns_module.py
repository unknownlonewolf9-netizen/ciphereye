from .base import OSINTModule
import dns.resolver
import time

class DNSModule(OSINTModule):
    name = "dns"
    description = "Perform DNS A, AAAA, and MX record lookups"

    def run(self, target: str, **kwargs):
        started = time.time()
        results = {}
        
        # Record types to look for
        record_types = ["A", "AAAA", "MX", "NS", "TXT"]
        
        for rtype in record_types:
            try:
                answers = dns.resolver.resolve(target, rtype)
                # Convert answers to string list
                results[rtype] = [str(r) for r in answers]
            except Exception:
                # If no record found or error, skip
                results[rtype] = []

        return {
            "module": self.name,
            "target": target,
            "success": True,
            "duration_s": round(time.time() - started, 3),
            "data": results
        }

def get_module():
    return DNSModule()
