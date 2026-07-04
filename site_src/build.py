#!/usr/bin/env python3
"""Build the static website from structured source data.

Edit JSON files in site_src/data/, then run:

    python3 site_src/build.py
"""

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
DATA_DIR = SRC_DIR / "data"
TEMPLATE_DIR = SRC_DIR / "templates"
MONTH_NAMES = [
    "",
    "Jan.",
    "Feb.",
    "Mar.",
    "Apr.",
    "May",
    "Jun.",
    "Jul.",
    "Aug.",
    "Sep.",
    "Oct.",
    "Nov.",
    "Dec.",
]


def load_json(name: str) -> Any:
    with (DATA_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=False)


def attr(value: Any) -> str:
    return html.escape(str(value), quote=True)


def render_template(name: str, context: Dict[str, str]) -> str:
    template = (TEMPLATE_DIR / name).read_text(encoding="utf-8")
    for key, value in context.items():
        template = template.replace("{{" + key + "}}", value)

    unresolved = sorted(set(re.findall(r"{{([a-zA-Z0-9_]+)}}", template)))
    if unresolved:
        raise ValueError(f"Unresolved template placeholders in {name}: {', '.join(unresolved)}")

    return template


def render_nav_items(nav: Iterable[List[str]]) -> str:
    lines = []
    for label, target in nav:
        lines.append(
            f'            <li class="nav-item"><a class="nav-link" href="/#{attr(target)}" '
            f'data-target="#{attr(target)}"><span>{esc(label)}</span></a></li>'
        )
    return "\n".join(lines)


def render_social_links(social: Iterable[Dict[str, str]]) -> str:
    links = []
    for item in social:
        icon = item["icon"]
        if icon == "x-twitter":
            icon_html = (
                '<svg class="x-icon" viewBox="0 0 512 512" aria-hidden="true">'
                '<path d="M389.2 48h70.6L305.6 224.2 487 464H345L233.7 318.6 '
                '86.8 464H16.2l164.9-188.5L7 48h145.6l102.3 135.2L389.2 '
                '48zm-24.8 373.8h39.1L151.1 88h-42l255.3 333.8z"/>'
                "</svg>"
            )
        else:
            icon_html = f'<i class="fa {attr(icon)}" aria-hidden="true"></i>'

        links.append(
            "          <li>\n"
            f'            <a href="{attr(item["url"])}" target="_blank" rel="noopener" '
            f'aria-label="{attr(item["label"])}">\n'
            f"              {icon_html}\n"
            "            </a>\n"
            "          </li>"
        )
    return "\n".join(links)


def render_education(items: Iterable[Dict[str, str]]) -> str:
    rendered = []
    for item in items:
        institution = esc(item["institution"]).replace("Peking University", "Peking&nbsp;University")
        rendered.append(
            "            <li>\n"
            "              <i class=\"fa-li fas fa-graduation-cap\"></i>\n"
            "              <div class=\"description\">\n"
            f"                <p class=\"course\">{esc(item['course'])}</p>\n"
            f"                <p class=\"institution\">{institution}</p>\n"
            "              </div>\n"
            "            </li>"
        )
    return "\n".join(rendered)


def render_profile_name(name: str) -> str:
    match = re.match(r"^(.*?)(\s*\([^()]+\))$", name)
    if not match:
        return esc(name)

    latin_name, cjk_name = match.groups()
    return (
        f'<span class="profile-name-latin">{esc(latin_name)}</span>'
        f'<span class="profile-name-cjk">{esc(cjk_name)}</span>'
    )


def render_bio(profile: Dict[str, Any]) -> str:
    bio = profile["bio_html"]
    if isinstance(bio, str):
        paragraphs = [bio]
    else:
        paragraphs = bio
    return "\n".join(f"              <p>{paragraph}</p>" for paragraph in paragraphs)


