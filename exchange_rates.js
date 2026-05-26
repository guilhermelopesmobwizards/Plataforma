"""
core/tests.py

Test suite for MAP Control — End of Month Platform.

Run with:
    python manage.py test core.tests
"""

import io
from datetime import date
from decimal import Decimal

import openpyxl
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client as TestClient
from django.test import TestCase

from core import models
from core.export.excel_export import generate_monthly_excel


# ── Helpers ───────────────────────────────────────────────────────────────────

HEADERS = [
    "Month", "Client", "Country", "Categoria", "Creativity", "Platform",
    "Plat. owner", "Client Camp.", "CPA", "ER cpa", "ER cost", "Cost TS",
    "Conv", "Cost €", "Revenue €", "Margin €", "ROI",
    "TS Manager", "TS Head", "Client Manager", "Client Head",
    "FE", "BE", "Criativo", "QA", "PM", "Detalhe",
    "conv cliente", "rev cliente", "var conv", "var rev",
    "var conv %", "var rev %", "ok/not ok conv", "ok/not ok rev",
    "Invoice google",
]

HEADER_ROW_INDEX = 4  # row 5 in Excel (0-based)


def _make_upload(rows: list[list]) -> SimpleUploadedFile:
    """Build a minimal .xlsx matching the import format and wrap as Django upload."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Register2026"
    for _ in range(HEADER_ROW_INDEX):
        ws.append([None] * len(rows[0]))
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile(
        "test.xlsx",
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _row(**overrides) -> list:
    """Return a data row aligned with HEADERS, with sensible defaults."""
    defaults = {
        "Month": date(2026, 2, 1),
        "Client": "DTY",
        "Country": "AE",
        "Categoria": "downloads",
        "Creativity": "StreamPlay",
        "Platform": "Google",
        "Plat. owner": "Mob",
        "Client Camp.": "NO",
        "CPA": 4.11,
        "ER cpa": 0.86,
        "ER cost": 0.04,
        "Cost TS": 71029.95,
        "Conv": 995,
        "Cost €": 2931.0,
        "Revenue €": 3510.6,
        "Margin €": 579.6,
        "ROI": 0.198,
        "TS Manager": "MEC",
        "TS Head": "MEC",
        "Client Manager": "MS",
        "Client Head": "MS",
        "FE": "N/A",
        "BE": "N/A",
        "Criativo": "MEC",
        "QA": "N/A",
        "PM": "N/A",
        "Detalhe": "CPA",
        "conv cliente": 995,
        "rev cliente": 4058.25,
        "var conv": 0,
        "var rev": 0,
        "var conv %": 0,
        "var rev %": 0,
        "ok/not ok conv": "ok",
        "ok/not ok rev": "ok",
        "Invoice google": 5427783081,
    }
    defaults.update(overrides)
    return [defaults[h] for h in HEADERS]


# ── Campaign model tests ──────────────────────────────────────────────────────

class CampaignModelTest(TestCase):
    """Basic model creation, fields, and constraints."""

    def setUp(self):
        self.month = models.Month.objects.create(
            month_date=date(2026, 2, 1), label="Feb 2026"
        )
        self.client_obj = models.Client.objects.create(code="TST", name="Test Client")
        self.country = models.Country.objects.create(iso_code="PT", name="Portugal")
        self.category = models.Category.objects.create(name="downloads")
        self.creative = models.Creative.objects.create(name="StreamPlay")

    def test_campaign_creation(self):
        campaign = models.Campaign.objects.create(
            month=self.month,
            client=self.client_obj,
            country=self.country,
        )
        self.assertIsNotNone(campaign.pk)
        # __str__ shows client name
        self.assertIn("Test Client", str(campaign))

    def test_campaign_has_timestamps(self):
        """TimestampedModel fields must be auto-populated on save."""
        campaign = models.Campaign.objects.create(
            month=self.month,
            client=self.client_obj,
            country=self.country,
        )
        self.assertIsNotNone(campaign.created_at)
        self.assertIsNotNone(campaign.updated_at)

    def test_campaign_unique_constraint(self):
        """Duplicate (month, client, country, category, creative) must raise IntegrityError."""
        from django.db import IntegrityError

        models.Campaign.objects.create(
            month=self.month,
            client=self.client_obj,
            country=self.country,
            category=self.category,
            creative=self.creative,
        )
        with self.assertRaises(IntegrityError):
            models.Campaign.objects.create(
                month=self.month,
                client=self.client_obj,
                country=self.country,
                category=self.category,
                creative=self.creative,
            )

    def test_metric_decimal_precision(self):
        """Metric monetary fields use Decimal — no float rounding errors."""
        campaign = models.Campaign.objects.create(
            month=self.month, client=self.client_obj, country=self.country,
        )
        metric = models.Metric.objects.create(
            campaign=campaign,
            cost_eur=Decimal("1234.5678"),
            revenue_eur=Decimal("9876.1234"),
        )
        metric.refresh_from_db()
        self.assertIsInstance(metric.cost_eur, Decimal)
        self.assertEqual(metric.cost_eur, Decimal("1234.5678"))

    def test_worker_model_exists_team_does_not(self):
        """
        Regression: models.Worker must exist; models.Team must not.
        Before the fix, models.Team was referenced in excel_import.py.
        """
        self.assertTrue(hasattr(models, "Worker"))
        self.assertFalse(hasattr(models, "Team"))
        worker = models.Worker.objects.create(ts_manager="MEC", ts_head="MEC")
        self.assertIsNotNone(worker.pk)

    def test_campaign_worker_field_not_team(self):
        """
        Regression: Campaign FK field is 'worker', not 'team'.
        Before the fix, campaign_defaults used key 'team' → TypeError.
        """
        worker = models.Worker.objects.create(ts_manager="MEC", ts_head="MEC")
        campaign = models.Campaign.objects.create(
            month=self.month,
            client=self.client_obj,
            country=self.country,
            worker=worker,
        )
        campaign.refresh_from_db()
        self.assertEqual(campaign.worker_id, worker.pk)
        self.assertFalse(
            hasattr(campaign, "team"),
            "Campaign must not have a 'team' attribute",
        )

    def test_all_dimension_models_have_timestamps(self):
        """Every model that inherits TimestampedModel must have created_at/updated_at."""
        timestamped_models = [
            models.Month, models.Client, models.Country, models.Category,
            models.Creative, models.Platform, models.PlatOwner, models.DetailType,
            models.Worker, models.Campaign, models.Metric, models.Comparison,
        ]
        for model_class in timestamped_models:
            with self.subTest(model=model_class.__name__):
                self.assertTrue(
                    hasattr(model_class, "created_at"),
                    f"{model_class.__name__} missing created_at",
                )
                self.assertTrue(
                    hasattr(model_class, "updated_at"),
                    f"{model_class.__name__} missing updated_at",
                )


# ── Excel import tests ────────────────────────────────────────────────────────

class ExcelImportTest(TestCase):
    """Tests for POST /app/api/import/excel/."""

    IMPORT_URL = "/app/api/import/excel/"

    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.http = TestClient()
        self.http.force_login(self.user)

    def _post(self, upload: SimpleUploadedFile):
        return self.http.post(self.IMPORT_URL, {"file": upload})

    def test_happy_path_creates_campaign_metric_comparison(self):
        """Importing a valid row must create Campaign + Metric + Comparison."""
        response = self._post(_make_upload([HEADERS, _row()]))

        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["created"], 1)
        self.assertEqual(data["updated"], 0)
        self.assertEqual(len(data["errors"]), 0)

        campaign = models.Campaign.objects.select_related("client", "worker").first()
        self.assertIsNotNone(campaign)
        self.assertEqual(campaign.client.code, "DTY")
        self.assertIsNotNone(campaign.worker)

        metric = campaign.metric
        self.assertEqual(metric.conv, 995)
        self.assertAlmostEqual(float(metric.cost_eur), 2931.0, places=1)

        self.assertEqual(campaign.comparison.ok_conv, "ok")

    def test_duplicate_row_updates_not_creates(self):
        """Importing the same logical row twice must update, not create a new campaign."""
        self._post(_make_upload([HEADERS, _row()]))
        response = self._post(_make_upload([HEADERS, _row(**{"Cost €": 3500.0})]))

        data = response.json()
        self.assertEqual(data["created"], 0, f"Should update, not create: {data}")
        self.assertEqual(data["updated"], 1)
        self.assertEqual(models.Campaign.objects.count(), 1)
        self.assertAlmostEqual(float(models.Metric.objects.first().cost_eur), 3500.0, places=1)

    def test_no_file_returns_400(self):
        response = self.http.post(self.IMPORT_URL, {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_wrong_extension_returns_400(self):
        upload = SimpleUploadedFile("data.csv", b"a,b,c", content_type="text/csv")
        response = self._post(upload)
        self.assertEqual(response.status_code, 400)

    def test_worker_model_used_not_team(self):
        """
        Critical regression: the import must complete without AttributeError on models.Team.
        Before the fix, line 156 called models.Team.objects.get_or_create() → AttributeError.
        """
        response = self._post(_make_upload([HEADERS, _row()]))

        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(
            len(data["errors"]),
            0,
            f"models.Team regression? Errors: {data['errors']}",
        )
        # Worker record must have been created via models.Worker
        self.assertEqual(models.Worker.objects.count(), 1)

    def test_div_zero_and_special_values_handled(self):
        """#DIV/0!, -, and None values must not crash the import."""
        response = self._post(_make_upload([HEADERS, _row(**{
            "ROI": "#DIV/0!",
            "var conv %": "-",
            "var rev %": None,
            "Conv": None,
            "ok/not ok conv": "#DIV/0!",
        })]))

        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(len(data["errors"]), 0)

        metric = models.Metric.objects.first()
        self.assertIsNone(metric.roi)
        self.assertIsNone(metric.conv)
        # "#DIV/0!" → _imp_ok returns None (not a valid "ok"/"not ok")
        self.assertIsNone(models.Comparison.objects.first().ok_conv)

    def test_multiple_distinct_rows(self):
        """Three distinct campaigns must each be created separately."""
        rows = [
            HEADERS,
            _row(Country="AE", Creativity="StreamPlay", Client="DTY"),
            _row(Country="BG", Creativity="Dulcetty",   Client="VSB"),
            _row(Country="CY", Creativity="TopContent", Client="FST"),
        ]
        response = self._post(_make_upload(rows))
        data = response.json()
        self.assertEqual(data["created"], 3)
        self.assertEqual(models.Campaign.objects.count(), 3)

    def test_missing_month_row_is_caught_not_crash(self):
        """
        A row with no Month value (like 'Acerto invoice GG' rows) must be logged
        as an error for that row, not crash the whole import.
        """
        bad_row = [None] * len(HEADERS)  # Month = None → _imp_month raises ValueError
        bad_row[1] = "GG"

        response = self._post(_make_upload([HEADERS, _row(), bad_row]))

        self.assertEqual(response.status_code, 200, response.content)
        data = response.json()
        self.assertEqual(data["created"], 1)
        self.assertEqual(len(data["errors"]), 1)
        self.assertIn("Month", data["errors"][0]["error"])


