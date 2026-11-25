"""Tiny synthetic STEP writer: one axis-aligned box as a manifold solid brep (test helper, no CAD content)."""
from __future__ import annotations


def box_step(dx: float, dy: float, dz: float) -> str:
    ents: list[str] = []

    def add(s: str) -> int:
        ents.append(s)
        return len(ents)

    def pt(x, y, z):
        return add(f"CARTESIAN_POINT('',({x:.6f},{y:.6f},{z:.6f}))")

    def dr(x, y, z):
        return add(f"DIRECTION('',({x:.6f},{y:.6f},{z:.6f}))")

    P = {(i, j, k): pt(i * dx, j * dy, k * dz) for i in (0, 1) for j in (0, 1) for k in (0, 1)}
    V = {c: add(f"VERTEX_POINT('',#{p})") for c, p in P.items()}
    edges = {}

    def edge(a, b):
        if (a, b) in edges:
            return edges[(a, b)]
        pa = ents[P[a] - 1]
        d = [(q - p) for p, q in zip(a, b)]
        ln = (d[0] * dx + d[1] * dy + d[2] * dz)
        ln = abs(ln)
        vec = add(f"VECTOR('',#{dr(*d)},{ln:.6f})")
        line = add(f"LINE('',#{P[a]},#{vec})")
        e = add(f"EDGE_CURVE('',#{V[a]},#{V[b]},#{line},.T.)")
        edges[(a, b)] = (e, True)
        edges[(b, a)] = (e, False)
        return edges[(a, b)]

    faces = []
    for ax in range(3):
        u, v = [i for i in range(3) if i != ax]
        for side in (0, 1):
            def c(a, b):
                t = [0, 0, 0]
                t[ax], t[u], t[v] = side, a, b
                return tuple(t)
            loop = [c(0, 0), c(1, 0), c(1, 1), c(0, 1)]
            if side == 1:
                loop = loop[::-1]
            oes = []
            for n in range(4):
                e, fwd = edge(loop[n], loop[(n + 1) % 4])
                oes.append(add(f"ORIENTED_EDGE('',*,*,#{e},{'.T.' if fwd else '.F.'})"))
            el = add("EDGE_LOOP('',(" + ",".join(f"#{o}" for o in oes) + "))")
            fb = add(f"FACE_BOUND('',#{el},.T.)")
            o = [0.0, 0.0, 0.0]
            o[ax] = side * (dx, dy, dz)[ax]
            n = [0, 0, 0]
            n[ax] = 1 if side else -1
            rd = [0, 0, 0]
            rd[u] = 1
            a2 = add(f"AXIS2_PLACEMENT_3D('',#{pt(*o)},#{dr(*n)},#{dr(*rd)})")
            pl = add(f"PLANE('',#{a2})")
            faces.append(add(f"ADVANCED_FACE('',(#{fb}),#{pl},.T.)"))
    sh = add("CLOSED_SHELL('',(" + ",".join(f"#{f}" for f in faces) + "))")
    br = add(f"MANIFOLD_SOLID_BREP('box',#{sh})")
    ctx = add("( GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#%d)) "
              "GLOBAL_UNIT_ASSIGNED_CONTEXT((#%d,#%d,#%d)) REPRESENTATION_CONTEXT('c','3D') )"
              % (len(ents) + 2, len(ents) + 3, len(ents) + 4, len(ents) + 5))
    add("UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-07),#%d,'d','d')" % (len(ents) + 3))
    add("( LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.) )")
    add("( NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.) )")
    add("( NAMED_UNIT(*) SOLID_ANGLE_UNIT() SI_UNIT($,.STERADIAN.) )")
    rep = add(f"ADVANCED_BREP_SHAPE_REPRESENTATION('',(#{br}),#{ctx})")
    pc = add("APPLICATION_CONTEXT('automotive design')")
    add(f"APPLICATION_PROTOCOL_DEFINITION('international standard','automotive_design',2000,#{pc})")
    pcx = add(f"PRODUCT_CONTEXT('',#{pc},'mechanical')")
    pr = add(f"PRODUCT('box','box','',(#{pcx}))")
    pf = add(f"PRODUCT_DEFINITION_FORMATION('','',#{pr})")
    pdc = add(f"PRODUCT_DEFINITION_CONTEXT('part definition',#{pc},'design')")
    pd = add(f"PRODUCT_DEFINITION('design','',#{pf},#{pdc})")
    ps = add(f"PRODUCT_DEFINITION_SHAPE('','',#{pd})")
    add(f"SHAPE_DEFINITION_REPRESENTATION(#{ps},#{rep})")
    body = "\n".join(f"#{i + 1}={s};" for i, s in enumerate(ents))
    return ("ISO-10303-21;\nHEADER;\nFILE_DESCRIPTION(('synthetic box'),'2;1');\n"
            "FILE_NAME('b.step','2026-01-01',(''),(''),'','','');\n"
            "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));\nENDSEC;\nDATA;\n" + body
            + "\nENDSEC;\nEND-ISO-10303-21;\n")