def render_about(data: Dict[str, Any]) -> str:
    site = data["site"]
    profile = data["profile"]
    return f"""
    <section id="about" class="home-section wg-about">
      <div class="home-section-bg"></div>
      <div class="container">
        <div class="row">
          <div class="col-12 col-lg-4">
            <div id="profile">
              <img class="avatar avatar-circle" width="270" height="270"
                   src="{attr(site['avatar'])}" alt="{attr(profile['name'])}">
              <div class="portrait-title">
                <h2>{render_profile_name(profile['name'])}</h2>
                <h3>{esc(profile['role'])}</h3>
                <h3><a href="{attr(profile['affiliation_url'])}" target="_blank" rel="noopener"><span>{esc(profile['affiliation'])}</span></a></h3>
              </div>
              <ul class="network-icon" aria-hidden="true">
{render_social_links(data["social"])}
              </ul>
            </div>
          </div>
          <div class="col-12 col-lg-8">
            <div class="article-style">
{render_bio(profile)}
            </div>
            <div class="about-details">
              <div class="about-contact">
                <div class="section-subheading">Contact</div>
                {esc(profile['contact'])}
              </div>
              <div class="about-education">
                <div class="section-subheading">Education</div>
                <ul class="ul-edu fa-ul mb-0">
{render_education(data["education"])}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
"""


def render_link(link: Dict[str, str]) -> str:
    label = str(link["label"])
    href = attr(link["url"])
    if label.lower() == "arxiv":
        return (
            '<a class="btn btn-outline-primary btn-page-header btn-sm publication-link-icon" '
            f'href="{href}" target="_blank" rel="noopener" aria-label="arXiv" title="arXiv">'
            '<i class="ai ai-arxiv" aria-hidden="true"></i>'
            "</a>"
        )
    if label.lower() == "project page":
        return (
            '<a class="btn btn-outline-primary btn-page-header btn-sm publication-link-icon" '
            f'href="{href}" target="_blank" rel="noopener" aria-label="Project page" title="Project page">'
            '<i class="fa fa-globe" aria-hidden="true"></i>'
            "</a>"
        )
    if label.lower() in {"code", "github"}:
        return (
            '<a class="btn btn-outline-primary btn-page-header btn-sm publication-link-icon" '
            f'href="{href}" target="_blank" rel="noopener" aria-label="Code" title="Code">'
            '<i class="fa fa-github" aria-hidden="true"></i>'
            "</a>"
        )
    if label.lower() == "link":
        return (
            '<a class="btn btn-outline-primary btn-page-header btn-sm publication-link-icon" '
            f'href="{href}" target="_blank" rel="noopener" aria-label="Link" title="Link">'
            '<i class="fa fa-link" aria-hidden="true"></i>'
            "</a>"
        )
    return (
        '<a class="btn btn-outline-primary btn-page-header btn-sm" '
        f'href="{href}" target="_blank" rel="noopener">{esc(label)}</a>'
    )


def render_link_buttons(links: Iterable[Dict[str, str]]) -> str:
    buttons = [render_link(link) for link in links]
    return "\n        ".join(buttons)


def render_links(links: Iterable[Dict[str, str]]) -> str:
    buttons = render_link_buttons(links)
    if not buttons:
        return ""
    return f"      <p>{buttons}</p>"


def render_publication_links(links: Iterable[Dict[str, str]]) -> str:
    buttons = render_link_buttons(links)
    if not buttons:
        return ""
    return f'\n          <span class="publication-title-links">{buttons}</span>'


def render_talk_links(links: Iterable[Dict[str, str]]) -> str:
    buttons = render_link_buttons(links)
    if not buttons:
        return ""
    return f'<span class="talk-title-links">{buttons}</span>'


def format_talk_date(value: str) -> str:
    try:
        date = datetime.strptime(value, "%m/%d/%Y")
    except ValueError:
        return value

    return f"{MONTH_NAMES[date.month]} {date.day}, {date.year}"


def is_highlighted_author(author: str) -> bool:
    return "Puheng Li" in author


def render_authors(authors: Iterable[str]) -> str:
    rendered = []
    for author in authors:
        css = ' class="author-highlighted"' if is_highlighted_author(author) else ""
        rendered.append(f"<span{css}>{esc(author)}</span>")
    return ", ".join(rendered) + "."


def render_publication(item: Dict[str, Any]) -> str:
    venue = item.get("venue")
    venue_html = f'\n        <span class="publication-venue"><em>{esc(venue)}</em>.</span>' if venue else ""
    link_html = render_publication_links(item.get("links", []))
    return (
        '      <div class="pub-list-item" style="margin-bottom: 1rem">\n'
        '        <i class="far fa-file-alt pub-icon" aria-hidden="true"></i>\n'
        '        <span class="article-metadata li-cite-author">\n'
        f"        {render_authors(item['authors'])}\n"
        '        <span class="publication-title-row">\n'
        f'          <span class="publication-title">{esc(item["title"])}</span>{link_html}\n'
        f"        </span>{venue_html}\n"
        "        </span>\n"
        "      </div>"
    )


