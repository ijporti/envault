"""Tests for envault.template."""

import pytest
from envault.template import (
    TemplateError,
    collect_placeholders,
    render_all,
    render_template,
)


VARS = {"HOST": "localhost", "PORT": "5432", "USER": "admin"}


def test_render_simple_substitution():
    result = render_template("${HOST}:${PORT}", VARS)
    assert result == "localhost:5432"


def test_render_with_default_used():
    result = render_template("${MISSING:fallback}", {})
    assert result == "fallback"


def test_render_with_default_ignored_when_var_present():
    result = render_template("${HOST:default_host}", VARS)
    assert result == "localhost"


def test_render_empty_default():
    result = render_template("prefix_${MISSING:}_suffix", {})
    assert result == "prefix__suffix"


def test_render_unresolved_left_intact_when_not_strict():
    result = render_template("${UNKNOWN}", {}, strict=False)
    assert result == "${UNKNOWN}"


def test_render_strict_raises_on_missing_var():
    with pytest.raises(TemplateError, match="UNKNOWN"):
        render_template("${UNKNOWN}", {}, strict=True)


def test_render_strict_does_not_raise_when_default_provided():
    result = render_template("${UNKNOWN:safe}", {}, strict=True)
    assert result == "safe"


def test_render_no_placeholders_returns_original():
    text = "no placeholders here"
    assert render_template(text, VARS) == text


def test_render_multiple_same_placeholder():
    result = render_template("${HOST}/${HOST}", VARS)
    assert result == "localhost/localhost"


def test_collect_placeholders_returns_sorted_unique():
    template = "${PORT} ${HOST} ${PORT} ${USER}"
    names = collect_placeholders(template)
    assert names == ["HOST", "PORT", "USER"]


def test_collect_placeholders_empty_template():
    assert collect_placeholders("no vars") == []


def test_render_all_applies_to_all_values():
    templates = {
        "DB_URL": "postgres://${USER}@${HOST}:${PORT}/mydb",
        "LABEL": "server-${HOST}",
    }
    result = render_all(templates, VARS)
    assert result["DB_URL"] == "postgres://admin@localhost:5432/mydb"
    assert result["LABEL"] == "server-localhost"


def test_render_all_strict_propagates_error():
    templates = {"KEY": "${MISSING}"}
    with pytest.raises(TemplateError):
        render_all(templates, {}, strict=True)
