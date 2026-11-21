"""Design-local calculations for the claims-mini fixture. Registered by name in CALCS."""


def hover_tw(thrust_g, mass_g):
    return {"tw": thrust_g / mass_g}


CALCS = {"hover_tw": hover_tw}
