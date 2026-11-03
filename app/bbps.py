"""Bill-fetch adapter. Real BBPS/DISCOM access needs a registered BBPS operating unit (BBPOU) or
aggregator account, which we don't have, so DemoProvider stands in. Same interface for a real one."""
import hashlib, os, re

class BillNotFound(Exception): ...

class DemoProvider:
    """Deterministic fake: the same Consumer ID always returns the same bill. NOT real verification."""
    def fetch(self, cid: str) -> dict:
        if not re.fullmatch(r"\d{10}", cid):
            raise BillNotFound("Consumer ID must be 10 digits")
        h = int(hashlib.sha256(cid.encode()).hexdigest(), 16)
        return {"consumer_id": cid, "amount": 700 + h % 3800, "months": 1 + h % 2, "source": "demo"}

class RealProvider:
    def fetch(self, cid: str) -> dict:
        raise NotImplementedError("Wire your BBPS aggregator's bill-fetch call here and return the same dict.")

_provider = RealProvider() if os.getenv("BBPS_PROVIDER") == "real" else DemoProvider()
def fetch_bill(cid: str) -> dict:
    return _provider.fetch(cid)
