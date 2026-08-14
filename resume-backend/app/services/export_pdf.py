from __future__ import annotations

from html import escape
import os
from pathlib import Path

from app.schemas.resume import ResumePayload


class PdfRendererUnavailableError(Exception):
    pass


def chromium_is_available(browser_root: str) -> bool:
    root = Path(browser_root)
    return root.is_dir() and any(root.rglob("chrome.exe"))


async def render_pdf_resume(
    resume: ResumePayload,
    template_id: str,
    output_path: Path,
    renderer: str,
    browser_root: str,
    watermark_text: str | None = None,
) -> None:
    html = render_resume_html(resume, template_id, watermark_text)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if renderer == "playwright":
        await _render_with_playwright(html, output_path, browser_root)
        return
    if renderer == "weasyprint":
        _render_with_weasyprint(html, output_path)
        return
    raise PdfRendererUnavailableError(f"Unsupported PDF renderer: {renderer}")


def render_resume_html(
    resume: ResumePayload, template_id: str, watermark_text: str | None = None
) -> str:
    template_root = Path(__file__).resolve().parents[1] / "templates" / "html"
    base_html = (template_root / "base.html").read_text(encoding="utf-8")
    theme_styles = (template_root / f"{template_id}.html").read_text(encoding="utf-8")
    content = _render_content(resume)
    if watermark_text:
        content += f'<p style="margin-top: 24px; color: #7a8494; font-size: 10px; text-align: center;">{escape(watermark_text)}</p>'
    return base_html.replace("{{ theme_styles }}", theme_styles).replace("{{ content }}", content)


def _render_content(resume: ResumePayload) -> str:
    contact = " | ".join(
        escape(value) for value in [resume.basic.phone, resume.basic.email, resume.basic.city] if value
    )
    sections: list[str] = []
    if resume.section_visibility.basic:
        sections.append(
            f'<section class="header"><h1>{escape(resume.basic.name)}</h1>'
            f'<div class="contact">{contact}</div></section>'
        )
    if resume.section_visibility.job:
        sections.append(_section("求职意向", [escape(resume.job.target_role)]))
    if resume.section_visibility.education:
        sections.append(
            _section(
                "教育经历",
                [
                    _entry(
                        f"{item.school} | {item.major} | {item.degree}",
                        f"{item.start_date} - {item.end_date}",
                    )
                    for item in resume.education
                ],
            )
        )
    if resume.section_visibility.employment:
        sections.append(
            _section(
                "实习/工作经历",
                [
                    _entry(
                        f"{item.company} | {item.position}",
                        f"{item.start_date} - {item.end_date}",
                        item.description,
                    )
                    for item in resume.employment
                ],
            )
        )
    if resume.section_visibility.projects:
        sections.append(
            _section(
                "项目经历",
                [
                    _entry(
                        f"{item.name} | {item.role}",
                        f"{item.start_date} - {item.end_date}",
                        item.description,
                    )
                    for item in resume.projects
                ],
            )
        )
    if resume.section_visibility.skills:
        sections.append(_section("技能证书", [escape(", ".join(resume.skills.skills + resume.skills.certificates))]))
    if resume.section_visibility.self_evaluation:
        sections.append(_section("自我评价", [escape(resume.self_evaluation)]))
    return "\n".join(section for section in sections if section)


def _section(title: str, entries: list[str]) -> str:
    content = "\n".join(entry for entry in entries if entry)
    return f"<section><h2>{escape(title)}</h2>{content}</section>" if content else ""


def _entry(title: str, meta: str, description: str = "") -> str:
    return (
        '<div class="entry">'
        f'<div class="entry-title">{escape(title)}</div>'
        f'<div class="meta">{escape(meta)}</div>'
        f'<div>{escape(description)}</div>'
        "</div>"
    )


async def _render_with_playwright(html: str, output_path: Path, browser_root: str) -> None:
    if not chromium_is_available(browser_root):
        raise PdfRendererUnavailableError("Chromium is not installed for the configured Playwright browser path")
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = browser_root
    try:
        from playwright.async_api import async_playwright
    except ImportError as error:
        raise PdfRendererUnavailableError("Playwright is not installed") from error

    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                await page.set_content(html)
                await page.pdf(path=str(output_path), format="A4", print_background=True)
            finally:
                await browser.close()
    except PdfRendererUnavailableError:
        raise
    except Exception as error:
        raise PdfRendererUnavailableError("Playwright could not render the PDF") from error


def _render_with_weasyprint(html: str, output_path: Path) -> None:
    try:
        from weasyprint import HTML
    except ImportError as error:
        raise PdfRendererUnavailableError("WeasyPrint is not installed") from error
    HTML(string=html).write_pdf(output_path)
