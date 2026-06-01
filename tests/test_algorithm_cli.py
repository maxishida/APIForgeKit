from run_algorithm_lab import build_parser


def test_algorithm_cli_parser_supports_suite_and_export_flags():
    parser = build_parser()
    args = parser.parse_args(["--suite", "lead_score", "--export"])

    assert args.suite == "lead_score"
    assert args.export is True
