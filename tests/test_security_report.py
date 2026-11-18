"""Tests for money format, login/privacy and the Excel report (Samia)."""
import io
import unittest

import pandas as pd

import services as svc
from testbase import TakaTrackTestCase


class FormatTests(unittest.TestCase):
    def test_taka_format_uses_bangladeshi_grouping(self):
        self.assertEqual(svc.format_taka(1234567), "৳12,34,567")
        self.assertEqual(svc.format_taka(999), "৳999")
        self.assertEqual(svc.format_taka(-45000), "-৳45,000")


class SecurityAndReportTests(TakaTrackTestCase):
    def test_login_required(self):
        anonymous = self.app.test_client()
        self.assertEqual(anonymous.get("/").status_code, 302)
        self.assertEqual(anonymous.get("/report.xlsx").status_code, 302)

    def test_post_without_csrf_token_is_rejected(self):
        r = self.client.post("/budget", data={"amount": "5"})
        self.assertEqual(r.status_code, 400)

    def test_user_cannot_delete_someone_elses_expense(self):
        cat = self.add_category("Food", 5000)
        self.add_expense_row(cat, 100, "2026-11-01")
        eid = self.sql("SELECT id FROM expenses")[0]["id"]
        other = self.app.test_client()
        self.register_and_login(other, "someone")
        self.assertEqual(self.post(other, f"/expenses/{eid}/delete").status_code, 404)
        self.assertEqual(self.expense_count(), 1)

    def test_users_only_see_their_own_data(self):
        cat = self.add_category("Secret", 5000)
        self.add_expense_row(cat, 123, "2026-11-01")
        other = self.app.test_client()
        self.register_and_login(other, "someone")
        self.assertNotIn("Secret", other.get("/").get_data(as_text=True))

    def test_excel_report_has_three_sheets(self):
        self.post(self.client, "/budget", {"amount": "10000"})
        cat = self.add_category("Food", 5000)
        self.add_expense_row(cat, 250, "2026-11-03")
        r = self.client.get("/report.xlsx?month=2026-11")
        self.assertEqual(r.status_code, 200)
        sheets = pd.read_excel(io.BytesIO(r.data), sheet_name=None)
        self.assertEqual(list(sheets), ["Summary", "By category", "Expenses"])
        self.assertEqual(int(sheets["Expenses"]["Amount"].sum()), 250)

    def test_all_pages_load(self):
        self.post(self.client, "/budget", {"amount": "10000"})
        for url in ("/", "/expenses/add", "/expenses", "/limits", "/budget", "/savings"):
            self.assertEqual(self.client.get(url).status_code, 200, url)


if __name__ == "__main__":
    unittest.main()
