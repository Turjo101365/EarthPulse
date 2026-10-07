---
source: NASA FIRMS Documentation & Wooster et al. (2005)
title: NASA FIRMS and Fire Radiative Power (FRP) Science
category: physics_emissions
dataset: FIRMS_GLOBAL
satellite: MODIS, VIIRS
date: 2024-02-01
chunk_index: 0
---

# NASA FIRMS and Fire Radiative Power (FRP) Science

## NASA FIRMS Mission Architecture
The Fire Information for Resource Management System (FIRMS) is operated by the NASA Earth Science Data and Information System (ESDIS) at Goddard Space Flight Center. FIRMS ingests near-real-time (NRT) orbit passes from MODIS (Terra/Aqua) and VIIRS (S-NPP/NOAA-20/NOAA-21), executes spatial detection algorithms, and distributes vector fire footprints within 3 hours of satellite overpass (Ultra-Real-Time within 60 seconds of downlink via direct broadcast).

## Physics of Fire Radiative Power (FRP)
Fire Radiative Power (FRP), expressed in Megawatts (MW), measures the instantaneous rate of radiant thermal energy output from combustion:
- Measured through the MIR radiance method (Wooster et al., 2003, 2005):
  FRP = (A_pix * sigma / a) * (L_4 - L_4_bkg)
  where:
  - A_pix is the ground surface area of the satellite pixel footprint (m²).
  - sigma is the Stefan-Boltzmann constant (5.670374e-8 W/(m² K⁴)).
  - a is a sensor-specific empirical radiance coefficient (W m⁻² sr⁻¹ µm⁻¹ K⁻⁴).
  - L_4 is the 3.9 µm mid-infrared spectral radiance measured for the active fire pixel.
  - L_4_bkg is the mean 3.9 µm radiance of surrounding non-fire background pixels.

## Biomass Consumption and Atmospheric Emissions
The time-integral of FRP yields Fire Radiative Energy (FRE in Joules):
FRE = integral(FRP(t) dt)
Under the Wooster et al. formulation, the mass of dry biomass fuel combusted is directly proportional to FRE:
Biomass_Consumed (kg) = C_rad * FRE
where C_rad = 0.368 ± 0.015 kg/MJ.

From total combusted biomass, atmospheric greenhouse gas and aerosol emissions are calculated via emission factors (EF):
- Carbon Dioxide (CO₂): ~1,600 to 1,800 g CO₂ / kg dry biomass.
- Methane (CH₄): ~4.5 to 6.8 g CH₄ / kg dry biomass (28x higher 100-year Global Warming Potential than CO₂).
- Total Radiative Power: EarthPulse sums instantaneous FRP into Gigawatts (GW) of planetary thermal output.

## Hotspot vs. Confirmed Active Fire Distinction
A satellite hotspot detection is an identified thermal radiation anomaly. It should never be treated as an absolute guarantee of a catastrophic wildfire:
1. Low-intensity hotspots may represent controlled agricultural residue burning, trash incineration, or prescribed forest burns.
2. High-reflectance industrial surfaces, solar panels, and warm desert bare soil can occasionally trigger false alarms.
3. True active wildfires require validation through multi-temporal passes, contextual fire weather, and persistence clustering.
