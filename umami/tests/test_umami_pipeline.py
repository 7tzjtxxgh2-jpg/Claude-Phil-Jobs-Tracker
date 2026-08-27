#!/usr/bin/env python3
"""End-to-end checks for the Umami ingest -> plan pipeline.

Umami's real export container is not documented publicly, so these fixtures
cover the plausible shapes: one JSON array, a book-wrapped object, a file per
recipe, newline-delimited JSON, and an HTML export with embedded JSON-LD. The
ingester is expected to handle all of them without being told which is which.

    python3 tests/test_umami_pipeline.py
"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import plan_week
import umami_ingest as ing


def recipe(name, **overrides):
    base = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": name,
        "recipeIngredient": ["2 cups flour", "1 tsp salt", "3 large eggs"],
        "recipeInstructions": [
            {"@type": "HowToStep", "text": "Mix everything."},
            {"@type": "HowToStep", "text": "Cook it."},
        ],
        "recipeYield": "4 servings",
        "prepTime": "PT15M",
        "cookTime": "PT30M",
        "recipeCategory": "Dinner",
        "recipeCuisine": "Italian",
        "keywords": "weeknight, quick",
    }
    base.update(overrides)
    return base


class Normalization(unittest.TestCase):
    def test_iso_durations(self):
        self.assertEqual(ing.to_minutes("PT30M"), 30)
        self.assertEqual(ing.to_minutes("PT1H30M"), 90)
        self.assertEqual(ing.to_minutes("PT2H"), 120)
        self.assertEqual(ing.to_minutes("P1DT2H"), 1560)
        self.assertEqual(ing.to_minutes("PT90S"), 2)

    def test_loose_durations(self):
        self.assertEqual(ing.to_minutes("1 hr 30 min"), 90)
        self.assertEqual(ing.to_minutes("45 minutes"), 45)
        self.assertEqual(ing.to_minutes(25), 25)
        self.assertIsNone(ing.to_minutes(None))

    def test_total_is_derived_when_absent(self):
        out = ing.normalize(recipe("X"), "Book", "f.json")
        self.assertEqual(out["total_minutes"], 45)

    def test_explicit_total_wins(self):
        out = ing.normalize(recipe("X", totalTime="PT20M"), "Book", "f.json")
        self.assertEqual(out["total_minutes"], 20)

    def test_instruction_shapes(self):
        as_string = ing.normalize(
            recipe("A", recipeInstructions="1. Chop.\n2. Fry.\n\n3. Serve."),
            "B", "f.json")
        self.assertEqual([t for _, t in as_string["instructions"]],
                         ["Chop.", "Fry.", "Serve."])

        sectioned = ing.normalize(recipe("A", recipeInstructions=[{
            "@type": "HowToSection", "name": "Sauce",
            "itemListElement": [{"@type": "HowToStep", "text": "Simmer."}],
        }]), "B", "f.json")
        self.assertEqual(sectioned["instructions"], [("Sauce", "Simmer.")])

        plain_list = ing.normalize(
            recipe("A", recipeInstructions=["Do this", "Then that"]), "B", "f.json")
        self.assertEqual(len(plain_list["instructions"]), 2)

    def test_ingredient_shapes(self):
        split = ing.normalize(recipe("A", recipeIngredient=[
            {"quantity": "2", "unit": "cups", "name": "flour"}]), "B", "f.json")
        self.assertEqual(split["ingredients"], ["2 cups flour"])

        blob = ing.normalize(
            recipe("A", recipeIngredient="- 2 eggs\n- 1 cup milk"), "B", "f.json")
        self.assertEqual(blob["ingredients"], ["2 eggs", "1 cup milk"])

    def test_tags_from_string_and_list(self):
        out = ing.normalize(recipe("A", keywords=["vegan", "quick"],
                                   suitableForDiet="https://schema.org/VeganDiet"),
                            "B", "f.json")
        values = {v.lower() for _, v in out["tags"]}
        self.assertTrue({"vegan", "quick", "dinner", "italian"} <= values)

    def test_author_and_yield_variants(self):
        out = ing.normalize(recipe("A", author={"@type": "Person", "name": "Phil"},
                                   recipeYield=6), "B", "f.json")
        self.assertEqual(out["author"], "Phil")
        self.assertEqual(out["servings"], 6)

    def test_id_is_stable_without_an_explicit_one(self):
        a = ing.normalize(recipe("Stew"), "B", "one.json")["id"]
        b = ing.normalize(recipe("Stew"), "Other", "two.json")["id"]
        self.assertEqual(a, b)
        self.assertNotEqual(a, ing.normalize(recipe("Soup"), "B", "one.json")["id"])

    def test_explicit_id_is_preferred(self):
        out = ing.normalize(recipe("A", **{"@id": "umami:123"}), "B", "f.json")
        self.assertEqual(out["id"], "umami:123")


class Discovery(unittest.TestCase):
    def test_finds_recipes_in_a_bare_array(self):
        found = list(ing.iter_recipes([recipe("A"), recipe("B")]))
        self.assertEqual(len(found), 2)

    def test_finds_recipes_nested_under_a_book(self):
        doc = {"recipeBooks": [
            {"name": "Weeknights", "recipes": [recipe("A"), recipe("B")]},
            {"name": "Baking", "recipes": [recipe("C")]},
        ]}
        found = list(ing.iter_recipes(doc))
        self.assertEqual(len(found), 3)
        self.assertEqual({b for _, b in found}, {"Weeknights", "Baking"})

    def test_finds_recipes_in_a_graph(self):
        doc = {"@context": "https://schema.org",
               "@graph": [{"@type": "WebSite"}, recipe("A")]}
        self.assertEqual(len(list(ing.iter_recipes(doc))), 1)

    def test_does_not_descend_into_a_recipe(self):
        # nutrition/author sub-objects must not be mistaken for extra recipes
        doc = recipe("A", nutrition={"@type": "NutritionInformation",
                                     "calories": "350 calories"},
                     author={"@type": "Person", "name": "Phil"})
        self.assertEqual(len(list(ing.iter_recipes(doc))), 1)

    def test_non_schema_shape_still_recognized(self):
        doc = {"title": "Chili", "ingredients": ["beans"], "directions": ["Simmer."]}
        self.assertTrue(ing.looks_like_recipe(doc))


class Ingest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.export = self.root / "export"
        self.export.mkdir()
        self.db = self.root / "library.db"
    def tearDown(self):
        self.tmp.cleanup()

    def _write_mixed_export(self):
        # shape 1: one array file
        (self.export / "all.json").write_text(
            json.dumps([recipe("Carbonara"), recipe("Ragu")]), encoding="utf-8")
        # shape 2: book-wrapped object
        (self.export / "books.json").write_text(json.dumps(
            {"recipeBooks": [{"name": "Baking",
                              "recipes": [recipe("Focaccia", totalTime="PT3H")]}]}),
            encoding="utf-8")
        # shape 3: one file per recipe, in a per-book folder
        book = self.export / "Weeknights"
        book.mkdir()
        (book / "tacos.json").write_text(json.dumps(recipe("Tacos")), encoding="utf-8")
        # shape 4: newline-delimited JSON
        (self.export / "stream.json").write_text(
            "\n".join(json.dumps(recipe(n)) for n in ("Pho", "Laksa")), encoding="utf-8")
        # shape 5: HTML export with embedded JSON-LD
        (self.export / "roast.html").write_text(
            '<html><head><script type="application/ld+json">'
            + json.dumps(recipe("Roast Chicken"))
            + "</script></head><body>Roast Chicken</body></html>", encoding="utf-8")
        # noise the walker must ignore
        (self.export / "README.txt").write_text("not a recipe", encoding="utf-8")
        (self.export / "settings.json").write_text(
            json.dumps({"theme": "dark", "units": "metric"}), encoding="utf-8")

    def test_ingests_every_shape(self):
        self._write_mixed_export()
        conn, counts = ing.ingest([str(self.export)], str(self.db))
        self.assertEqual(counts["recipes"], 7)
        titles = {r["title"] for r in conn.execute("SELECT title FROM recipes")}
        self.assertEqual(titles, {"Carbonara", "Ragu", "Focaccia", "Tacos",
                                  "Pho", "Laksa", "Roast Chicken"})
        books = {r["book"] for r in conn.execute("SELECT DISTINCT book FROM recipes")}
        self.assertIn("Baking", books)
        self.assertIn("Weeknights", books)

    def test_child_tables_populated(self):
        self._write_mixed_export()
        conn, _ = ing.ingest([str(self.export)], str(self.db))
        rid = conn.execute(
            "SELECT id FROM recipes WHERE title = 'Carbonara'").fetchone()[0]
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM ingredients WHERE recipe_id = ?",
                         (rid,)).fetchone()[0], 3)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM instructions WHERE recipe_id = ?",
                         (rid,)).fetchone()[0], 2)
        self.assertGreaterEqual(
            conn.execute("SELECT COUNT(*) FROM tags WHERE recipe_id = ?",
                         (rid,)).fetchone()[0], 4)

    def test_reingest_is_idempotent(self):
        self._write_mixed_export()
        ing.ingest([str(self.export)], str(self.db))
        conn, _ = ing.ingest([str(self.export)], str(self.db))
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM recipes").fetchone()[0], 7)
        self.assertEqual(
            conn.execute("SELECT COUNT(*) FROM ingredients").fetchone()[0], 21)

    def test_zip_export(self):
        import zipfile
        self._write_mixed_export()
        archive = self.root / "export.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            for path in self.export.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(self.export))
        conn, counts = ing.ingest([str(archive)], str(self.db))
        self.assertEqual(counts["recipes"], 7)

    def test_empty_export_reports_nothing_found(self):
        (self.export / "settings.json").write_text('{"theme":"dark"}', encoding="utf-8")
        _, counts = ing.ingest([str(self.export)], str(self.db))
        self.assertEqual(counts["recipes"], 0)


class Planning(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        export = self.root / "export"
        export.mkdir()
        (export / "all.json").write_text(json.dumps([
            recipe(f"Recipe {i}", totalTime=f"PT{20 + i * 10}M",
                   keywords="vegan" if i % 2 else "meat")
            for i in range(12)
        ]), encoding="utf-8")
        self.db = self.root / "library.db"
        ing.ingest([str(export)], str(self.db))
    def tearDown(self):
        self.tmp.cleanup()

    def test_builds_a_full_week(self):
        conn = plan_week.open_library(self.db)
        chosen = plan_week.select_recipes(
            plan_week.load_candidates(conn), 7, seed=1)
        plan = plan_week.build_plan(chosen, date(2026, 8, 31), 7)
        self.assertEqual(len(plan), 7)
        self.assertEqual(plan[0]["date"], "2026-08-31")
        self.assertEqual(plan[-1]["date"], "2026-09-06")
        self.assertEqual(len({e["recipe"]["id"] for e in plan}), 7)

    def test_seed_is_reproducible(self):
        conn = plan_week.open_library(self.db)
        cands = plan_week.load_candidates(conn)
        a = [r["id"] for r in plan_week.select_recipes(cands, 5, seed=42)]
        b = [r["id"] for r in plan_week.select_recipes(cands, 5, seed=42)]
        self.assertEqual(a, b)

    def test_time_and_tag_filters(self):
        conn = plan_week.open_library(self.db)
        quick = plan_week.load_candidates(conn, max_minutes=50)
        self.assertTrue(all(r["total_minutes"] <= 50 for r in quick))
        self.assertLess(len(quick), 12)
        vegan = plan_week.load_candidates(conn, include=["vegan"])
        self.assertEqual(len(vegan), 6)
        self.assertTrue(all("vegan" in [t.lower() for t in r["tags"]] for r in vegan))
        not_vegan = plan_week.load_candidates(conn, exclude=["vegan"])
        self.assertEqual(len(not_vegan), 6)

    def test_history_holds_recipes_back(self):
        conn = plan_week.open_library(self.db)
        chosen = plan_week.select_recipes(plan_week.load_candidates(conn), 7, seed=3)
        plan = plan_week.build_plan(chosen, date.today(), 7)
        plan_week.commit_plan(conn, plan)
        held = plan_week.recently_planned(conn, 28)
        self.assertEqual(len(held), 7)
        remaining = plan_week.load_candidates(conn, exclude_recipe_ids=tuple(held))
        self.assertEqual(len(remaining), 5)
        self.assertFalse({r["id"] for r in remaining} & held)

    def test_grocery_rollup_merges_shared_ingredients(self):
        conn = plan_week.open_library(self.db)
        plan = plan_week.build_plan(
            plan_week.select_recipes(plan_week.load_candidates(conn), 3, seed=7),
            date(2026, 8, 31), 3)
        groceries = plan_week.grocery_list(plan)
        # every fixture recipe shares the same three ingredients
        self.assertEqual(set(groceries), {"flour", "salt", "large eggs"})
        self.assertTrue(all(len(v) == 3 for v in groceries.values()))

    def test_ingredient_normalization(self):
        self.assertEqual(
            plan_week.normalize_ingredient("1 1/2 cups (350g) plain flour, sifted"),
            "plain flour")
        self.assertEqual(plan_week.normalize_ingredient("3 large eggs"), "large eggs")
        self.assertEqual(plan_week.normalize_ingredient("Salt"), "salt")

    def test_markdown_and_ics_render(self):
        conn = plan_week.open_library(self.db)
        plan = plan_week.build_plan(
            plan_week.select_recipes(plan_week.load_candidates(conn), 7, seed=9),
            date(2026, 8, 31), 7)
        md = plan_week.render_markdown(plan, plan_week.grocery_list(plan),
                                       date(2026, 8, 31), 7)
        self.assertIn("# Meal plan: Mon 31 Aug", md)
        self.assertIn("## Grocery list", md)
        for entry in plan:
            self.assertIn(entry["recipe"]["title"], md)

        ics = plan_week.render_ics(plan)
        self.assertTrue(ics.startswith("BEGIN:VCALENDAR"))
        self.assertTrue(ics.rstrip().endswith("END:VCALENDAR"))
        self.assertEqual(ics.count("BEGIN:VEVENT"), 7)
        self.assertEqual(ics.count("END:VEVENT"), 7)
        self.assertIn("DTSTART;VALUE=DATE:20260831", ics)
        self.assertIn("DTEND;VALUE=DATE:20260901", ics)

    def test_cli_writes_outputs(self):
        out = self.root / "out"
        rc = plan_week.main([
            "--db", str(self.db), "--days", "5", "--start", "2026-08-31",
            "--out", str(out), "--ics", "--seed", "11",
        ])
        self.assertEqual(rc, 0)
        for name in ("meal-plan-2026-08-31.md", "meal-plan-2026-08-31.json",
                     "meal-plan-2026-08-31.ics"):
            self.assertTrue((out / name).exists(), name)
        payload = json.loads((out / "meal-plan-2026-08-31.json").read_text())
        self.assertEqual(len(payload["plan"]), 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
