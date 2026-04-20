"""Génération de rapports PDF avec WeasyPrint + Jinja2."""
import os

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "pdf")
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=True)


def _render(template_name: str, context: dict) -> bytes:
    tmpl = _env.get_template(template_name)
    html = tmpl.render(**context)
    return HTML(string=html).write_pdf()


def scan_pdf(scan: dict, vulnerabilities: list) -> bytes:
    return _render("scan_report.html", {"scan": scan, "vulnerabilities": vulnerabilities})


def mobile_scan_pdf(scan: dict) -> bytes:
    return _render("mobile_scan.html", {"scan": scan})


def incident_pdf(incident: dict) -> bytes:
    return _render("incident_report.html", {"incident": incident})


def forensic_report_pdf(report: dict) -> bytes:
    return _render("forensic_report.html", {"report": report})


def ebios_pdf(project: dict, assets: list, fear_events: list,
              risk_sources: list, scenarios: list) -> bytes:
    return _render("ebios_report.html", {
        "project": project,
        "assets": assets,
        "fear_events": fear_events,
        "risk_sources": risk_sources,
        "scenarios": scenarios,
    })


def architecture_pdf(content: str) -> bytes:
    """Génère un PDF à partir du markdown de l'architecture."""
    return _render("architecture.html", {"content": content})
