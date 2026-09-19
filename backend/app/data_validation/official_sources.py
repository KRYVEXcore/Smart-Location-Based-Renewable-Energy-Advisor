"""Which hosts count as an *official* Indian source for a production
tariff or incentive number.

Commercial calculators, solar vendors, blogs, news sites and aggregators
are never listed here, so a record citing one is rejected. The list is
deliberately explicit: adding a host is a reviewed decision.
"""

from urllib.parse import urlparse

# Any host under these suffixes is a Government of India / State Government
# domain (regulators, ministries, PIB, government CDNs, DISCOMs on gov.in).
OFFICIAL_HOST_SUFFIXES: tuple[str, ...] = (".gov.in", ".nic.in")

# Official organisations that do not use a gov.in domain.
OFFICIAL_HOSTS: frozenset[str] = frozenset(
    {
        "www.tnpdcl.org",  # Tamil Nadu Power Distribution Corporation Ltd (DISCOM)
        "tnpdcl.org",
        "www.mahadiscom.in",  # Maharashtra State Electricity Distribution Co. Ltd (DISCOM)
        "mahadiscom.in",
        "kseb.in",  # Kerala State Electricity Board Ltd (DISCOM)
        "www.kseb.in",
        "www.erckerala.org",  # Kerala State Electricity Regulatory Commission
        "erckerala.org",
    }
)


def is_official_source_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    if host in OFFICIAL_HOSTS:
        return True
    return any(host.endswith(suffix) for suffix in OFFICIAL_HOST_SUFFIXES)
