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

Servos may add `frames` and `frames_source` (both or neither; `category: servo` only), used by `plane design place`:
```
frames:
  output: {point: [x, y, z], axis: [x, y, z]}        # output shaft: a point on it, direction pointing OUT of the case (axis-aligned, part-local)
  mount_face: {point: [x, y, z], normal: [x, y, z]}    # plane the ears sit against, OUTWARD normal toward the shaft side (axis-aligned)
frames_source: <text>   # where the numbers come from; "estimate" is allowed, a measured value names the drawing or measurement
```

Any part may add `ports` and `ports_source` (both or neither): the places a wire can start or end, used by `from_port` / `to_port` of a `wiring.harnesses[]` entry:
```
ports: {signal: {point: [x, y, z], direction: [x, y, z]}}   # part-local mm; direction points out of the case, need not be unit length
ports_source: <text>   # where the numbers come from; "estimate" is allowed
```
Port names are slugs (`^[a-z0-9][a-z0-9_]*$`).
