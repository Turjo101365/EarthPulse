---
source: NOAA/NASA JPSS Mission Office
title: VJ114IMG / VJ114IMGML Product Guide: NOAA-20 VIIRS 375m Active Fire
category: datasets
dataset: VJ114IMG
satellite: NOAA-20
date: 2024-02-15
chunk_index: 0
---

# VJ114IMG / VJ114IMGML Product Guide: NOAA-20 VIIRS 375m Active Fire

## Satellite Mission and Orbit
VJ114IMG represents the 375m active fire product from the VIIRS sensor aboard NOAA-20 (formerly JPSS-1), launched in November 2017. NOAA-20 flies in the same orbital plane as Suomi-NPP but precedes or trails it by exactly 50 minutes.

## Dual-Satellite 50-Minute Observation Advantage
Because NOAA-20 and Suomi-NPP scan the same geographic territory 50 minutes apart:
1. **Fire Front Velocity**: EarthPulse tracks the progression vector of advancing flame perimeters between consecutive passes.
2. **False Positive Suppression**: Ephemeral glint anomalies do not persist across 50 minutes, allowing reliable automated filtering.
3. **Cloud Clearing**: Moving cloud decks often reveal active fires on the second pass that were obscured 50 minutes earlier.
