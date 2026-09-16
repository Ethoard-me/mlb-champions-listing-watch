# MLB Champions Listing Watch

A small read-only monitor for the **MLB Champions** NFT collection on OpenSea.
It polls OpenSea's API for new `item_listed` events a few times a day and
flags listings featuring star players (multi-time All-Stars / Hall of Fame
caliber), with urgent alerts for **Shohei Ohtani**, **Aaron Judge**, and
**Buster Posey**.

This project exists to support a personal collection watch — it places no
orders and performs no trades.

## How it works

1. `watch.py` queries the OpenSea API v2 collection events endpoint for new
   listings.
2. Each listing's NFT name is matched against `watchlist.json`.
3. New matches are reported with the player name, collectible year (parsed
   from the NFT name when present), listing price, currency, and the OpenSea
   URL.
4. Seen event IDs are stored in `state.json` so repeat runs only surface
   genuinely new listings.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # then add your OpenSea API key
python watch.py
```

## API usage

Read-only, a handful of requests per day — comfortably within OpenSea's
free-tier rate limits.