def render_publication_group(group: Dict[str, Any]) -> str:
    items = "\n".join(render_publication(item) for item in group["items"])
    return f"""
        <div class="row">
          <div class="section-heading col-12 col-lg-4 mb-3 mb-lg-0 d-flex flex-column align-items-center align-items-lg-start">
            <h1 class="mb-0">{esc(group['title'])}</h1>
          </div>
          <div class="col-12 col-lg-8">
{items}
          </div>
        </div>
"""


def render_research(publications: Dict[str, Any]) -> str:
    groups = "\n".join(render_publication_group(group) for group in publications["groups"])
    return f"""
    <section id="research" class="home-section wg-pages">
      <div class="home-section-bg"></div>
      <div class="container">
        <p>{esc(publications['note'])}</p>
{groups}
      </div>
    </section>
"""


def render_talk(item: Dict[str, Any]) -> str:
    date = format_talk_date(item["date"])
    link_html = render_talk_links(item.get("links", []))
    return (
        '        <div class="section-list-item talk-item">\n'
        f'          <div class="item-title">"{esc(item["title"])}"{link_html}</div>\n'
        f'          <div class="item-meta">{esc(date)} &middot; {item["description_html"]}</div>\n'
        "        </div>"
    )


def render_section(section_id: str, title: str, body_html: str) -> str:
    return f"""
    <section id="{attr(section_id)}" class="home-section wg-pages">
      <div class="home-section-bg"></div>
      <div class="container">
        <div class="row">
          <div class="section-heading col-12 col-lg-4 mb-3 mb-lg-0 d-flex flex-column align-items-center align-items-lg-start">
            <h1 class="mb-0">{esc(title)}</h1>
          </div>
          <div class="col-12 col-lg-8">
{body_html}
          </div>
        </div>
      </div>
    </section>
"""


def render_talks(talks: Iterable[Dict[str, Any]]) -> str:
    body = "      <div class=\"section-list talk-list\">\n" + "\n".join(render_talk(talk) for talk in talks) + "\n      </div>"
    return render_section("talks", "Talks", body)


def render_teaching(teaching: Dict[str, Any], service_html: str) -> str:
    courses = []
    for course in teaching["courses"]:
        title_class = "course-title"
        if course["title"] == "Resampling Methods: Bootstrap, Cross Validation and Beyond":
            title_class += " course-title-long"
        courses.append(
            "          <li>\n"
            f"            <span class=\"course-code\">{esc(course['code'])}</span>\n"
            f"            <span class=\"{title_class}\">{esc(course['title'])}</span>\n"
            f"            <span class=\"course-term\">{esc(course['term'])}</span>\n"
            "          </li>"
        )
    body = (
        "      <div class=\"section-list teaching-list\">\n"
        f"        <div class=\"item-title\">{esc(teaching['role'])}</div>\n"
        "        <ul class=\"course-list\">\n"
        + "\n".join(courses)
        + "\n        </ul>\n"
        "        <div class=\"section-list-item service-item\">\n"
        "          <div class=\"item-title\">Reviewer</div>\n"
        f"          <p>{service_html}</p>\n"
        "        </div>\n"
        "      </div>"
    )
    return render_section("teaching", "Service", body)


def render_experience(data: Dict[str, Any]) -> str:
    blocks = []
    for job in data["experience"]:
        items = "\n".join(f"          <li>{item}</li>" for item in job["items_html"])
        details = f"\n        <ul class=\"compact-list\">\n{items}\n        </ul>" if items else ""
        blocks.append(
            "        <div class=\"section-list-item experience-item\">\n"
            f"          <div class=\"item-title\">{esc(job['title'])}</div>{details}\n"
            "        </div>"
        )
    body = "      <div class=\"section-list experience-list\">\n" + "\n".join(blocks) + "\n      </div>"
    return render_section("experience", "Experience", body)


