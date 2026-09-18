"""Chain definitions for supported EVM networks."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chain:
    """An EVM-compatible blockchain network."""

    name: str
    chain_id: int
    rpc_url: str
    native_symbol: str
    explorer_url: str
    rpc_urls: tuple[str, ...] = ()   # ordered fallbacks; rpc_url is tried first


CHAINS: dict[str, Chain] = {
    "ethereum": Chain(
        name="ethereum",
        chain_id=1,
        # 2026-09-18: primary swapped OFF https://eth.llamarpc.com -> HTTP 525
        # (Cloudflare "SSL handshake failed", edge->origin TLS). Their outage, not ours.
        rpc_url="https://ethereum-rpc.publicnode.com",
        rpc_urls=('https://eth.drpc.org', 'https://1rpc.io/eth', 'https://cloudflare-eth.com'),
        native_symbol="ETH",
        explorer_url="https://etherscan.io",
    ),
    "base": Chain(
        name="base",
        chain_id=8453,
        rpc_url="https://mainnet.base.org",
        rpc_urls=('https://base.publicnode.com', 'https://base.drpc.org'),
        native_symbol="ETH",
        explorer_url="https://basescan.org",
    ),
    "arbitrum": Chain(
        name="arbitrum",
        chain_id=42161,
        rpc_url="https://arb1.arbitrum.io/rpc",
        rpc_urls=('https://arbitrum-one-rpc.publicnode.com', 'https://arbitrum.drpc.org'),
        native_symbol="ETH",
        explorer_url="https://arbiscan.io",
    ),
    "polygon": Chain(
        name="polygon",
        chain_id=137,
        # 2026-09-18: primary swapped OFF https://polygon-rpc.com -> HTTP 401
        # "API key disabled, reason: tenant disabled" (-32051). Polygon retired its
        # keyless public mainnet endpoint (cutoff 31 Jul); this is PERMANENT, and
        # failover on AUTH is wrong by design (see wallet/rpc.py).
        rpc_url="https://polygon-bor-rpc.publicnode.com",
        rpc_urls=('https://polygon.drpc.org', 'https://1rpc.io/matic'),
        native_symbol="POL",
        explorer_url="https://polygonscan.com",
    ),
}


def endpoints_for(name: str) -> list[str]:
    """Ordered list of RPC endpoints for a chain: primary first, then fallbacks."""
    ch = get_chain(name)
    out = [ch.rpc_url, *ch.rpc_urls]
    seen: set[str] = set()
    return [u for u in out if not (u in seen or seen.add(u))]


def get_chain(name: str) -> Chain:
    """Get a chain by name. Raises ``KeyError`` if not found."""
    if name not in CHAINS:
        raise KeyError(
            f"Unknown chain '{name}'. Available: {list_chain_names()}"
        )
    return CHAINS[name]


def list_chain_names() -> list[str]:
    """Return the names of all supported chains."""
    return list(CHAINS.keys())
