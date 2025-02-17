import contextlib
from pathlib import Path
from textwrap import dedent
from unittest.mock import Mock, patch

import lkml
import pytest
from click import ClickException
from click.testing import CliRunner
from google.cloud import bigquery
from google.cloud.bigquery.schema import SchemaField
from mozilla_schema_generator.probes import GleanProbe

from generator.explores import ClientCountsExplore
from generator.lookml import _lookml
from generator.views import ClientCountsView, GrowthAccountingView

from .utils import print_and_test


@pytest.fixture
def runner():
    return CliRunner()


class MockGleanPing:
    @staticmethod
    def get_repos():
        return [{"name": "glean-app-release"}]


class MockClient:
    """Mock bigquery.Client."""

    def get_table(self, table_ref):
        """Mock bigquery.Client.get_table."""

        if table_ref == "mozdata.custom.baseline":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField("client_id", "STRING"),
                    SchemaField("country", "STRING"),
                    SchemaField(
                        "document_id",
                        "STRING",
                        description="The document ID specified in the URI when the client sent this message",
                    ),
                ],
            )
        if table_ref == "mozdata.glean_app.baseline_clients_daily":
            return bigquery.Table(
                table_ref,
                schema=[
                    bigquery.schema.SchemaField("client_id", "STRING"),
                    bigquery.schema.SchemaField("submission_date", "DATE"),
                    bigquery.schema.SchemaField("country", "STRING"),
                    bigquery.schema.SchemaField("document_id", "STRING"),
                ],
            )
        if table_ref == "mozdata.glean_app.baseline_clients_last_seen":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField("client_id", "STRING"),
                    SchemaField("country", "STRING"),
                    SchemaField("document_id", "STRING"),
                ],
            )
        if table_ref == "mozdata.glean_app.baseline":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField(
                        "client_info",
                        "RECORD",
                        fields=[
                            SchemaField("client_id", "STRING"),
                            SchemaField("parsed_first_run_date", "DATE"),
                        ],
                    ),
                    SchemaField(
                        "metadata",
                        "RECORD",
                        fields=[
                            SchemaField(
                                "geo",
                                "RECORD",
                                fields=[
                                    SchemaField("country", "STRING"),
                                ],
                            ),
                            SchemaField(
                                "header",
                                "RECORD",
                                fields=[
                                    SchemaField("date", "STRING"),
                                    SchemaField("parsed_date", "TIMESTAMP"),
                                ],
                            ),
                        ],
                    ),
                    SchemaField(
                        "metrics",
                        "RECORD",
                        fields=[
                            SchemaField(
                                "counter",
                                "RECORD",
                                fields=[SchemaField("test_counter", "INTEGER")],
                            )
                        ],
                    ),
                    SchemaField("parsed_timestamp", "TIMESTAMP"),
                    SchemaField("submission_timestamp", "TIMESTAMP"),
                    SchemaField("submission_date", "DATE"),
                    SchemaField("test_bignumeric", "BIGNUMERIC"),
                    SchemaField("test_bool", "BOOLEAN"),
                    SchemaField("test_bytes", "BYTES"),
                    SchemaField("test_float64", "FLOAT"),
                    SchemaField("test_int64", "INTEGER"),
                    SchemaField("test_numeric", "NUMERIC"),
                    SchemaField("test_string", "STRING"),
                    SchemaField("additional_properties", "STRING"),
                ],
            )
        if table_ref == "mozdata.glean_app.metrics":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField(
                        "client_info",
                        "RECORD",
                        fields=[
                            SchemaField("client_id", "STRING"),
                        ],
                    ),
                    SchemaField(
                        "metrics",
                        "RECORD",
                        fields=[
                            SchemaField(
                                "boolean",
                                "RECORD",
                                fields=[
                                    SchemaField("test_boolean", "BOOLEAN"),
                                ],
                            ),
                            SchemaField(
                                "boolean",
                                "RECORD",
                                fields=[
                                    SchemaField(
                                        "test_boolean_not_in_source", "BOOLEAN"
                                    ),
                                ],
                            ),
                            SchemaField(
                                "counter",
                                "RECORD",
                                fields=[
                                    SchemaField("test_counter", "INTEGER"),
                                    SchemaField(
                                        "glean_validation_metrics_ping_count", "INTEGER"
                                    ),
                                    SchemaField("no_category_counter", "INTEGER"),
                                ],
                            ),
                            SchemaField(
                                "labeled_counter",
                                "RECORD",
                                "REPEATED",
                                fields=[
                                    SchemaField("key", "STRING"),
                                    SchemaField("value", "INTEGER"),
                                ],
                            ),
                            SchemaField(
                                "labeled_counter_not_in_source",
                                "RECORD",
                                "REPEATED",
                                fields=[
                                    SchemaField("key", "STRING"),
                                    SchemaField("value", "INTEGER"),
                                ],
                            ),
                            SchemaField(
                                "custom_distribution",
                                "RECORD",
                                fields=[
                                    SchemaField(
                                        "test_custom_distribution",
                                        "RECORD",
                                        "NULLABLE",
                                        None,
                                        (
                                            SchemaField(
                                                "sum",
                                                "INTEGER",
                                                "NULLABLE",
                                                None,
                                                (),
                                                None,
                                            ),
                                            SchemaField(
                                                "values",
                                                "RECORD",
                                                "REPEATED",
                                                None,
                                                (
                                                    SchemaField(
                                                        "key",
                                                        "STRING",
                                                        "NULLABLE",
                                                        None,
                                                        (),
                                                        None,
                                                    ),
                                                    SchemaField(
                                                        "value",
                                                        "INTEGER",
                                                        "NULLABLE",
                                                        None,
                                                        (),
                                                        None,
                                                    ),
                                                ),
                                                None,
                                            ),
                                        ),
                                        None,
                                    )
                                ],
                            ),
                            SchemaField(
                                "datetime",
                                "RECORD",
                                fields=[SchemaField("test_datetime", "STRING")],
                            ),
                            SchemaField(
                                "jwe",
                                "RECORD",
                                fields=[SchemaField("test_jwe", "STRING")],
                            ),
                            SchemaField(
                                "memory_distribution",
                                "RECORD",
                                fields=[
                                    SchemaField(
                                        "test_memory_distribution",
                                        "RECORD",
                                        "NULLABLE",
                                        None,
                                        (
                                            SchemaField(
                                                "sum",
                                                "INTEGER",
                                                "NULLABLE",
                                                None,
                                                (),
                                                None,
                                            ),
                                            SchemaField(
                                                "values",
                                                "RECORD",
                                                "REPEATED",
                                                None,
                                                (
                                                    SchemaField(
                                                        "key",
                                                        "STRING",
                                                        "NULLABLE",
                                                        None,
                                                        (),
                                                        None,
                                                    ),
                                                    SchemaField(
                                                        "value",
                                                        "INTEGER",
                                                        "NULLABLE",
                                                        None,
                                                        (),
                                                        None,
                                                    ),
                                                ),
                                                None,
                                            ),
                                        ),
                                        None,
                                    )
                                ],
                            ),
                            SchemaField(
                                "quantity",
                                "RECORD",
                                fields=[SchemaField("test_quantity", "INTEGER")],
                            ),
                            SchemaField(
                                "string",
                                "RECORD",
                                fields=[SchemaField("test_string", "STRING")],
                            ),
                            SchemaField(
                                "timing_distribution",
                                "RECORD",
                                fields=[
                                    SchemaField(
                                        "test_timing_distribution",
                                        "RECORD",
                                        "NULLABLE",
                                        None,
                                        (
                                            SchemaField(
                                                "sum",
                                                "INTEGER",
                                                "NULLABLE",
                                                None,
                                                (),
                                                None,
                                            ),
                                            SchemaField(
                                                "values",
                                                "RECORD",
                                                "REPEATED",
                                                None,
                                                (
                                                    SchemaField(
                                                        "key",
                                                        "STRING",
                                                        "NULLABLE",
                                                        None,
                                                        (),
                                                        None,
                                                    ),
                                                    SchemaField(
                                                        "value",
                                                        "INTEGER",
                                                        "NULLABLE",
                                                        None,
                                                        (),
                                                        None,
                                                    ),
                                                ),
                                                None,
                                            ),
                                        ),
                                        None,
                                    )
                                ],
                            ),
                            SchemaField(
                                "rate",
                                "RECORD",
                                fields=[
                                    SchemaField(
                                        "test_rate",
                                        "RECORD",
                                        fields=[
                                            SchemaField("denominator", "INTEGER"),
                                            SchemaField("numerator", "INTEGER"),
                                        ],
                                    )
                                ],
                            ),
                            SchemaField(
                                "timespan",
                                "RECORD",
                                fields=[
                                    SchemaField(
                                        "test_timespan",
                                        "RECORD",
                                        "NULLABLE",
                                        None,
                                        (
                                            SchemaField(
                                                "time_unit",
                                                "STRING",
                                                "NULLABLE",
                                                None,
                                                (),
                                                None,
                                            ),
                                            SchemaField(
                                                "value",
                                                "INTEGER",
                                                "NULLABLE",
                                                None,
                                                (),
                                                None,
                                            ),
                                        ),
                                        None,
                                    )
                                ],
                            ),
                            SchemaField(
                                "uuid",
                                "RECORD",
                                fields=[SchemaField("test_uuid", "STRING")],
                            ),
                        ],
                    ),
                ],
            )
        if table_ref == "mozdata.fail.duplicate_dimension":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField("parsed_timestamp", "TIMESTAMP"),
                    SchemaField("parsed_date", "DATE"),
                ],
            )
        if table_ref == "mozdata.fail.duplicate_client":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField(
                        "client_info",
                        "RECORD",
                        fields=[
                            SchemaField("client_id", "STRING"),
                        ],
                    ),
                    SchemaField("client_id", "STRING"),
                ],
            )
        if table_ref == "mozdata.custom.context":
            return bigquery.Table(
                table_ref, schema=[SchemaField("context_id", "STRING")]
            )
        if table_ref == "mozdata.glean_app.events_daily":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField("client_id", "STRING"),
                    SchemaField("submission_date", "DATE"),
                    SchemaField("country", "STRING"),
                    SchemaField("events", "STRING"),
                ],
            )
        if table_ref == "mozdata.glean_app.event_types":
            return bigquery.Table(
                table_ref,
                schema=[
                    SchemaField("category", "STRING"),
                    SchemaField("event", "STRING"),
                    SchemaField("index", "STRING"),
                ],
            )
        raise ValueError(f"Table not found: {table_ref}")


