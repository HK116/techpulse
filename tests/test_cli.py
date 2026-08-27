"""
Tests for techpulse.cli.

We test argument parsing directly and patch run_pipeline so no real
network/LLM calls happen when `main()` executes.
"""

from unittest.mock import patch

from techpulse.cli import build_arg_parser, main


def test_arg_parser_defaults():
    args = build_arg_parser().parse_args([])
    assert args.limit == 20
    assert args.db == "techpulse.db"
    assert args.verbose is False


def test_arg_parser_custom_values():
    args = build_arg_parser().parse_args(["--limit", "5", "--db", "custom.db", "--verbose"])
    assert args.limit == 5
    assert args.db == "custom.db"
    assert args.verbose is True


@patch("techpulse.cli.run_pipeline")
def test_main_calls_run_pipeline_with_parsed_args(mock_run_pipeline):
    mock_run_pipeline.return_value = 7
    exit_code = main(["--limit", "10", "--db", "test.db"])
    assert exit_code == 0
    mock_run_pipeline.assert_called_once_with(limit=10, db_path="test.db")