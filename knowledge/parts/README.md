# Real-parts library

One folder per part: `knowledge/parts/<part-id>/part.yaml` (plus mesh files its geometry names). A design uses it with the
`library_part` generator (`params: {part: <part-id>}`) and a BOM item `library_part: <part-id>`; T8 checks both agree.
List and show with `plane parts list` / `plane parts show`.

```
id: <slug, equals the folder name>
name: <string>
category: motor|propeller|esc|battery|servo|flight-controller|receiver|gps|sensor|connector|fastener|structure|other
vendor: <string>
part_number: <string>
url: <http(s) url>
mass_g: <number > 0>
dimensions_mm: [x, y, z]            # envelope, part-local frame
cad_status: vendor-cad | representative-envelope
cad_source: <string: URL of the vendor CAD, or where the envelope came from>
verified: {by: <string>, date: 'YYYY-MM-DD', method: <string>}
geometry: {generator: <registered generator>, params: {...}}   # same shape as a component's geometry; file paths resolve against the part's folder
```
