#!/usr/bin/env python3
"""Poll OpenSea for new MLB Champions listings and flag star-player items.

Usage:
    OPENSEA_API_KEY=... python watch.py [--state state.json] [--json]

Reads the collection's recent `item_listed` events, matches NFT names against
watchlist.json, and prints new star-player listings as JSON. Seen event IDs
persist in the state file so only genuinely new listings are reported.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error

# NOTE: verify the exact collection slug on opensea.io before relying on this.
COLLECTION_SLUG = "mlbchampions"
EVENTS_URL = (
    "https://api.opensea.io/api/v2/events/collection/"
    f"{COLLECTION_SLUG}?event_type=item_listed&limit=50"
)
URGENT_PLAYERS = {"shohei ohtani", "aaron judge", "buster posey"}
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


def fetch_events(api_key):
    req = urllib.request.Request(EVENTS_URL)
    req.add_header("Accept", "application/json")
    req.add_header("X-API-KEY", api_key)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp).get("asset_events", [])
    except urllib.error.HTTPError as exc:
        print(f"OpenSea API error: HTTP {exc.code}", file=sys.stderr)
        sys.exit(1)


def load_watchlist(path):
    with open(path) as f:
        return [p.strip() for p in json.load(f) if p.strip()]


def match_player(nft_name, watchlist):
    lowered = nft_name.lower()
    return next((p for p in watchlist if p.lower() in lowered), None)


def extract_year(nft_name):
    m = YEAR_RE.search(nft_name or "")
    return m.group(0) if m else None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=os.path.join(here, "state.json"))
    args = ap.parse_args()

    api_key = os.environ.get("OPENSEA_API_KEY")
    if not api_key:
        print("Set OPENSEA_API_KEY first (see .env.example).", file=sys.stderr)
        sys.exit(1)

    watchlist = load_watchlist(os.path.join(here, "watchlist.json"))
    try:
        with open(args.state) as f:
            seen = set(json.load(f).get("seen_event_ids", []))
    except (FileNotFoundError, json.JSONDecodeError):
        seen = set()

    alerts = []
    for ev in fetch_events(api_key):
        event_id = str(ev.get("id") or ev.get("transaction", {}).get("transaction_hash", ""))
        if not event_id or event_id in seen:
            continue
        seen.add(event_id)

        nft = ev.get("nft") or {}
        nft_name = nft.get("name") or ""
        player = match_player(nft_name, watchlist)
        if not player:
            continue

        payment = ev.get("payment_token") or {}
        alerts.append({
            "player": player,
            "nft_name": nft_name,
            "year": extract_year(nft_name),
            "price": ev.get("payment", {}).get("quantity")
                     or (ev.get("payment_token") or {}).get("decimals") and None,
            "price_raw": (ev.get("payment") or {}).get("quantity"),
            "currency": payment.get("symbol"),
            "opensea_url": nft.get("opensea_url"),
            "listed_at": ev.get("event_timestamp"),
            "urgent": player.lower() in URGENT_PLAYERS,
        })

    with open(args.state, "w") as f:
        json.dump({"seen_event_ids": sorted(seen)}, f, indent=2)

    print(json.dumps({"new_star_listings": alerts}, indent=2))


if __name__ == "__main__":
    main()
