# Named airfoils

Airfoils that `airfoil_file` (wing_panel, tail_surfaces) accepts by name instead of a design-folder path.
A reference is "named" when it has no `.`, `/` or `\`; it resolves to a generated NACA 4-digit section (`naca2412`, case-insensitive), else to `knowledge/airfoils/<name>.dat`, else an error listing the known names; anything else is a design-folder-relative file.
Format: Selig or Lednicer .dat (`read_airfoil` reads both); first line a title; source URL and date checked in this table (the UIUC titles carry no URL or date, and the spec inserts a title only when none exists), then x y rows.

| name | airfoil | source |
|---|---|---|
| `s5010` | S5010 9.82 % | UIUC https://m-selig.ae.illinois.edu/ads/coord/s5010.dat, checked 2026-11-09 (as in the file's header) |
| `clarky` | Clark Y (Lednicer layout) | UIUC https://m-selig.ae.illinois.edu/ads/coord/clarky.dat, checked 2026-11-24 |
| `sd7037` | SD7037-092-88 | UIUC https://m-selig.ae.illinois.edu/ads/coord/sd7037.dat, checked 2026-11-24 |

NACA 4-digit names are generated, not stored.
