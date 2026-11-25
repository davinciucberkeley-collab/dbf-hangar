# W31-S2 lot D: airfoil coordinate files (checked 2026-11-24)

Files copied from the UIUC coordinate database into knowledge/airfoils/ (CRLF converted to LF; numbers unchanged). Licence: none stated on the page or in the files read.

| name | file | source URL | date checked | points upper/lower |
|---|---|---|---|---|
| Clark Y | knowledge/airfoils/clarky.dat | https://m-selig.ae.illinois.edu/ads/coord/clarky.dat (index: https://m-selig.ae.illinois.edu/ads/coord_database.html) | 2026-11-24 | 61 / 61 (read_airfoil parse check) |
| SD7037 | knowledge/airfoils/sd7037.dat | https://m-selig.ae.illinois.edu/ads/coord/sd7037.dat (index: https://m-selig.ae.illinois.edu/ads/coord_database.html) | 2026-11-24 | 32 / 30 (read_airfoil parse check) |

Parse check run: `PYTHONPATH=core C:/ProgramData/miniforge3/python.exe -c "from hangar.geom.wing import read_airfoil; ..."`, output "61 61" (clarky) and "32 30" (sd7037). Both files already begin with a title line, so no title line was inserted.
