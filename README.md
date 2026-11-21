# The Passport Page of a Country That Isn't There

[![make.fun](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)
[![rank](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/aldi235/the-passport-page-of-a-countr-2-20261121-0318/rank.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)
[![reward](https://make.fun/badge/the-passport-page-of-a-countr-2-20261121-0318/aldi235/the-passport-page-of-a-countr-2-20261121-0318/reward.svg)](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)

Entry for the [make.fun bounty](https://make.fun/bounty/the-passport-page-of-a-countr-2-20261121-0318)
"The Passport Page of a Country That Isn't There".

`main.py` draws an open passport spread for the invented free-port
**Republic of Talmar** entirely in code (Python + PIL, no network, no
external images) and writes it to `/output/entry.png` (1024×1024, under
1 MiB):

- **Data page** — coat of arms, drawn portrait of the holder
  (Elena Maris Kovac, born Port Talmar), personal data, signature, and a
  machine-readable zone with real ICAO 9303 check digits.
- **Visa page** — a Kingdom of Dravia visa sticker (with its harbour
  registration condition and a "FEE 12 ZLV PAID" stamp) and eight border
  stamps telling one coherent travel history: Dravia in September 2024,
  Corvinia in March 2025, every date after the passport's issue
  (12 Jun 2023) and before its expiry (11 Jun 2033).
- **Telling detail** — Endorsement 7: the holder is a licensed harbour
  pilot of the Port of Talmar, stamped for crew-list purposes — the
  paperwork of a small maritime free port.

## Run

```sh
python3 main.py          # writes /output/entry.png
ENTRY_PNG=entry.png python3 main.py   # write somewhere else
```

Requires Pillow (`pip install Pillow`). Fonts are bundled in `fonts/`
(Liberation family, SIL Open Font License). Output is deterministic:
repeated runs produce byte-identical PNGs.

## License

MIT — see [LICENSE](LICENSE).
