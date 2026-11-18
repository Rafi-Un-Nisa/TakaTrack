"""Tests for the recurring budget, rollover and savings (Rafi)."""
import sqlite3
import unittest

import services as svc
from testbase import TakaTrackTestCase


class RecurringBudgetAndRolloverTests(TakaTrackTestCase):
    def test_recurring_budget_creates_current_month(self):
        self.post(self.client, "/budget", {"amount": "10000"})
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("November 2026", page)
        self.assertIn("৳10,000", page)

    def test_banner_shows_leftover_from_last_month(self):
        self.october_with_leftover(7000)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("৳3,000 left over from October 2026", page)

    def test_carry_part_and_save_part(self):
        self.post(self.client, "/budget", {"amount": "10000"})
        self.october_with_leftover(7000)                       # leftover 3,000
        r = self.post(self.client, "/rollover/2026/10", {"carry": "2000", "save": "1000"})
        self.assertEqual(r.status_code, 302)
        nov = self.sql("SELECT * FROM monthly_budgets WHERE year=2026 AND month=11")[0]
        self.assertEqual(nov["base_amount"] + nov["carried_over"], 12000)
        self.assertEqual(svc.savings_total(sqlite3.connect(self.db_path), self.user_id()), 1000)
        page = self.client.get("/").get_data(as_text=True)
        self.assertIn("৳2,000 carried over", page)
        self.assertNotIn("left over from October", page)       # decision removes the banner

    def test_carry_creates_next_month_even_without_recurring_budget(self):
        self.october_with_leftover(7000)
        self.post(self.client, "/rollover/2026/10", {"carry": "3000", "save": "0"})
        nov = self.sql("SELECT * FROM monthly_budgets WHERE year=2026 AND month=11")[0]
        self.assertEqual((nov["base_amount"], nov["carried_over"]), (0, 3000))

    def test_cannot_share_out_more_than_leftover(self):
        self.october_with_leftover(7000)
        self.post(self.client, "/rollover/2026/10", {"carry": "3000", "save": "500"})
        self.assertEqual(self.sql("SELECT COUNT(*) AS n FROM rollovers")[0]["n"], 0)

    def test_month_can_only_be_decided_once(self):
        self.october_with_leftover(7000)
        self.post(self.client, "/rollover/2026/10", {"carry": "1000", "save": "1000"})
        self.post(self.client, "/rollover/2026/10", {"carry": "1000", "save": "1000"})
        self.assertEqual(self.sql("SELECT COUNT(*) AS n FROM rollovers")[0]["n"], 1)
        nov = self.sql("SELECT carried_over FROM monthly_budgets WHERE year=2026 AND month=11")[0]
        self.assertEqual(nov["carried_over"], 1000)            # not added twice

    def test_overspent_month_has_nothing_to_roll_over(self):
        self.october_with_leftover(12000)                      # spent more than budget
        page = self.client.get("/").get_data(as_text=True)
        self.assertNotIn("left over from", page)

    def test_current_month_cannot_be_closed(self):
        self.post(self.client, "/budget", {"amount": "10000"})
        self.post(self.client, "/rollover/2026/11", {"carry": "1", "save": "0"})
        self.assertEqual(self.sql("SELECT COUNT(*) AS n FROM rollovers")[0]["n"], 0)


if __name__ == "__main__":
    unittest.main()
