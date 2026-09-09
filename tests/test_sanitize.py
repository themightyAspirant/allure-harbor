from app.core.sanitize import sanitize_name, sanitize_project


def test_sanitize_project_slug() -> None:
    assert sanitize_project("Checkout Suite") == "checkout-suite"
    assert sanitize_project(None) == "default"
    assert sanitize_project("@@@") == "default"
    assert sanitize_project("A" * 80) == ("a" * 64)


def test_sanitize_name() -> None:
    assert sanitize_name("  nightly  ") == "nightly"
    assert sanitize_name("   ") is None
    assert sanitize_name(None) is None
    assert len(sanitize_name("n" * 300) or "") == 255
