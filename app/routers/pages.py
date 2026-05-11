"""Server-rendered template page routes (everything except `/`).

The home page route stays in `app.main` because it carries the existing
simulator's full slider-bound context. All other pages render
self-contained Jinja2 templates that extend `base.html`.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.constants import VACCINATION_COVERAGE_MAX
from app.templates_shared import templates

router = APIRouter()


@router.get("/about")
async def about_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "about.html", {"active_page": "about"})


@router.get("/scenarios")
async def scenarios_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "scenarios.html", {"active_page": "scenarios"}
    )


@router.get("/history")
async def history_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "history.html", {"active_page": "history"}
    )


@router.get("/sensitivity")
async def sensitivity_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "sensitivity.html", {"active_page": "sensitivity"}
    )


@router.get("/vaccination")
async def vaccination_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "vaccination.html",
        {
            "active_page": "vaccination",
            "vaccination_coverage_max": VACCINATION_COVERAGE_MAX,
        },
    )


@router.get("/glossary")
async def glossary_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "glossary.html", {"active_page": "glossary"}
    )


@router.get("/author")
async def author_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "author.html", {"active_page": "author"})


@router.get("/credits")
async def credits_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "credits.html", {"active_page": "credits"}
    )


@router.get("/roadmap")
async def roadmap_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "roadmap.html", {"active_page": "roadmap"}
    )
