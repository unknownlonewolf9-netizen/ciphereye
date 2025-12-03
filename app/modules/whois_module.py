from .base import OSINTModule
import whois
import time

class WhoisModule(OSINTModule):
    name = "whois"
    description = "Perform WHOIS lookup on domain"

    def run(self, target: str, **kwargs):
        started = time.time()
        try:
            data = whois.whois(target)
            out = dict(data) if data else {}
            return {
                "module": self.name,
                "target": target,
                "success": True,
                "duration_s": round(time.time() - started, 3),
                "data": out
            }
        except Exception as e:
            return {
                "module": self.name,
                "target": target,
                "success": False,
                "duration_s": round(time.time() - started, 3),
                "error": str(e)
            }

def get_module():
    return WhoisModule()
