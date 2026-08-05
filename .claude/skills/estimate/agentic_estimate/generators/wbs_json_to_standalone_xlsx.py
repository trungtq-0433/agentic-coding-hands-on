"""WBS data to standalone Excel workbook generator."""

from pathlib import Path


def render(data: dict, output_path, config: dict | None = None) -> None:
    """Render WBS data to standalone XLSX workbook.

    Accepts two input formats:
    - Estimate JSON: tasks in data["options"][0]["categories"][n]["tasks"]
    - Breakdown JSON: tasks in data["epics"][n]["stories"][n]["tasks"]

    Args:
        data: Estimate or breakdown JSON data
        output_path: Path to write XLSX file
        config: Optional configuration (not used)
    """
    from openpyxl import Workbook

    from .wbs_xlsx_sheet_builders import create_per_role_sheets, create_summary_sheet

    data_format = _detect_format(data)
    active_roles, role_names = _get_roles_for_format(data, data_format)
    wbs_data = _extract_wbs_data(data, data_format, active_roles)

    wb = Workbook()
    wb.remove(wb.active)

    create_summary_sheet(wb, wbs_data, active_roles, role_names)
    create_per_role_sheets(wb, wbs_data, active_roles, role_names)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(str(output_path))


def _detect_format(data: dict) -> str:
    if "epics" in data:
        return "breakdown"
    if "options" in data:
        return "estimate"
    raise ValueError("Unrecognized data format: missing 'epics' or 'options'")


def _get_roles_for_format(data: dict, data_format: str) -> tuple[list, dict]:
    if data_format == "breakdown":
        return data.get("active_roles", []), data.get("role_names", {})
    from .estimate_render_helpers import get_roles

    return get_roles(data)


def _extract_wbs_data(data: dict, data_format: str, active_roles: list) -> list:
    wbs_data = []

    if data_format == "estimate":
        option = data.get("options", [{}])[0]
        categories = option.get("categories", [])

        for category in categories:
            category_name = category.get("name", "Unknown")
            tasks = category.get("tasks", [])

            for task in tasks:
                wbs_data.append(
                    {
                        "category": category_name,
                        "id": task.get("id", ""),
                        "name": task.get("name", ""),
                        "effort": task.get("effort", {}),
                        "total_md": task.get("total_md", 0),
                        "story_points": task.get("story_points", 0),
                        "notes": task.get("notes", ""),
                    }
                )
    else:
        epics = data.get("epics", [])

        for epic in epics:
            epic_name = epic.get("name", "Unknown")
            stories = epic.get("stories", [])

            for story in stories:
                tasks = story.get("tasks", [])

                for task in tasks:
                    role = task.get("role", "")
                    md = task.get("md", 0) or 0

                    effort = {role: {"md": md}} if role else {}

                    wbs_data.append(
                        {
                            "category": epic_name,
                            "id": task.get("id", ""),
                            "name": task.get("name", ""),
                            "effort": effort,
                            "total_md": md,
                            "story_points": 0,
                            "notes": "",
                        }
                    )

    return wbs_data
