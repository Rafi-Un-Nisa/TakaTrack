"""Tests for category limits and caution messages (Hrishika)."""
import unittest

from testbase import TakaTrackTestCase


class CategoryLimitTests(TakaTrackTestCase):
    base = {"title": "Lunch", "amount": "300", "category": "Food",
            "spent_on": "2026-11-18", "note": ""}

    def test_new_category_asks_for_limit_and_does_not_save_yet(self):
        r = self.post(self.client, "/expenses/add", self.base)
        self.assertEqual(r.status_code, 200)
        self.assertIn("has no monthly spending limit yet", r.get_data(as_text=True))
        self.assertEqual(self.expense_count(), 0)

    def test_setting_limit_saves_category_and_expense(self):
        r = self.post(self.client, "/expenses/add", dict(self.base, limit="5000"))
        self.assertEqual(r.status_code, 302)
        cat = self.sql("SELECT * FROM categories WHERE name = 'Food'")[0]
        self.assertEqual(cat["monthly_limit"], 5000)
        self.assertEqual(self.expense_count(), 1)

    def test_skip_saves_without_limit_and_never_asks_again(self):
        r = self.post(self.client, "/expenses/add", dict(self.base, skip_limit="1"))
        self.assertEqual(r.status_code, 302)
        cat = self.sql("SELECT * FROM categories WHERE name = 'Food'")[0]
        self.assertIsNone(cat["monthly_limit"])
        r2 = self.post(self.client, "/expenses/add", self.base)  # second time: no question
        self.assertEqual(r2.status_code, 302)
        self.assertEqual(self.expense_count(), 2)

    def test_category_names_ignore_capital_letters(self):
        self.post(self.client, "/expenses/add", dict(self.base, limit="5000"))
        r = self.post(self.client, "/expenses/add", dict(self.base, category="food"))
        self.assertEqual(r.status_code, 302)                     # found "Food", no new question
        self.assertEqual(self.sql("SELECT COUNT(*) AS n FROM categories")[0]["n"], 1)

    def test_limit_set_in_limits_page_means_no_question(self):
        self.post(self.client, "/limits", {"new_name": "Transport", "limit": "2000"})
        r = self.post(self.client, "/expenses/add", dict(self.base, category="Transport"))
        self.assertEqual(r.status_code, 302)

    def test_caution_when_over_category_limit(self):
        cat = self.add_category("Transport", 1000)
        self.add_expense_row(cat, 800, "2026-11-05")
        data = dict(self.base, category="Transport", amount="300")
        r = self.post(self.client, "/expenses/add", data)
        self.assertEqual(r.status_code, 200)
        html = r.get_data(as_text=True)
        self.assertIn("Caution: Transport would reach ৳1,100 of its ৳1,000 monthly limit", html)
        self.assertEqual(self.expense_count(), 1)                # not saved until confirmed
        r2 = self.post(self.client, "/expenses/add", dict(data, confirm="1"), follow=True)
        self.assertEqual(self.expense_count(), 2)
        self.assertIn("Caution", r2.get_data(as_text=True))      # caution also shown after saving

    def test_no_caution_when_within_limit(self):
        cat = self.add_category("Transport", 1000)
        self.add_expense_row(cat, 500, "2026-11-05")
        r = self.post(self.client, "/expenses/add",
                      dict(self.base, category="Transport", amount="400"))
        self.assertEqual(r.status_code, 302)

    def test_caution_when_over_monthly_budget(self):
        self.post(self.client, "/budget", {"amount": "1000"})
        self.add_category("Fun", 99999)
        r = self.post(self.client, "/expenses/add",
                      dict(self.base, category="Fun", amount="1500"))
        self.assertIn("goes over your November 2026 budget", r.get_data(as_text=True))
        self.assertEqual(self.expense_count(), 0)

    def test_live_check_endpoint(self):
        cat = self.add_category("Transport", 1000)
        self.add_expense_row(cat, 800, "2026-11-05")
        data = self.client.get("/api/check?category=transport&amount=300&date=2026-11-18").get_json()
        self.assertEqual(len(data["warnings"]), 1)
        self.assertFalse(data["new_category"])
        data = self.client.get("/api/check?category=Brand+New&amount=10").get_json()
        self.assertTrue(data["new_category"])

    def test_invalid_amount_is_rejected(self):
        for bad in ("abc", "0", "-5", "12.5"):
            r = self.post(self.client, "/expenses/add", dict(self.base, amount=bad, limit="100"))
            self.assertEqual(r.status_code, 200, bad)
        self.assertEqual(self.expense_count(), 0)


if __name__ == "__main__":
    unittest.main()