# ── API endpoint tests ────────────────────────────────────────────────────────

class APIEndpointTest(TestCase):
    """Tests for the JSON read API (/app/api/*)."""

    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.http = TestClient()
        self.http.force_login(self.user)

        month = models.Month.objects.create(month_date=date(2026, 2, 1), label="Feb 2026")
        client_obj = models.Client.objects.create(code="DTY", name="DTY Client")
        country = models.Country.objects.create(iso_code="AE", name="UAE")
        platform = models.Platform.objects.create(name="Google")
        category = models.Category.objects.create(name="downloads")

        self.campaign = models.Campaign.objects.create(
            month=month, client=client_obj, country=country,
            platform=platform, category=category,
        )
        self.metric = models.Metric.objects.create(
            campaign=self.campaign,
            conv=995, cost_eur=Decimal("2931.00"),
            revenue_eur=Decimal("3510.60"), margin_eur=Decimal("579.60"),
            roi=Decimal("0.198"), cpa=Decimal("4.11"),
        )
        self.comparison = models.Comparison.objects.create(
            campaign=self.campaign,
            client_conv=995, client_rev=Decimal("4058.25"),
            ok_conv="ok", ok_rev="ok",
        )

    def test_campaigns_returns_results(self):
        response = self.http.get("/app/api/campaigns/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)
        result = data["results"][0]
        self.assertEqual(result["client"], "DTY Client")
        self.assertEqual(result["metric"]["conv"], 995)

    def test_campaigns_pagination_enforced(self):
        response = self.http.get("/app/api/campaigns/?page_size=1")
        data = response.json()
        self.assertLessEqual(len(data["results"]), 1)

    def test_campaigns_filter_by_nonexistent_client(self):
        response = self.http.get("/app/api/campaigns/?client=99999")
        self.assertEqual(response.json()["count"], 0)

    def test_dashboard_totals(self):
        response = self.http.get("/app/api/dashboard/")
        self.assertEqual(response.status_code, 200)
        totals = response.json()["totals"]
        self.assertEqual(totals["total_campaigns"], 1)
        self.assertAlmostEqual(totals["total_conv"], 995, delta=1)

    def test_metrics_endpoint(self):
        response = self.http.get("/app/api/metrics/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("totals", data)
        self.assertIn("by_platform", data)
        self.assertIn("by_month", data)

    def test_comparisons_endpoint(self):
        response = self.http.get("/app/api/comparisons/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("by_month", data)
        self.assertIn("by_client", data)
        self.assertIn("by_platform", data)

    def test_campaign_detail(self):
        response = self.http.get(f"/app/api/campaigns/{self.campaign.pk}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.campaign.pk)
        self.assertIsNotNone(data["metric"])
        self.assertIsNotNone(data["comparison"])


# ── Excel export tests ────────────────────────────────────────────────────────

class ExcelExportTest(TestCase):
    """Tests for generate_monthly_excel() and GET /app/api/export/excel/."""

    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@test.com", "pass")
        self.http = TestClient()
        self.http.force_login(self.user)

        month = models.Month.objects.create(month_date=date(2026, 2, 1), label="Feb 2026")
        client_obj = models.Client.objects.create(code="DTY", name="DTY Client")
        country = models.Country.objects.create(iso_code="AE", name="UAE")
        creative = models.Creative.objects.create(name="StreamPlay")

        self.campaign = models.Campaign.objects.create(
            month=month, client=client_obj, country=country, creative=creative,
        )
        models.Metric.objects.create(
            campaign=self.campaign,
            conv=995, cost_eur=Decimal("2931.00"),
            revenue_eur=Decimal("3510.60"), margin_eur=Decimal("579.60"),
            roi=Decimal("0.198"), cpa=Decimal("4.11"),
        )
        models.Comparison.objects.create(
            campaign=self.campaign, ok_conv="ok", ok_rev="ok",
        )

    def _load_ws(self, buf_or_response) -> openpyxl.worksheet.worksheet.Worksheet:
        content = buf_or_response if isinstance(buf_or_response, (bytes, bytearray)) \
                  else buf_or_response.content
        return openpyxl.load_workbook(io.BytesIO(content))["Register2026"]

    def test_returns_valid_xlsx_with_correct_sheet(self):
        buf = generate_monthly_excel()
        wb = openpyxl.load_workbook(buf)
        self.assertIn("Register2026", wb.sheetnames)

    def test_structure_headers_on_row_5(self):
        ws = self._load_ws(generate_monthly_excel().read())
        headers = [ws.cell(5, c).value for c in range(1, 6)]
        self.assertIn("Month", headers)
        self.assertIn("Client", headers)

    def test_data_on_row_6(self):
        ws = self._load_ws(generate_monthly_excel().read())
        client_col = next(
            c for c in range(1, ws.max_column + 1)
            if ws.cell(5, c).value == "Client"
        )
        self.assertEqual(ws.cell(6, client_col).value, "DTY")

    def test_month_filter_excludes_other_months(self):
        ws = self._load_ws(generate_monthly_excel(month_date="2025-01").read())
        client_col = next(
            c for c in range(1, ws.max_column + 1)
            if ws.cell(5, c).value == "Client"
        )
        self.assertNotEqual(ws.cell(6, client_col).value, "DTY")

    def test_month_filter_includes_matching(self):
        response = self.http.get("/app/api/export/excel/?month=2026-02")
        ws = self._load_ws(response)
        client_col = next(
            c for c in range(1, ws.max_column + 1)
            if ws.cell(5, c).value == "Client"
        )
        self.assertEqual(ws.cell(6, client_col).value, "DTY")

    def test_view_returns_xlsx_download(self):
        response = self.http.get("/app/api/export/excel/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("spreadsheetml", response["Content-Type"])
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(".xlsx", response["Content-Disposition"])

    def test_filename_contains_month_when_filtered(self):
        response = self.http.get("/app/api/export/excel/?month=2026-02")
        self.assertIn("2026_02", response["Content-Disposition"])

    def test_negative_margin_included_in_export(self):
        """Campaigns with negative margin must appear (red-coded) in the export."""
        month = models.Month.objects.get(month_date=date(2026, 2, 1))
        client_obj = models.Client.objects.get(code="DTY")
        country = models.Country.objects.get(iso_code="AE")
        creative2 = models.Creative.objects.create(name="BadDeal")

        campaign2 = models.Campaign.objects.create(
            month=month, client=client_obj, country=country, creative=creative2,
        )
        models.Metric.objects.create(
            campaign=campaign2,
            cost_eur=Decimal("5000.00"),
            revenue_eur=Decimal("3000.00"),
            margin_eur=Decimal("-2000.00"),
        )

        ws = self._load_ws(generate_monthly_excel(month_date="2026-02").read())
        margin_col = next(c for c in range(1, ws.max_column + 1) if ws.cell(5, c).value == "Margin €")
        margins = [ws.cell(r, margin_col).value for r in [6, 7] if ws.cell(r, margin_col).value is not None]
        self.assertIn(-2000.0, margins)

    def test_totals_row_present_when_data_exists(self):
        """A totals row must appear below the data rows."""
        ws = self._load_ws(generate_monthly_excel().read())
        last_row = ws.max_row
        self.assertEqual(ws.cell(last_row, 1).value, "TOTAL")