@pytest.fixture
def msg_glean_probes():
    history = [
        {"dates": {"first": "2020-01-01 00:00:00", "last": "2020-01-02 00:00:00"}}
    ]

    history_with_descr = [
        {
            "dates": {"first": "2020-01-01 00:00:00", "last": "2020-01-02 00:00:00"},
            "description": "test counter description",
        }
    ]

    return [
        GleanProbe(
            "test.boolean",
            {
                "type": "boolean",
                "history": history,
                "name": "test.boolean",
                "in-source": True,
            },
        ),
        GleanProbe(  # This probe should be ignored as a dupe
            "test.boolean",
            {
                "type": "boolean",
                "history": history,
                "name": "test.boolean",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.boolean_not_in_source",
            {
                "type": "boolean",
                "history": history,
                "name": "test.boolean_not_in_source",
                "in-source": False,
            },
        ),
        GleanProbe(
            "test.counter",
            {
                "type": "counter",
                "history": history_with_descr,
                "name": "test.counter",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.labeled_counter",
            {
                "type": "labeled_counter",
                "history": history_with_descr,
                "name": "test.labeled_counter",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.labeled_counter_not_in_source",
            {
                "type": "labeled_counter",
                "history": history_with_descr,
                "name": "test.labeled_counter_not_in_source",
                "in-source": False,
            },
        ),
        GleanProbe(
            "no_category_counter",
            {
                "type": "counter",
                "history": history,
                "name": "no_category_counter",
                "in-source": True,
            },
        ),
        GleanProbe(
            "glean.validation.metrics_ping_count",
            {
                "type": "counter",
                "history": history,
                "name": "glean.validation.metrics_ping_count",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.custom_distribution",
            {
                "type": "custom_distribution",
                "history": history,
                "name": "test.custom_distribution",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.datetime",
            {
                "type": "datetime",
                "history": history,
                "name": "test.datetime",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.jwe",
            {"type": "jwe", "history": history, "name": "test.jwe", "in-source": True},
        ),
        GleanProbe(
            "test.memory_distribution",
            {
                "type": "memory_distribution",
                "history": history,
                "name": "test.memory_distribution",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.quantity",
            {
                "type": "quantity",
                "history": history,
                "name": "test.quantity",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.string",
            {
                "type": "string",
                "history": history,
                "name": "test.string",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.timing_distribution",
            {
                "type": "timing_distribution",
                "history": history,
                "name": "test.timing_distribution",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.rate",
            {
                "type": "rate",
                "history": history,
                "name": "test.rate",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.timespan",
            {
                "type": "timespan",
                "history": history,
                "name": "test.timespan",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.uuid",
            {
                "type": "uuid",
                "history": history,
                "name": "test.uuid",
                "in-source": True,
            },
        ),
        GleanProbe(
            "test.missing_from_bq",
            {
                "type": "counter",
                "history": history,
                "name": "test.missing_from_bq",
                "in-source": True,
            },
        ),
    ]


@contextlib.contextmanager
def _prepare_lookml_actual_test(
    mock_glean_ping_view,
    mock_glean_ping_explore,
    runner,
    glean_apps,
    tmp_path,
    msg_glean_probes,
):
    namespaces = tmp_path / "namespaces.yaml"
    namespaces_text = dedent(
        """
            custom:
              pretty_name: Custom
              glean_app: false
              views:
                baseline:
                  type: ping_view
                  tables:
                  - channel: release
                    table: mozdata.custom.baseline
            glean-app:
              pretty_name: Glean App
              glean_app: true
              views:
                baseline_clients_daily_table:
                  type: table_view
                  tables:
                  - channel: release
                    table: mozdata.glean_app.baseline_clients_daily
                  - channel: beta
                    table: mozdata.glean_app_beta.baseline_clients_daily
                baseline:
                  type: glean_ping_view
                  tables:
                  - channel: release
                    table: mozdata.glean_app.baseline
                  - channel: beta
                    table: mozdata.glean_app_beta.baseline
                metrics:
                  type: glean_ping_view
                  tables:
                  - channel: release
                    table: mozdata.glean_app.metrics
                growth_accounting:
                  type: growth_accounting_view
                  tables:
                  - table: mozdata.glean_app.baseline_clients_last_seen
                client_counts:
                  type: client_counts_view
                  tables:
                  - table: mozdata.glean_app.baseline_clients_daily
              explores:
                baseline:
                  type: glean_ping_explore
                  views:
                    base_view: baseline
                growth_accounting:
                  type: growth_accounting_explore
                  views:
                    base_view: growth_accounting
                client_counts:
                  type: client_counts_explore
                  views:
                    extended_view: baseline_clients_daily_table
                    base_view: client_counts
            """
    )
    namespaces.write_text(namespaces_text)
    for mock in [mock_glean_ping_view, mock_glean_ping_explore]:
        mock.get_repos.return_value = [{"name": "glean-app-release"}]
        glean_app = Mock()
        glean_app.get_probes.return_value = msg_glean_probes
        glean_app.get_ping_descriptions.return_value = {
            "baseline": "The baseline ping\n    is foo."
        }
        mock.return_value = glean_app

    with runner.isolated_filesystem():
        with patch("google.cloud.bigquery.Client", MockClient):
            _lookml(open(namespaces), glean_apps, "looker-hub/")
            yield namespaces_text


@patch("generator.views.glean_ping_view.GleanPing")
@patch("generator.explores.glean_ping_explore.GleanPing")
def test_lookml_actual_baseline_view(
    mock_glean_ping_view,
    mock_glean_ping_explore,
    runner,
    glean_apps,
    tmp_path,
    msg_glean_probes,
):
    with _prepare_lookml_actual_test(
        mock_glean_ping_view,
        mock_glean_ping_explore,
        runner,
        glean_apps,
        tmp_path,
        msg_glean_probes,
    ) as namespaces_text:
        expected = {
            "views": [
                {
                    "name": "baseline",
                    "sql_table_name": "`mozdata.custom.baseline`",
                    "dimensions": [
                        {
                            "name": "client_id",
                            "hidden": "yes",
                            "sql": "${TABLE}.client_id",
                        },
                        {
                            "name": "country",
                            "map_layer_name": "countries",
                            "sql": "${TABLE}.country",
                            "type": "string",
                        },
                        {
                            "name": "document_id",
                            "hidden": "yes",
                            "sql": "${TABLE}.document_id",
                            "primary_key": "yes",
                            "description": "The document ID specified in the URI when the client sent this message",
                        },
                    ],
                    "measures": [
                        {
                            "name": "clients",
                            "type": "count_distinct",
                            "sql": "${client_id}",
                        },
                        {
                            "name": "ping_count",
                            "type": "count",
                        },
                    ],
                }
            ]
        }
        print_and_test(
            expected,
            lkml.load(Path("looker-hub/custom/views/baseline.view.lkml").read_text()),
        )
        print_and_test(namespaces_text, open(Path("looker-hub/namespaces.yaml")).read())


@patch("generator.views.glean_ping_view.GleanPing")
@patch("generator.explores.glean_ping_explore.GleanPing")
def test_lookml_actual_baseline_view_parameterized(
    mock_glean_ping_view,
    mock_glean_ping_explore,
    runner,
    glean_apps,
    tmp_path,
    msg_glean_probes,
):
    with _prepare_lookml_actual_test(
        mock_glean_ping_view,
        mock_glean_ping_explore,
        runner,
        glean_apps,
        tmp_path,
        msg_glean_probes,
    ):
        expected = {
            "views": [
                {
                    "name": "baseline",
                    "parameters": [
                        {
                            "name": "channel",
                            "type": "unquoted",
                            "default_value": "mozdata.glean_app.baseline",
                            "allowed_values": [
                                {
                                    "label": "Release",
                                    "value": "mozdata.glean_app.baseline",
                                },
                                {
                                    "label": "Beta",
                                    "value": "mozdata.glean_app_beta.baseline",
                                },
                            ],
                        }
                    ],
                    "sql_table_name": "`{% parameter channel %}`",
                    "dimensions": [
                        {
                            "name": "additional_properties",
                            "hidden": "yes",
                            "sql": "${TABLE}.additional_properties",
                        },
                        {
                            "name": "client_info__client_id",
                            "hidden": "yes",
                            "sql": "${TABLE}.client_info.client_id",
                        },
                        {
                            "name": "metadata__geo__country",
                            "map_layer_name": "countries",
                            "group_item_label": "Country",
                            "group_label": "Metadata Geo",
                            "sql": "${TABLE}.metadata.geo.country",
                            "type": "string",
                        },
                        {
                            "name": "metadata__header__date",
                            "group_item_label": "Date",
                            "group_label": "Metadata Header",
                            "sql": "${TABLE}.metadata.header.date",
                            "type": "string",
                        },
                        {
                            "name": "test_bignumeric",
                            "sql": "${TABLE}.test_bignumeric",
                            "type": "string",
                        },
                        {
                            "name": "test_bool",
                            "sql": "${TABLE}.test_bool",
                            "type": "yesno",
                        },
                        {
                            "name": "test_bytes",
                            "sql": "${TABLE}.test_bytes",
                            "type": "string",
                        },
                        {
                            "name": "test_float64",
                            "sql": "${TABLE}.test_float64",
                            "type": "number",
                        },
                        {
                            "name": "test_int64",
                            "sql": "${TABLE}.test_int64",
                            "type": "number",
                        },
                        {
                            "name": "test_numeric",
                            "sql": "${TABLE}.test_numeric",
                            "type": "number",
                        },
                        {
                            "name": "test_string",
                            "sql": "${TABLE}.test_string",
                            "type": "string",
                        },
                    ],
                    "dimension_groups": [
                        {
                            "name": "client_info__parsed_first_run",
                            "convert_tz": "no",
                            "datatype": "date",
                            "label": "Client Info: Parsed First Run Date",
                            "sql": "${TABLE}.client_info.parsed_first_run_date",
                            "timeframes": [
                                "raw",
                                "date",
                                "week",
                                "month",
                                "quarter",
                                "year",
                            ],
                            "type": "time",
                        },
                        {
                            "name": "metadata__header__parsed",
                            "label": "Metadata Header: Parsed Date",
                            "sql": "${TABLE}.metadata.header.parsed_date",
                            "timeframes": [
                                "raw",
                                "time",
                                "date",
                                "week",
                                "month",
                                "quarter",
                                "year",
                            ],
                            "type": "time",
                        },
                        {
                            "name": "parsed",
                            "sql": "${TABLE}.parsed_timestamp",
                            "timeframes": [
                                "raw",
                                "time",
                                "date",
                                "week",
                                "month",
                                "quarter",
                                "year",
                            ],
                            "type": "time",
                        },
                        {
                            "name": "submission",
                            "sql": "${TABLE}.submission_timestamp",
                            "timeframes": [
                                "raw",
                                "time",
                                "date",
                                "week",
                                "month",
                                "quarter",
                                "year",
                            ],
                            "type": "time",
                        },
                    ],
                    "measures": [
                        {
                            "name": "clients",
                            "type": "count_distinct",
                            "sql": "${client_info__client_id}",
                        },
                    ],
                }
            ]
        }

        print_and_test(
            expected,
            lkml.load(
                Path("looker-hub/glean-app/views/baseline.view.lkml").read_text()
            ),
        )


@patch("generator.views.glean_ping_view.GleanPing")
@patch("generator.explores.glean_ping_explore.GleanPing")
def test_lookml_actual_metrics_view(
    mock_glean_ping_view,
    mock_glean_ping_explore,
    runner,
    glean_apps,
    tmp_path,
    msg_glean_probes,
):
    with _prepare_lookml_actual_test(
        mock_glean_ping_view,
        mock_glean_ping_explore,
        runner,
        glean_apps,
        tmp_path,
        msg_glean_probes,
    ):
        expected = {
            "views": [
                {
                    "name": "metrics",
                    "sql_table_name": "`mozdata.glean_app.metrics`",
                    "dimensions": [
                        {
                            "group_item_label": "Boolean",
                            "group_label": "Test",
                            "name": "metrics__boolean__test_boolean",
                            "label": "Test Boolean",
                            "sql": "${TABLE}.metrics.boolean.test_boolean",
                            "type": "yesno",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Boolean",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_boolean",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Boolean Not In Source",
                            "group_label": "Test",
                            "name": "metrics__boolean__test_boolean_not_in_source",
                            "label": "Test Boolean Not In Source",
                            "sql": "${TABLE}.metrics.boolean.test_boolean_not_in_source",
                            "type": "yesno",
                            "hidden": "yes",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Boolean Not In Source",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_boolean_not_in_source",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Counter",
                            "group_label": "Test",
                            "name": "metrics__counter__test_counter",
                            "label": "Test Counter",
                            "description": "test counter description",
                            "sql": "${TABLE}.metrics.counter.test_counter",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Counter",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_counter",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "No Category Counter",
                            "group_label": "Glean",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",
                                    "label": "Glean Dictionary "
                                    "reference for Glean No "
                                    "Category Counter",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/no_category_counter",  # noqa: 501
                                }
                            ],
                            "name": "metrics__counter__no_category_counter",
                            "label": "Glean No Category Counter",
                            "sql": "${TABLE}.metrics.counter.no_category_counter",
                            "type": "number",
                        },
                        {
                            "group_item_label": "Metrics Ping Count",
                            "group_label": "Glean Validation",
                            "name": "metrics__counter__glean_validation_metrics_ping_count",
                            "label": "Glean Validation Metrics Ping Count",
                            "sql": "${TABLE}.metrics.counter.glean_validation_metrics_ping_count",  # noqa: E501
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Glean Validation Metrics Ping Count",  # noqa: E501
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/glean_validation_metrics_ping_count",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Custom Distribution Sum",
                            "group_label": "Test",
                            "name": "metrics__custom_distribution__test_custom_distribution__sum",
                            "label": "Test Custom Distribution Sum",
                            "sql": "${TABLE}.metrics.custom_distribution.test_custom_distribution.sum",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Custom Distribution Sum",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_custom_distribution",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Datetime",
                            "group_label": "Test",
                            "name": "metrics__datetime__test_datetime",
                            "label": "Test Datetime",
                            "sql": "${TABLE}.metrics.datetime.test_datetime",
                            "type": "string",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Datetime",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_datetime",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Jwe",
                            "group_label": "Test",
                            "name": "metrics__jwe__test_jwe",
                            "label": "Test Jwe",
                            "sql": "${TABLE}.metrics.jwe.test_jwe",
                            "type": "string",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Jwe",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_jwe",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Memory Distribution Sum",
                            "group_label": "Test",
                            "name": "metrics__memory_distribution__test_memory_distribution__sum",
                            "label": "Test Memory Distribution Sum",
                            "sql": "${TABLE}.metrics.memory_distribution.test_memory_distribution.sum",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Memory Distribution Sum",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_memory_distribution",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Quantity",
                            "group_label": "Test",
                            "name": "metrics__quantity__test_quantity",
                            "label": "Test Quantity",
                            "sql": "${TABLE}.metrics.quantity.test_quantity",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Quantity",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_quantity",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "String",
                            "group_label": "Test",
                            "name": "metrics__string__test_string",
                            "label": "Test String",
                            "sql": "${TABLE}.metrics.string.test_string",
                            "type": "string",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test String",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_string",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Timing Distribution Sum",
                            "group_label": "Test",
                            "name": "metrics__timing_distribution__test_timing_distribution__sum",
                            "label": "Test Timing Distribution Sum",
                            "sql": "${TABLE}.metrics.timing_distribution.test_timing_distribution.sum",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Timing Distribution Sum",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_timing_distribution",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Rate Numerator",
                            "group_label": "Test",
                            "name": "metrics__rate__test_rate__numerator",
                            "label": "Test Rate Numerator",
                            "sql": "${TABLE}.metrics.rate.test_rate.numerator",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Rate Numerator",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_rate",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Rate Denominator",
                            "group_label": "Test",
                            "name": "metrics__rate__test_rate__denominator",
                            "label": "Test Rate Denominator",
                            "sql": "${TABLE}.metrics.rate.test_rate.denominator",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Rate Denominator",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_rate",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Timespan Value",
                            "group_label": "Test",
                            "name": "metrics__timespan__test_timespan__value",
                            "label": "Test Timespan Value",
                            "sql": "${TABLE}.metrics.timespan.test_timespan.value",
                            "type": "number",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Timespan Value",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_timespan",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "group_item_label": "Uuid",
                            "group_label": "Test",
                            "name": "metrics__uuid__test_uuid",
                            "label": "Test Uuid",
                            "sql": "${TABLE}.metrics.uuid.test_uuid",
                            "type": "string",
                            "hidden": "no",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary reference for Test Uuid",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_uuid",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "hidden": "yes",
                            "name": "client_info__client_id",
                            "sql": "${TABLE}.client_info.client_id",
                        },
                    ],
                    "measures": [
                        {
                            "name": "clients",
                            "sql": "${client_info__client_id}",
                            "type": "count_distinct",
                        },
                        {
                            "name": "test_counter",
                            "type": "sum",
                            "sql": "${metrics__counter__test_counter}",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary "
                                    "reference for Test "
                                    "Counter",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_counter",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "name": "test_counter_client_count",
                            "type": "count_distinct",
                            "filters__all": [
                                [{"metrics__counter__test_counter": ">0"}]
                            ],
                            "sql": "${client_info__client_id}",
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary "
                                    "reference for Test "
                                    "Counter",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/test_counter",  # noqa: E501
                                }
                            ],
                        },
                        {
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",
                                    "label": "Glean Dictionary "
                                    "reference for No "
                                    "Category Counter",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/no_category_counter",  # noqa: 501
                                }
                            ],
                            "name": "no_category_counter",
                            "sql": "${metrics__counter__no_category_counter}",
                            "type": "sum",
                        },
                        {
                            "filters__all": [
                                [{"metrics__counter__no_category_counter": ">0"}]
                            ],
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",
                                    "label": "Glean Dictionary "
                                    "reference for No "
                                    "Category Counter",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/no_category_counter",  # noqa: 501
                                }
                            ],
                            "name": "no_category_counter_client_count",
                            "sql": "${client_info__client_id}",
                            "type": "count_distinct",
                        },
                        {
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary "
                                    "reference for Glean Validation Metrics Ping Count",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/glean_validation_metrics_ping_count",  # noqa: E501
                                }
                            ],
                            "name": "glean_validation_metrics_ping_count",
                            "sql": "${metrics__counter__glean_validation_metrics_ping_count}",  # noqa: E501
                            "type": "sum",
                        },
                        {
                            "links": [
                                {
                                    "icon_url": "https://dictionary.telemetry.mozilla.org/favicon.png",  # noqa: E501
                                    "label": "Glean Dictionary "
                                    "reference for Glean Validation Metrics Ping Count",
                                    "url": "https://dictionary.telemetry.mozilla.org/apps/glean-app/metrics/glean_validation_metrics_ping_count",  # noqa: E501
                                }
                            ],
                            "name": "glean_validation_metrics_ping_count_client_count",
                            "filters__all": [
                                [
                                    {
                                        "metrics__counter__glean_validation_metrics_ping_count": ">0"
                                    }
                                ]
                            ],
                            "sql": "${client_info__client_id}",
                            "type": "count_distinct",
                        },
                    ],
                },
                {
                    "dimensions": [
                        {
                            "hidden": "yes",
                            "name": "document_id",
                            "sql": "${metrics.document_id}",
                            "type": "string",
                        },
                        {
                            "hidden": "yes",
                            "name": "document_label_id",
                            "primary_key": "yes",
                            "sql": "${metrics.document_id}-${label}",
                            "type": "string",
                        },
                        {
                            "name": "label",
                            "hidden": "no",
                            "sql": "${TABLE}.key",
                            "suggest_dimension": "suggest__metrics__metrics__labeled_counter__test_labeled_counter.key",
                            "suggest_explore": "suggest__metrics__metrics__labeled_counter__test_labeled_counter",
                            "type": "string",
                        },
                        {
                            "hidden": "yes",
                            "name": "value",
                            "sql": "${TABLE}.value",
                            "type": "number",
                        },
                    ],
                    "label": "Test - Labeled Counter",
                    "measures": [
                        {
                            "name": "count",
                            "sql": "${value}",
                            "type": "sum",
                            "hidden": "no",
                        },
                        {
                            "name": "client_count",
                            "sql": "case when ${value} > 0 then "
                            "${metrics.client_info__client_id} end",
                            "type": "count_distinct",
                            "hidden": "no",
                        },
                    ],
                    "name": "metrics__metrics__labeled_counter__test_labeled_counter",
                },
                {
                    "dimensions": [
                        {
                            "hidden": "yes",
                            "name": "document_id",
                            "sql": "${metrics.document_id}",
                            "type": "string",
                        },
                        {
                            "hidden": "yes",
                            "name": "document_label_id",
                            "primary_key": "yes",
                            "sql": "${metrics.document_id}-${label}",
                            "type": "string",
                        },
                        {
                            "name": "label",
                            "hidden": "yes",
                            "sql": "${TABLE}.key",
                            "suggest_dimension": "suggest__metrics__metrics__labeled_counter__test_labeled_counter_not_in_source.key",  # noqa: E501
                            "suggest_explore": "suggest__metrics__metrics__labeled_counter__test_labeled_counter_not_in_source",  # noqa: E501
                            "type": "string",
                        },
                        {
                            "hidden": "yes",
                            "name": "value",
                            "sql": "${TABLE}.value",
                            "type": "number",
                        },
                    ],
                    "label": "Test - Labeled Counter Not In Source",
                    "measures": [
                        {
                            "name": "count",
                            "sql": "${value}",
                            "type": "sum",
                            "hidden": "yes",
                        },
                        {
                            "name": "client_count",
                            "sql": "case when ${value} > 0 then "
                            "${metrics.client_info__client_id} end",
                            "type": "count_distinct",
                            "hidden": "yes",
                        },
                    ],
                    "name": "metrics__metrics__labeled_counter__test_labeled_counter_not_in_source",
                },
                {
                    "derived_table": {
                        "sql": "select\n"
                        "    m.key,\n"
                        "    count(*) as n\n"
                        "from mozdata.glean_app.metrics as "
                        "t,\n"
                        "unnest(metrics.labeled_counter.test_labeled_counter) as m\n"
                        "where date(submission_timestamp) > date_sub(current_date, interval 30 day)\n"
                        "    and sample_id = 0\n"
                        "group by key\n"
                        "order by n desc"
                    },
                    "dimensions": [
                        {"name": "key", "sql": "${TABLE}.key", "type": "string"}
                    ],
                    "name": "suggest__metrics__metrics__labeled_counter__test_labeled_counter",
                },
                {
                    "derived_table": {
                        "sql": "select\n"
                        "    m.key,\n"
                        "    count(*) as n\n"
                        "from mozdata.glean_app.metrics as "
                        "t,\n"
                        "unnest(metrics.labeled_counter.test_labeled_counter_not_in_source) as m\n"
                        "where date(submission_timestamp) > date_sub(current_date, interval 30 day)\n"
                        "    and sample_id = 0\n"
                        "group by key\n"
                        "order by n desc"
                    },
                    "dimensions": [
                        {"name": "key", "sql": "${TABLE}.key", "type": "string"}
                    ],
                    "name": "suggest__metrics__metrics__labeled_counter__test_labeled_counter_not_in_source",
                },
            ]
        }
        print_and_test(
            expected,
            lkml.load(Path("looker-hub/glean-app/views/metrics.view.lkml").read_text()),
        )


@patch("generator.views.glean_ping_view.GleanPing")
@patch("generator.explores.glean_ping_explore.GleanPing")
def test_lookml_actual_growth_accounting_view(
    mock_glean_ping_view,
    mock_glean_ping_explore,
    runner,
    glean_apps,
    tmp_path,
    msg_glean_probes,
):
    with _prepare_lookml_actual_test(
        mock_glean_ping_view,
        mock_glean_ping_explore,
        runner,
        glean_apps,
        tmp_path,
        msg_glean_probes,
    ):
        expected = {
            "views": [
                {
                    "name": "growth_accounting",
                    "sql_table_name": "`mozdata.glean_app.baseline_clients_last_seen`",
                    "dimensions": [
                        {
                            "name": "client_id",
                            "hidden": "yes",
                            "sql": "${TABLE}.client_id",
                        },
                        {
                            "name": "country",
                            "map_layer_name": "countries",
                            "sql": "${TABLE}.country",
                            "type": "string",
                        },
                        {
                            "name": "document_id",
                            "hidden": "yes",
                            "sql": "${TABLE}.document_id",
                        },
                    ]
                    + GrowthAccountingView.default_dimensions,
                    "measures": GrowthAccountingView.default_measures,
                }
            ]
        }

        # lkml changes the format of lookml, so we need to cycle it through to match
        print_and_test(
            lkml.load(lkml.dump(expected)),
            lkml.load(
                Path(
                    "looker-hub/glean-app/views/growth_accounting.view.lkml"
                ).read_text()
            ),
        )


@patch("generator.views.glean_ping_view.GleanPing")
@patch("generator.explores.glean_ping_explore.GleanPing")
def test_lookml_actual_baseline_explore(
    mock_glean_ping_view,
    mock_glean_ping_explore,
    runner,
    glean_apps,
    tmp_path,
    msg_glean_probes,
):
    with _prepare_lookml_actual_test(
        mock_glean_ping_view,
        mock_glean_ping_explore,
        runner,
        glean_apps,
        tmp_path,
        msg_glean_probes,
    ):
        expected = {
            "includes": ["/looker-hub/glean-app/views/baseline.view.lkml"],
            "explores": [
                {
                    "name": "baseline",
                    "description": "Explore for the baseline ping. The baseline ping is foo.",
                    "view_name": "baseline",
                    "view_label": " Baseline",
                    "always_filter": {
                        "filters": [
                            {"channel": "mozdata.glean^_app.baseline"},
                            {"submission_date": "28 days"},
                        ]
                    },
                    "sql_always_where": "${baseline.submission_date} >= '2010-01-01'",
                }
            ],
        }
        print_and_test(
            lkml.load(lkml.dump(expected)),
            lkml.load(
                Path("looker-hub/glean-app/explores/baseline.explore.lkml").read_text()
            ),
        )


@patch("generator.views.glean_ping_view.GleanPing")
@patch("generator.explores.glean_ping_explore.GleanPing")
def test_lookml_actual_client_counts(
    mock_glean_ping_view,
    mock_glean_ping_explore,
    runner,
    glean_apps,
    tmp_path,
    msg_glean_probes,
):
    with _prepare_lookml_actual_test(
        mock_glean_ping_view,
        mock_glean_ping_explore,
        runner,
        glean_apps,
        tmp_path,
        msg_glean_probes,
    ):
        expected = {
            "includes": ["baseline_clients_daily_table.view.lkml"],
            "views": [
                {
                    "extends": ["baseline_clients_daily_table"],
                    "name": "client_counts",
                    "dimensions": ClientCountsView.default_dimensions,
                    "dimension_groups": ClientCountsView.default_dimension_groups,
                    "measures": ClientCountsView.default_measures,
                }
            ],
        }

        print_and_test(
            lkml.load(lkml.dump(expected)),
            lkml.load(
                Path("looker-hub/glean-app/views/client_counts.view.lkml").read_text()
            ),
        )

        expected = {
            "includes": ["/looker-hub/glean-app/views/client_counts.view.lkml"],
            "explores": [
                {
                    "name": "client_counts",
                    "view_name": "client_counts",
                    "description": "Client counts across dimensions and cohorts.",
                    "always_filter": {
                        "filters__all": [
                            [
                                {
                                    "channel": "mozdata.glean^_app.baseline^_clients^_daily"
                                },
                                {"submission_date": "28 days"},
                            ],
                        ],
                    },
                    "queries": ClientCountsExplore.queries,
                    "sql_always_where": "${client_counts.submission_date} >= '2010-01-01'",
                }
            ],
        }

        print_and_test(
            lkml.load(lkml.dump(expected)),
            lkml.load(
                Path(
                    "looker-hub/glean-app/explores/client_counts.explore.lkml"
                ).read_text()
            ),
        )


def test_duplicate_dimension(runner, glean_apps, tmp_path):
    namespaces = tmp_path / "namespaces.yaml"
    namespaces.write_text(
        dedent(
            """
            custom:
              pretty_name: Custom
              glean_app: false
              views:
                baseline:
                  type: ping_view
                  tables:
                  - channel: release
                    table: mozdata.fail.duplicate_dimension
            """
        )
    )
    with runner.isolated_filesystem():
        with patch("google.cloud.bigquery.Client", MockClient):
            with pytest.raises(ClickException):
                _lookml(open(namespaces), glean_apps, "looker-hub/")


def test_duplicate_client_id(runner, glean_apps, tmp_path):
    namespaces = tmp_path / "namespaces.yaml"
    namespaces.write_text(
        dedent(
            """
            custom:
              pretty_name: Custom
              glean_app: false
              views:
                baseline:
                  type: ping_view
                  tables:
                  - channel: release
                    table: mozdata.fail.duplicate_client
            """
        )
    )
    with runner.isolated_filesystem():
        with patch("google.cloud.bigquery.Client", MockClient):
            with pytest.raises(ClickException):
                _lookml(open(namespaces), glean_apps, "looker-hub/")


def test_context_id(runner, glean_apps, tmp_path):
    namespaces = tmp_path / "namespaces.yaml"
    namespaces.write_text(
        dedent(
            """
            custom:
              pretty_name: Custom
              glean_app: false
              views:
                context:
                  type: ping_view
                  tables:
                  - channel: release
                    table: mozdata.custom.context
            """
        )
    )

    with runner.isolated_filesystem():
        with patch("google.cloud.bigquery.Client", MockClient):
            _lookml(open(namespaces), glean_apps, "looker-hub/")
        expected = {
            "views": [
                {
                    "sql_table_name": "`mozdata.custom.context`",
                    "name": "context",
                    "dimensions": [
                        {
                            "name": "context_id",
                            "hidden": "yes",
                            "sql": "${TABLE}.context_id",
                        }
                    ],
                    "measures": [
                        {
                            "name": "clients",
                            "type": "count_distinct",
                            "sql": "${context_id}",
                        }
                    ],
                }
            ],
        }

        print_and_test(
            lkml.load(lkml.dump(expected)),
            lkml.load(Path("looker-hub/custom/views/context.view.lkml").read_text()),
        )
