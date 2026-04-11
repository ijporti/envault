"""Template rendering for environment variable substitution."""

import re
from typing import Dict, Optional


class TemplateError(Exception):
    """Raised when template rendering fails."""


_PLACEHOLDER_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::([^}]*))?\}")


def render_template(template: str, variables: Dict[str, str], strict: bool = False) -> str:
    """Render a template string by substituting ${VAR} or ${VAR:default} placeholders.

    Args:
        template: The template string containing placeholders.
        variables: A mapping of variable names to their values.
        strict: If True, raise TemplateError for unresolved placeholders with no default.

    Returns:
        The rendered string with all resolvable placeholders replaced.

    Raises:
        TemplateError: If strict=True and a placeholder has no value and no default.
    """

    def _replace(match: re.Match) -> str:
        name = match.group(1)
        default: Optional[str] = match.group(2)
        if name in variables:
            return variables[name]
        if default is not None:
            return default
        if strict:
            raise TemplateError(
                f"Unresolved placeholder '${{{name}}}' — variable not found and no default provided."
            )
        return match.group(0)  # leave unchanged when not strict

    return _PLACEHOLDER_RE.sub(_replace, template)


def collect_placeholders(template: str) -> list[str]:
    """Return a sorted list of unique variable names referenced in a template."""
    return sorted({m.group(1) for m in _PLACEHOLDER_RE.finditer(template)})


def render_all(
    templates: Dict[str, str],
    variables: Dict[str, str],
    strict: bool = False,
) -> Dict[str, str]:
    """Render every value in a dict of templates, returning a new dict."""
    return {key: render_template(value, variables, strict=strict) for key, value in templates.items()}
