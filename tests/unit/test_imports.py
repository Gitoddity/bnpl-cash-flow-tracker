def test_package_imports():
    import bnpl_cashflow
    import bnpl_cashflow.domain
    import bnpl_cashflow.reporting
    import bnpl_cashflow.rules

    assert bnpl_cashflow.__all__ == ["domain", "rules", "reporting"]
    assert bnpl_cashflow.domain is not None
    assert bnpl_cashflow.reporting is not None
    assert bnpl_cashflow.rules is not None