def render_honors(data: Dict[str, Any]) -> str:
    honors = "\n".join(f"          <li>{item}</li>" for item in data["honors"])
    body = (
        "      <ul class=\"section-list honors-list\">\n"
        f"{honors}\n"
        "      </ul>"
    )
    return render_section("honors", "Honors & Awards", body)


def render_miscellaneous(data: Dict[str, Any]) -> str:
    paragraphs = "\n".join(f"        <p>{item}</p>" for item in data["miscellaneous_html"])
    body = f"      <div class=\"section-copy misc-copy\">\n{paragraphs}\n      </div>"
    return render_section("miscellaneous", "Miscellaneous", body)


def render_analytics(data: Dict[str, Any]) -> str:
    visitor_map = data.get("visitor_map")
    if not visitor_map:
        return ""
    map_id = json.dumps(str(visitor_map["id"]))
    map_src = json.dumps(str(visitor_map["src"]))
    return f"""
    <section class="home-section wg-pages">
      <div class="visitor-map-container"></div>
      <script>
        (function () {{
          var container = document.currentScript.previousElementSibling;
          var mapId = {map_id};
          var mapSrc = {map_src};
          var lastMode = null;
          var colorSets = {{
            light: {{ co: "ffffff", cl: "1565c0", ct: "111827" }},
            dark: {{ co: "1f2024", cl: "ffffff", ct: "ffffff" }}
          }};

          function isDarkTheme(event) {{
            if (event && event.detail && typeof event.detail.isDarkTheme === "function") {{
              return event.detail.isDarkTheme();
            }}
            return document.body.classList.contains("dark");
          }}

          function buildMapUrl(dark) {{
            var colors = dark ? colorSets.dark : colorSets.light;
            var url = new URL(mapSrc, window.location.href);
            url.searchParams.set("co", colors.co);
            url.searchParams.set("cl", colors.cl);
            url.searchParams.set("ct", colors.ct);
            return url.toString();
          }}

          function renderMap(dark) {{
            var mode = dark ? "dark" : "light";
            if (lastMode === mode && container.children.length > 0) {{
              return;
            }}
            lastMode = mode;
            container.innerHTML = "";

            var script = document.createElement("script");
            script.type = "text/javascript";
            script.id = mapId;
            script.src = buildMapUrl(dark);
            container.appendChild(script);
          }}

          function renderCurrentMap() {{
            renderMap(isDarkTheme());
          }}

          document.addEventListener("wcThemeChange", function (event) {{
            renderMap(isDarkTheme(event));
          }});

          if (document.readyState === "loading") {{
            document.addEventListener("DOMContentLoaded", renderCurrentMap);
          }} else {{
            renderCurrentMap();
          }}
        }}());
      </script>
    </section>
"""


def common_context(data: Dict[str, Any]) -> Dict[str, str]:
    site = data["site"]
    return {
        "title": esc(site["title"]),
        "author": attr(site["author"]),
        "description": attr(site["description"]),
        "base_url": attr(site["base_url"].rstrip("/")),
        "theme_color": attr(site["theme_color"]),
        "avatar": attr(site["avatar"]),
        "favicon_svg": attr(site["favicon_svg"]),
        "favicon": attr(site["favicon"]),
        "apple_touch_icon": attr(site["apple_touch_icon"]),
        "manifest": attr(site["manifest"]),
        "footer_html": data["footer_html"],
    }


def build() -> None:
    data = load_json("site.json")
    publications = load_json("publications.json")
    talks = load_json("talks.json")
    teaching = load_json("teaching.json")

    index_context = {
        **common_context(data),
        "nav_items": render_nav_items(data["nav"]),
        "about_section": render_about(data),
        "research_section": render_research(publications),
        "talks_section": render_talks(talks),
        "teaching_section": render_teaching(teaching, data["service_html"]),
        "experience_section": render_experience(data),
        "honors_section": render_honors(data),
        "miscellaneous_section": render_miscellaneous(data),
        "analytics_section": render_analytics(data),
    }
    (ROOT_DIR / "index.html").write_text(render_template("index.html", index_context), encoding="utf-8")

    not_found_context = common_context(data)
    (ROOT_DIR / "404.html").write_text(render_template("404.html", not_found_context), encoding="utf-8")


if __name__ == "__main__":
    build()
