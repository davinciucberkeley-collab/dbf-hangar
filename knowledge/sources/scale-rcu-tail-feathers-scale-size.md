---
id: scale-rcu-tail-feathers-scale-size
title: Tail feathers scale size (RCUniverse forum thread)
authors: RCUniverse forum members (uhu, da Rock, HighPlains, Roger_Martin, buzzard bait, mesae, BMatthews)
year: 2006
url: https://www.rcuniverse.com/forum/aerodynamics-76/4279429-tail-feathers-scale-size.html
type: website
retrieved: 2026-11-24
verified: true
---

## Summary
Forum discussion of whether scale RC models need larger tail surfaces than the original. Opinions only, not tested data; modern radios reduce the need, and most posters regard a larger stabilizer as a barely visible deviation from scale.

## Usable rules / numbers
- Commercial kits and plans often enlarge scale tails by 10 to 33 percent (original post). Opinion-level, not tested.
- Tail volume (S_tail/S_wing) x (arm/chord) is dimensionless, so the same number applies at any scale (buzzard bait post).
- Under geometric scaling the arm shrinks by s and area by s^2, so tail effectiveness in absolute terms drops and low Reynolds number reduces it further (Roger_Martin post).
- A larger stabilizer lets the CG move aft, which helps short-nosed scale models; enlarging span helps more than chord (buzzard bait, mesae posts).

## How we could use it
- Scale-adjustment field `tail_enlargement` default 1.0 to 1.33 on area, applied only if scale-size tail volume falls below the MIT range (std-mit-unified-desrules, Vh 0.30 to 0.60, Vv 0.02 to 0.05).
