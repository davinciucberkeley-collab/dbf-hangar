# U11.2 profile: `plane design set <copy of concept-a-param> parameters.span_mm --value 820`

Main @ ef77e0d, 2026-11-24. Copy of `designs/concept-a-param` (192 KB plane.yaml, 8 designs in repo). Python 3.13 (miniforge), PyYAML has libyaml (`yaml.__with_libyaml__` is True), cProfile.
Machine: 12 logical CPUs, 23 % CPU busy and 7 python processes (other agents), so "mostly idle, not idle".

## Wall time
| run | profiled | unprofiled |
|---|---|---|
| 1 (fresh copy) | 26 s | 16 s |
| 2 (fresh copy) | 25 s | 17 s |

No persistent cache exists, so cold and warm are the same; each run is a new process (the in-process cache `geometry._BASE_PARTS` starts empty). Output of every run: mass 1273.0 -> 1259.4 g, "moved 52 part(s), 58 joint(s); interference: 0 new, 0 cleared".
Target 15 s idle: unprofiled we are at 16-17 s under load, so the margin is small but real work remains.

## Where the seconds go (profiled run 2, total 25.0 s; share of the 22.3 s in `set_op`)
| item | cumulative s | note |
|---|---|---|
| `set_op` total | 22.1 | rest is import time (`hangar/__init__` 2.6, `checks` 2.6) |
| `regeneration_report` | 13.6 | |
| `_interference` (two `interference_rows` calls, new and old) | 9.7 | 316 pair calls: 240 `_overlap_volume` (2.5 s unprofiled), 76 `_min_distance` (5.8 s unprofiled) |
| `yaml.safe_load` (pure-Python SafeLoader, 12 calls) | 7.7 | about 0.34 s per parse unprofiled (3.5 s total); CSafeLoader parses the same file in 0.036 s |
| ruamel load (`patch_text`) | 2.2 | |
| `mass_properties` (2 calls) | 1.1 | |
| mesh builds: `build_component` 8 calls, `generated_volumes` 16 calls | 0.8 / 0.8 | wing 0.8, fin tubes small |
| `trimesh boolean_manifold` 224 calls | 2.4 own | all in the overlap checks |
| `trimesh closest_point` 357 calls | 2.7 own, 6.4 cum | all in the gap checks |

Top own time: closest_point 2.74, boolean_manifold 2.21, rtree intersection 1.05, import open_code 0.84, yaml reader/scanner (many rows, 0.3-0.9 each, about 5.5 s together).

## Findings
1. Double mesh build is NOT confirmed. Meshes are already cached by content in `geometry._base_parts` (`_BASE_PARTS`, key from `_base_key`: geometry, cavities, mesh/generator files with mtime and size). Generators run 8 times for 4 regenerated parts (old and new design, once each); total mesh and boolean-build time is about 1.5 s, not the dominant cost. The 4 unchanged generated parts are built once.
2. The "doubling" that does cost time is `interference_rows` run for the new and the old design: 8.2 s unprofiled. A pair-level cache cannot help here: hashing the vertices and faces of both sides of every pair call, 316 calls gave 316 unique keys (0 repeats). With 52 parts moved, every pair that is checked has at least one moved side. Caching these would change nothing, and a shortcut would change results, so it is not proposed.
3. The cheap dominant waste is YAML: 12 parses of the 192 KB file with the pure-Python SafeLoader, although libyaml is installed. About 3.5 s unprofiled (profiler inflates it to 7.7 s). CSafeLoader gives the same data (equality to be proven by test) at 10x the speed. Expected saving about 3 s.
4. Imports cost about 2.6 s per run (trimesh, scipy, rtree); lazy imports could save a part of it but touch many files; not proposed.

## Conclusion
- Do not build the mesh cache (already exists; second build is not where time goes).
- Do the YAML fast loader: expected 16-17 s to about 13-14 s under the same load, meeting the target.
- Interference (about half of the time) is real geometry work with no repeated inputs; leave it unless Tristan wants the target tighter (options then: run old and new passes in two threads, test first; not briefed).
- Brief: `plans/2026-11-20-standardization/briefs/U11.2-speed.md`.
