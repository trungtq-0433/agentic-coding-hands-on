"""PDF generator using HTML and WeasyPrint."""

from datetime import datetime

try:
    from weasyprint import CSS, HTML

    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from .generator_base_output_interface import BaseGenerator


class PDFGenerator(BaseGenerator):
    """Generates PDF documents via HTML rendering."""

    @property
    def file_extension(self) -> str:
        return "pdf"

    def generate(self, results: dict) -> str:
        """Generate PDF document."""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "weasyprint is required for PDF generation. Install with: pip install weasyprint"
            )

        html_content = self._generate_html(results)
        css_content = self._get_css()

        filename = self.get_filename()
        output_path = self.config.get_output_path(filename)

        HTML(string=html_content).write_pdf(
            output_path,
            stylesheets=[CSS(string=css_content)],
        )

        return str(output_path)

    def _generate_html(self, results: dict) -> str:
        """Generate HTML content for PDF."""
        project = results.get("project_name", "Project")
        estimate = results.get("estimate", {})
        requirements = results.get("requirements", [])
        risk_assessment = results.get("risk_assessment", {})
        validation = results.get("validation_report", {})

        html_parts = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'></head><body>",
            f"<h1>Project Estimate: {self._escape(project)}</h1>",
            f"<p class='meta'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>",
        ]

        # Executive Summary
        html_parts.extend(
            [
                "<h2>Executive Summary</h2>",
                "<table class='summary'>",
                "<tr><th>Metric</th><th>Value</th></tr>",
                f"<tr><td>Total Story Points</td><td>{estimate.get('total_story_points', 0)}</td></tr>",
                f"<tr><td>Total Man-Days</td><td>{estimate.get('total_man_days', 0)}</td></tr>",
                f"<tr><td>Buffer</td><td>{estimate.get('buffer_percentage', 20)}%</td></tr>",
                f"<tr><td>Confidence</td><td>{estimate.get('confidence_level', 'medium')}</td></tr>",
                f"<tr><td>Risk Level</td><td>{risk_assessment.get('overall_level', 'medium')}</td></tr>",
                f"<tr><td>Quality Score</td><td>{validation.get('quality_score', 'N/A')}/100</td></tr>",
                "</table>",
            ]
        )

        # Phases
        phases = estimate.get("phases", [])
        if phases:
            html_parts.extend(
                [
                    "<h2>Project Phases</h2>",
                    "<table>",
                    "<tr><th>Phase</th><th>Story Points</th><th>Man-Days</th></tr>",
                ]
            )
            for phase in phases:
                html_parts.append(
                    f"<tr><td>{self._escape(phase.get('name', ''))}</td>"
                    f"<td>{phase.get('story_points', 0)}</td>"
                    f"<td>{phase.get('man_days', 0)}</td></tr>"
                )
            html_parts.append("</table>")

        # Requirements (limited)
        if requirements:
            html_parts.extend(
                [
                    "<h2>Requirements Summary</h2>",
                    f"<p>Total: {len(requirements)} requirements</p>",
                    "<table>",
                    "<tr><th>ID</th><th>Title</th><th>Type</th><th>Complexity</th><th>SP</th></tr>",
                ]
            )
            for req in requirements[:20]:
                html_parts.append(
                    f"<tr><td>{self._escape(str(req.get('id', '')))}</td>"
                    f"<td>{self._escape(req.get('title', '')[:50])}</td>"
                    f"<td>{self._escape(req.get('type', ''))}</td>"
                    f"<td>{self._escape(req.get('complexity', ''))}</td>"
                    f"<td>{req.get('story_points', 0)}</td></tr>"
                )
            if len(requirements) > 20:
                html_parts.append(
                    f"<tr><td colspan='5'>... and {len(requirements) - 20} more</td></tr>"
                )
            html_parts.append("</table>")

        # Risks
        if self.config.include_risks and risk_assessment:
            risks = risk_assessment.get("risks", [])[:10]
            if risks:
                html_parts.extend(
                    [
                        "<h2>Risk Assessment</h2>",
                        f"<p>Overall Level: <strong>{risk_assessment.get('overall_level', 'medium')}</strong></p>",
                        "<table>",
                        "<tr><th>Risk</th><th>Impact</th><th>Score</th><th>Mitigation</th></tr>",
                    ]
                )
                for risk in risks:
                    mitigations = risk.get("mitigations", [])
                    mitigation = mitigations[0] if mitigations else ""
                    html_parts.append(
                        f"<tr><td>{self._escape(risk.get('type', '').replace('_', ' ').title())}</td>"
                        f"<td>{self._escape(risk.get('impact', ''))}</td>"
                        f"<td>{risk.get('score', 0)}</td>"
                        f"<td>{self._escape(mitigation)}</td></tr>"
                    )
                html_parts.append("</table>")

        # Validation
        if self.config.include_validation and validation:
            html_parts.extend(
                [
                    "<h2>Validation Report</h2>",
                    f"<p>Status: <strong>{validation.get('status', 'N/A')}</strong></p>",
                ]
            )

            issues = validation.get("issues", [])
            if issues:
                html_parts.append("<h3>Issues</h3><ul>")
                for issue in issues:
                    html_parts.append(
                        f"<li><strong>[{issue.get('severity', '').upper()}]</strong> "
                        f"{self._escape(issue.get('message', ''))}</li>"
                    )
                html_parts.append("</ul>")

            recommendations = validation.get("recommendations", [])
            if recommendations:
                html_parts.append("<h3>Recommendations</h3><ul>")
                for rec in recommendations:
                    html_parts.append(f"<li>{self._escape(rec.get('action', ''))}</li>")
                html_parts.append("</ul>")

        # Assumptions
        assumptions = estimate.get("assumptions", [])
        if assumptions:
            html_parts.extend(
                [
                    "<h2>Assumptions</h2>",
                    "<ul>",
                ]
            )
            for assumption in assumptions:
                html_parts.append(f"<li>{self._escape(assumption)}</li>")
            html_parts.append("</ul>")

        # Footer
        html_parts.extend(
            [
                "<footer>",
                f"<p>Generated by Agentic Estimate - {datetime.now().isoformat()}</p>",
                "</footer>",
                "</body></html>",
            ]
        )

        return "\n".join(html_parts)

    def _get_css(self) -> str:
        """Get CSS styles for PDF."""
        return """
        @page {
            size: A4;
            margin: 2cm;
        }

        body {
            font-family: 'Helvetica', 'Arial', sans-serif;
            font-size: 10pt;
            line-height: 1.4;
            color: #333;
        }

        h1 {
            color: #2c3e50;
            font-size: 20pt;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }

        h2 {
            color: #34495e;
            font-size: 14pt;
            margin-top: 25px;
            margin-bottom: 10px;
            border-bottom: 1px solid #bdc3c7;
            padding-bottom: 5px;
        }

        h3 {
            color: #7f8c8d;
            font-size: 12pt;
            margin-top: 15px;
        }

        .meta {
            color: #7f8c8d;
            font-size: 9pt;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            font-size: 9pt;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }

        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }

        tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        table.summary {
            width: 50%;
        }

        table.summary td:first-child {
            font-weight: bold;
            background-color: #ecf0f1;
        }

        ul {
            margin: 10px 0;
            padding-left: 25px;
        }

        li {
            margin: 5px 0;
        }

        footer {
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            font-size: 8pt;
            color: #95a5a6;
            text-align: center;
        }

        strong {
            color: #2c3e50;
        }
        """

    def _escape(self, text: str) -> str:
        """Escape HTML special characters."""
        if not isinstance(text, str):
            text = str(text)
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
