"""Executive design themes and design systems for Tableau Dashboards.

Provides structured palettes, card formatting, padding, borders, and font specifications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DashboardTheme:
    name: str
    description: str
    canvas_bg: str
    card_bg: str
    card_border: str
    card_border_width: int
    card_padding: int
    text_primary: str
    text_secondary: str
    text_muted: str
    accent_primary: str
    accent_secondary: str
    positive_color: str
    negative_color: str
    font_family: str
    title_font_size: int
    subtitle_font_size: int
    kpi_number_font_size: int
    body_font_size: int

    def get_zone_style(self, is_card: bool = True) -> dict[str, str | int]:
        """Return dict suitable for Tableau zone-style."""
        if is_card:
            return {
                "background-color": self.card_bg,
                "border-color": self.card_border,
                "border-style": "solid",
                "border-width": self.card_border_width,
                "padding": self.card_padding,
            }
        return {
            "background-color": self.canvas_bg,
            "border-style": "none",
            "border-width": 0,
            "padding": 0,
        }


# Pre-configured professional themes
THEMES: dict[str, DashboardTheme] = {
    "executive-light": DashboardTheme(
        name="Executive Light",
        description="Clean, modern C-level layout with soft slate canvas, crisp white cards, and corporate blue accents.",
        canvas_bg="#F1F5F9",
        card_bg="#FFFFFF",
        card_border="#E2E8F0",
        card_border_width=1,
        card_padding=8,
        text_primary="#0F172A",
        text_secondary="#475569",
        text_muted="#94A3B8",
        accent_primary="#2563EB",
        accent_secondary="#3B82F6",
        positive_color="#10B981",
        negative_color="#EF4444",
        font_family="Tableau Bold",
        title_font_size=18,
        subtitle_font_size=11,
        kpi_number_font_size=26,
        body_font_size=10,
    ),
    "executive-dark": DashboardTheme(
        name="Executive Dark",
        description="Sophisticated dark dashboard for command centers and high-contrast analytical monitors.",
        canvas_bg="#0B0F19",
        card_bg="#151D2F",
        card_border="#22304A",
        card_border_width=1,
        card_padding=8,
        text_primary="#F8FAFC",
        text_secondary="#CBD5E1",
        text_muted="#64748B",
        accent_primary="#38BDF8",
        accent_secondary="#0EA5E9",
        positive_color="#34D399",
        negative_color="#F87171",
        font_family="Tableau Bold",
        title_font_size=18,
        subtitle_font_size=11,
        kpi_number_font_size=26,
        body_font_size=10,
    ),
    "minimalist-slate": DashboardTheme(
        name="Minimalist Slate",
        description="Minimalist high-density reporting with subtle gray borders and restrained color accents.",
        canvas_bg="#FFFFFF",
        card_bg="#F8FAFC",
        card_border="#E2E8F0",
        card_border_width=1,
        card_padding=6,
        text_primary="#1E293B",
        text_secondary="#64748B",
        text_muted="#94A3B8",
        accent_primary="#0F766E",
        accent_secondary="#14B8A6",
        positive_color="#059669",
        negative_color="#DC2626",
        font_family="Tableau Book",
        title_font_size=16,
        subtitle_font_size=10,
        kpi_number_font_size=24,
        body_font_size=9,
    ),
    "periwinkle-executive": DashboardTheme(
        name="Periwinkle Executive",
        description="Figma-inspired executive command center with soft periwinkle canvas, crisp white cards, and cobalt/teal accents.",
        canvas_bg="#DFE3F2",
        card_bg="#FFFFFF",
        card_border="#E2E8F0",
        card_border_width=1,
        card_padding=8,
        text_primary="#111E29",
        text_secondary="#606B76",
        text_muted="#999CB2",
        accent_primary="#1E1ACB",
        accent_secondary="#7D85CC",
        positive_color="#32B593",
        negative_color="#FE4F60",
        font_family="Tableau Bold",
        title_font_size=18,
        subtitle_font_size=11,
        kpi_number_font_size=26,
        body_font_size=10,
    ),
    "digital-marketing": DashboardTheme(
        name="Digital Marketing",
        description="Performance marketing theme with crisp white cards, electric indigo accents, amber click indicators, and emerald conversion badges.",
        canvas_bg="#F5F7FA",
        card_bg="#FFFFFF",
        card_border="#E2E8EE",
        card_border_width=1,
        card_padding=8,
        text_primary="#2A2A2A",
        text_secondary="#42465A",
        text_muted="#787878",
        accent_primary="#4D56F6",
        accent_secondary="#5FA6C4",
        positive_color="#7ABD9A",
        negative_color="#FE4F60",
        font_family="Tableau Bold",
        title_font_size=18,
        subtitle_font_size=11,
        kpi_number_font_size=26,
        body_font_size=10,
    ),
    "ellen-blackburn": DashboardTheme(
        name="Ellen Blackburn Design System",
        description="Signature Ellen Blackburn aesthetic from Customer Support Cases & Consumer Duty Scorecard: 100% Arial typography, soft airy canvas (#F4F7FA), crisp white cards with soft architectural borders (#E2EAFD), deep midnight navy titles (#010948 / #404375), muted slate secondary text (#737899), emerald teal positive trends (#1CAF83 / #05AF7F), and a refined 4-hue categorical palette (#75A1C7, #C290B4, #F0A077, #9DAEDE).",
        canvas_bg="#F4F7FA",
        card_bg="#FFFFFF",
        card_border="#E2EAFD",
        card_border_width=1,
        card_padding=14,
        text_primary="#010948",
        text_secondary="#737899",
        text_muted="#97A6B9",
        accent_primary="#75A1C7",
        accent_secondary="#C290B4",
        positive_color="#1CAF83",
        negative_color="#E5592E",
        font_family="Arial",
        title_font_size=16,
        subtitle_font_size=9,
        kpi_number_font_size=20,
        body_font_size=9,
    ),
    "customer-support-cases": DashboardTheme(
        name="Customer Support Operations",
        description="Modern service operations & incident command center theme: Cool lavender canvas (#EFEFF8), deep midnight navy text (#010948), electric cyan accent (#1CD6E6), emerald resolved indicator (#05AF7F), and vivid coral severity alert (#E5592E).",
        canvas_bg="#EFEFF8",
        card_bg="#FFFFFF",
        card_border="#E2E8F0",
        card_border_width=1,
        card_padding=10,
        text_primary="#010948",
        text_secondary="#404375",
        text_muted="#64748B",
        accent_primary="#1CD6E6",
        accent_secondary="#AA55FF",
        positive_color="#05AF7F",
        negative_color="#E5592E",
        font_family="Tableau Bold",
        title_font_size=18,
        subtitle_font_size=11,
        kpi_number_font_size=26,
        body_font_size=10,
    ),
}


def get_theme(name_or_alias: Optional[str] = None) -> DashboardTheme:
    """Retrieve theme by name or return default executive-light."""
    if not name_or_alias:
        return THEMES["executive-light"]
    key = name_or_alias.strip().lower().replace("_", "-")
    return THEMES.get(key, THEMES["executive-light"])


def register_custom_theme(key: str, theme: DashboardTheme) -> None:
    """Dynamically register a newly learned theme."""
    clean_key = key.strip().lower().replace("_", "-")
    THEMES[clean_key] = theme

