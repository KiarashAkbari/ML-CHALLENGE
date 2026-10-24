import unittest

from data_factory.contract import ReasonCode
from data_factory.validate import validate_record

BASE = {
    "unique_key": "1",
    "created_date": "2025-01-03T00:57:07.000",
    "closed_date": "2025-01-03T01:30:00.000",
    "agency": "NYPD",
    "complaint_type": "Noise - Residential",
    "descriptor": "Loud Music/Party",
    "status": "Closed",
    "borough": "BRONX",
    "incident_zip": "10466",
    "community_board": "12 BRONX",
}


def make_row(**overrides):
    return {**BASE, **overrides}


class ValidateRecordTests(unittest.TestCase):
    def test_valid_row_passes(self):
        self.assertEqual(validate_record(BASE), ())

    def test_absent_required_field(self):
        row = make_row()
        del row["complaint_type"]
        self.assertEqual(validate_record(row), (ReasonCode.MISSING_REQUIRED_FIELD,))

    def test_blank_required_field_counts_as_missing(self):
        row = make_row(descriptor="   ")
        self.assertEqual(validate_record(row), (ReasonCode.MISSING_REQUIRED_FIELD,))

    def test_missing_unique_key(self):
        row = make_row(unique_key=None)
        self.assertEqual(validate_record(row), (ReasonCode.MISSING_REQUIRED_FIELD,))

    def test_missing_zip_is_allowed(self):
        self.assertEqual(validate_record(make_row(incident_zip=None)), ())

    def test_bad_zip_formats(self):
        for bad in ("N/A", "1046", "104666", " 10466", "00000"):
            with self.subTest(zip=bad):
                row = make_row(incident_zip=bad)
                self.assertEqual(validate_record(row), (ReasonCode.BAD_ZIP_FORMAT,))

    def test_zip_starting_with_zeros_but_not_all_zeros_is_valid(self):
        self.assertEqual(validate_record(make_row(incident_zip="00083")), ())

    def test_unparseable_created_date(self):
        row = make_row(created_date="03/01/2025")
        self.assertEqual(validate_record(row), (ReasonCode.UNPARSEABLE_DATE,))

    def test_missing_created_date(self):
        row = make_row(created_date=None)
        self.assertEqual(validate_record(row), (ReasonCode.MISSING_REQUIRED_FIELD,))

    def test_closed_before_created(self):
        row = make_row(
            created_date="2025-01-03T01:00:00.000",
            closed_date="2025-01-03T00:59:55.000",
        )
        self.assertEqual(validate_record(row), (ReasonCode.CLOSED_BEFORE_CREATED,))

    def test_closed_equal_to_created_is_valid(self):
        row = make_row(closed_date=BASE["created_date"])
        self.assertEqual(validate_record(row), ())

    def test_closed_status_without_closed_date(self):
        row = make_row(closed_date=None)
        self.assertEqual(
            validate_record(row), (ReasonCode.CLOSED_WITHOUT_CLOSED_DATE,)
        )

    def test_open_status_without_closed_date_is_valid(self):
        row = make_row(status="Open", closed_date=None)
        self.assertEqual(validate_record(row), ())

    def test_unparseable_closed_date_skips_ordering_check(self):
        row = make_row(closed_date="garbage")
        self.assertEqual(validate_record(row), (ReasonCode.UNPARSEABLE_DATE,))

    def test_borough_out_of_domain(self):
        row = make_row(borough="ATLANTIS")
        self.assertEqual(validate_record(row), (ReasonCode.VALUE_OUT_OF_DOMAIN,))

    def test_unspecified_borough_is_valid(self):
        self.assertEqual(validate_record(make_row(borough="Unspecified")), ())

    def test_multiple_violations_are_deduplicated_and_ordered(self):
        row = make_row(
            complaint_type=None, descriptor=None, borough="ATLANTIS", incident_zip="N/A"
        )
        self.assertEqual(
            validate_record(row),
            (
                ReasonCode.MISSING_REQUIRED_FIELD,
                ReasonCode.VALUE_OUT_OF_DOMAIN,
                ReasonCode.BAD_ZIP_FORMAT,
            ),
        )