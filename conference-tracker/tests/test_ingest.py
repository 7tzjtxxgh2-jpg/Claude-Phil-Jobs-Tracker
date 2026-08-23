"""Tests for the ingestion primitives.

Deliberately stdlib-only (unittest, no pytest) and network-free, so the suite
runs anywhere -- including a sandbox with no package index reachable.

The emphasis is on the failure modes rather than the happy paths. The whole
premise of this project is that a silent shortfall in a deadline tracker means
a call for papers you would have submitted to never appears, so the gates that
prevent that are what most need covering.
"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from philevents import store
from philevents.detail import deadline_candidates, extract_jsonld, parse_event
from philevents.errors import IngestAborted, StructureUnknown
from philevents.geo import Gazetteer, Place, haversine_miles, is_nearby
from philevents.listing import (extract_event_ids, plausibility_gate,
                                sweep_listing)


class TestListingExtraction(unittest.TestCase):
    def test_extracts_ids_in_order_without_duplicates(self):
        html = """
          <a href="/event/show/143379">SPEP</a>
          <a href="https://philevents.org/event/show/26594">FEW 2017</a>
          <a href="/event/show/143379">SPEP again</a>
        """
        self.assertEqual(extract_event_ids(html), ["143379", "26594"])

    def test_ignores_non_event_links(self):
        html = '<a href="/search/topic/642">Topics</a><a href="/help/">About</a>'
        self.assertEqual(extract_event_ids(html), [])

    def test_survives_attribute_reordering(self):
        """Regex on the URL shape, not the DOM, so markup churn does not break it."""
        html = '<a class="x" data-id="9" href="/event/show/555" title="t">E</a>'
        self.assertEqual(extract_event_ids(html), ["555"])


class TestSweep(unittest.TestCase):
    def test_stops_when_a_page_adds_nothing_new(self):
        pages = {
            1: '<a href="/event/show/1"></a><a href="/event/show/2"></a>',
            2: '<a href="/event/show/3"></a>',
            3: '<a href="/event/show/3"></a>',  # site clamps to the last real page
        }
        fetched = []

        def fake_fetch(url: str) -> str:
            page = int(url.rsplit("=", 1)[1])
            fetched.append(page)
            return pages.get(page, "")

        ids, count = sweep_listing(fake_fetch, "http://x/?page={page}")
        self.assertEqual(ids, ["1", "2", "3"])
        self.assertEqual(fetched, [1, 2, 3], "must stop once a page repeats itself")
        self.assertEqual(count, 3)

    def test_requires_page_placeholder(self):
        with self.assertRaises(ValueError):
            sweep_listing(lambda u: "", "http://x/no-placeholder")

    def test_respects_max_pages(self):
        """A site that always returns fresh IDs must not loop forever."""
        counter = iter(range(10_000))

        def endless(url: str) -> str:
            return f'<a href="/event/show/{next(counter)}"></a>'

        _, pages = sweep_listing(endless, "http://x/?page={page}", max_pages=4)
        self.assertEqual(pages, 4)


class TestPlausibilityGate(unittest.TestCase):
    def test_aborts_on_a_collapsed_sweep(self):
        """The F-5 case: the fetch broke and returned a fraction of the corpus."""
        with self.assertRaises(IngestAborted):
            plausibility_gate(12, [700, 690, 710])

    def test_allows_normal_variation(self):
        plausibility_gate(660, [700, 690, 710])  # ~94% of average

    def test_allows_bootstrap_with_no_history(self):
        plausibility_gate(700, [])

    def test_rejects_a_trivial_first_run(self):
        with self.assertRaises(IngestAborted):
            plausibility_gate(2, [])

    def test_ignores_zero_baselines(self):
        """A prior aborted run must not drag the average down and mask a failure."""
        with self.assertRaises(IngestAborted):
            plausibility_gate(10, [0, 0, 700])


class TestGeo(unittest.TestCase):
    def test_haversine_matches_published_distances(self):
        self.assertAlmostEqual(
            haversine_miles(37.7749, -122.4194, 34.0522, -118.2437), 347, delta=5)
        self.assertAlmostEqual(
            haversine_miles(47.6062, -122.3321, 45.5152, -122.6784), 145, delta=5)

    def test_identical_points_are_zero(self):
        self.assertEqual(haversine_miles(45.0, -122.0, 45.0, -122.0), 0.0)

    def test_ambiguous_city_resolves_to_most_populous(self):
        g = Gazetteer()
        g.add(Place("Portland", "US", "OR", 45.5152, -122.6784, 652503))
        g.add(Place("Portland", "US", "ME", 43.6591, -70.2568, 68408))
        self.assertEqual(g.lookup("Portland").admin1, "OR")
        self.assertEqual(g.lookup("Portland", region="ME").admin1, "ME")

    def test_unknown_city_returns_none(self):
        self.assertIsNone(Gazetteer().lookup("Nowhereville"))
        self.assertIsNone(Gazetteer().lookup(None))

    def test_unresolved_place_is_never_nearby(self):
        """An unknown location must not slip through the proximity filter."""
        near, distance = is_nearby(None, 47.6, -122.3, 120.0)
        self.assertFalse(near)
        self.assertIsNone(distance)

    def test_radius_boundary(self):
        g = Gazetteer()
        g.add(Place("Portland", "US", "OR", 45.5152, -122.6784, 652503))
        seattle = (47.6062, -122.3321)
        self.assertFalse(is_nearby(g.lookup("Portland"), *seattle, 120.0)[0])
        self.assertTrue(is_nearby(g.lookup("Portland"), *seattle, 200.0)[0])

    def test_missing_gazetteer_file_is_not_fatal(self):
        self.assertEqual(len(Gazetteer.from_geonames("/nonexistent/path")), 0)


class TestDetailParsing(unittest.TestCase):
    EVENT_HTML = """<html><head>
      <script type="application/ld+json">
      {"@type":"Event","name":"Workshop on Moral Status",
       "startDate":"2026-11-03","endDate":"2026-11-04",
       "location":{"@type":"Place","address":{"addressLocality":"Portland",
                   "addressRegion":"OR","addressCountry":"US"}},
       "description":"Submission deadline: 1 November 2026."}
      </script></head><body></body></html>"""

    def test_parses_schema_org_event(self):
        event = parse_event(self.EVENT_HTML, "1", "u")
        self.assertEqual(event.title, "Workshop on Moral Status")
        self.assertEqual(event.start_date, "2026-11-03")
        self.assertEqual((event.city, event.region, event.country), ("Portland", "OR", "US"))
        self.assertFalse(event.is_online)
        self.assertEqual(event.source, "json-ld")

    def test_missing_structured_data_raises_rather_than_returning_nulls(self):
        with self.assertRaises(StructureUnknown):
            parse_event("<html><body>an ordinary page</body></html>", "1", "u")

    def test_graph_wrapped_jsonld(self):
        html = ('<script type="application/ld+json">'
                '{"@graph":[{"@type":"WebSite"},{"@type":"Event","name":"X"}]}</script>')
        self.assertEqual(parse_event(html, "1", "u").title, "X")

    def test_malformed_jsonld_is_skipped_not_fatal(self):
        html = ('<script type="application/ld+json">{not json</script>'
                '<script type="application/ld+json">{"@type":"Event","name":"Y"}</script>')
        self.assertEqual(parse_event(html, "1", "u").title, "Y")

    def test_virtual_location_marks_event_online(self):
        html = ('<script type="application/ld+json">{"@type":"Event","name":"Z",'
                '"location":{"@type":"VirtualLocation","url":"https://zoom"}}</script>')
        self.assertTrue(parse_event(html, "1", "u").is_online)

    def test_hybrid_location_keeps_city_and_online_flag(self):
        html = ('<script type="application/ld+json">{"@type":"Event","name":"H",'
                '"location":[{"@type":"VirtualLocation","url":"https://zoom"},'
                '{"@type":"Place","address":{"addressLocality":"Seattle"}}]}</script>')
        event = parse_event(html, "1", "u")
        self.assertTrue(event.is_online)
        self.assertEqual(event.city, "Seattle")

    def test_no_jsonld_objects_at_all(self):
        self.assertEqual(extract_jsonld("<html></html>"), [])

    def test_deadline_candidates_finds_free_text_forms(self):
        text = ("Abstracts due by the end of September. "
                "The submission deadline is 1 Nov 2026.")
        hits = deadline_candidates(text)
        self.assertEqual(len(hits), 2)
        self.assertTrue(any("end of September" in h for h in hits),
                        "free-text deadlines must be surfaced, not just ISO dates")


class TestStore(unittest.TestCase):
    def setUp(self):
        self.conn = store.connect(os.path.join(tempfile.mkdtemp(), "t.db"))

    def _row(self, event_id="1", deadline="2026-09-01", title="T"):
        return dict(
            event_id=event_id, url=f"u/{event_id}", title=title, event_type=None,
            has_cfp=1, start_date="2026-11-03", end_date=None, deadline=deadline,
            deadline_is_exact=1, city="Portland", region="OR", country="US",
            lat=None, lon=None, is_online=0, topics="", body="", status="open",
            content_hash=store.content_hash(event_id, title, deadline))

    def test_insert_then_reseen_then_changed(self):
        self.assertEqual(store.upsert_event(self.conn, self._row()), "new")
        self.assertEqual(store.upsert_event(self.conn, self._row()), "unchanged")
        self.assertEqual(
            store.upsert_event(self.conn, self._row(deadline="2026-10-15")), "changed")

    def test_deadline_extension_is_recorded_for_the_digest(self):
        """The F-3 case inverted: a moved deadline is a headline, not a silent diff."""
        store.upsert_event(self.conn, self._row())
        store.upsert_event(self.conn, self._row(deadline="2026-10-15"))
        changes = self.conn.execute(
            "SELECT field, old_value, new_value FROM event_changes").fetchall()
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["field"], "deadline")
        self.assertEqual(changes[0]["new_value"], "2026-10-15")

    def test_recheck_window_selects_only_near_deadlines(self):
        store.upsert_event(self.conn, self._row("near", "2026-10-15"))
        store.upsert_event(self.conn, self._row("far", "2027-06-01"))
        due = store.events_due_for_recheck(self.conn, 45, today=date(2026, 9, 20))
        self.assertEqual(due, ["near"])

    def test_unparseable_deadline_is_rechecked_rather_than_assumed(self):
        store.upsert_event(self.conn, self._row("vague", "rolling"))
        due = store.events_due_for_recheck(self.conn, 45, today=date(2026, 9, 20))
        self.assertEqual(due, ["vague"])

    def test_past_deadline_drops_out_of_the_recheck_window(self):
        store.upsert_event(self.conn, self._row("gone", "2026-01-01"))
        self.assertEqual(
            store.events_due_for_recheck(self.conn, 45, today=date(2026, 9, 20)), [])

    def test_run_history_feeds_the_plausibility_gate(self):
        store.record_run(self.conn, events_found=700, events_new=5,
                         events_changed=1, parse_errors=0)
        store.record_run(self.conn, events_found=690, events_new=3,
                         events_changed=0, parse_errors=2)
        self.assertEqual(store.recent_sweep_sizes(self.conn), [690, 700])

    def test_content_hash_is_stable_and_distinguishing(self):
        self.assertEqual(store.content_hash("a", 1, None), store.content_hash("a", 1, None))
        self.assertNotEqual(store.content_hash("a", 1), store.content_hash("a", 2))


if __name__ == "__main__":
    unittest.main(verbosity=2)
