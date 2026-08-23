"""Distance filtering for attend-only events.

The university funds travel only for presenting, so events with no call for
papers are worth surfacing only when they are online or close to home. That
needs coordinates, which PhilEvents does not supply.

Strategy (plan section 5a):
  1. A bundled GeoNames extract, filtered to US/CA/MX. Offline, deterministic,
     free, no rate limit.
  2. A Claude fallback for small university towns under the population cutoff
     -- the same shape as the jobs repo's resolve_missing_states().
  3. Permanent caching, since a city's coordinates never change.

Distance is great-circle. That runs roughly 1.3-1.5x shorter than road
distance, so a 120-mile radius admits some places that are a three-hour drive
away. For a small local category that over-inclusion is cheap; the radius is a
config value if a tighter one is wanted.
"""
from __future__ import annotations

import csv
import math
import os
from dataclasses import dataclass

EARTH_RADIUS_MILES = 3958.7613

# Column offsets in the GeoNames "cities" gazetteer dumps. Documented at
# https://download.geonames.org/export/dump/readme.txt
_GN_NAME = 1
_GN_ASCII = 2
_GN_LAT = 4
_GN_LON = 5
_GN_COUNTRY = 8
_GN_ADMIN1 = 10
_GN_POPULATION = 14


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points, in statute miles."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = phi2 - phi1
    d_lambda = math.radians(lon2 - lon1)
    a = (math.sin(d_phi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class Place:
    name: str
    country: str
    admin1: str
    lat: float
    lon: float
    population: int


class Gazetteer:
    """Offline city lookup over a GeoNames extract.

    Keys are lower-cased city names. Where a name is ambiguous ("Portland" in
    both OR and ME; "Cambridge" in both the UK and MA) the most populous match
    wins unless the caller supplies a country or region to disambiguate --
    which is the right default for conference venues, since events cluster in
    larger cities.
    """

    def __init__(self) -> None:
        self._by_name: dict[str, list[Place]] = {}

    def __len__(self) -> int:
        return sum(len(v) for v in self._by_name.values())

    def add(self, place: Place) -> None:
        for key in {place.name.lower(), place.name.lower().replace(".", "")}:
            self._by_name.setdefault(key, []).append(place)

    @classmethod
    def from_geonames(cls, path: str, countries: set[str] | None = None) -> "Gazetteer":
        gazetteer = cls()
        if not os.path.exists(path):
            return gazetteer
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.reader(fh, delimiter="\t", quoting=csv.QUOTE_NONE):
                if len(row) <= _GN_POPULATION:
                    continue
                if countries and row[_GN_COUNTRY] not in countries:
                    continue
                try:
                    place = Place(
                        name=row[_GN_NAME],
                        country=row[_GN_COUNTRY],
                        admin1=row[_GN_ADMIN1],
                        lat=float(row[_GN_LAT]),
                        lon=float(row[_GN_LON]),
                        population=int(row[_GN_POPULATION] or 0),
                    )
                except ValueError:
                    continue
                gazetteer.add(place)
                if row[_GN_ASCII] and row[_GN_ASCII] != row[_GN_NAME]:
                    gazetteer.add(Place(**{**place.__dict__, "name": row[_GN_ASCII]}))
        return gazetteer

    def lookup(self, city: str | None, country: str | None = None,
               region: str | None = None) -> Place | None:
        """Best match for a city name, or None. Never guesses across countries."""
        if not city:
            return None
        matches = self._by_name.get(city.strip().lower())
        if not matches:
            return None
        if country:
            narrowed = [p for p in matches if p.country == country.upper()]
            matches = narrowed or []
        if region:
            by_region = [p for p in matches if p.admin1.upper() == region.upper()]
            matches = by_region or matches
        if not matches:
            return None
        return max(matches, key=lambda p: p.population)


def is_nearby(place: Place | None, home_lat: float, home_lon: float,
              radius_miles: float) -> tuple[bool, float | None]:
    """Return (within_radius, distance). Unresolved places are never 'nearby'.

    An unknown location must not silently pass the filter: better to surface it
    as unresolved than to imply a distance we did not compute.
    """
    if place is None:
        return False, None
    distance = haversine_miles(home_lat, home_lon, place.lat, place.lon)
    return distance <= radius_miles, distance
