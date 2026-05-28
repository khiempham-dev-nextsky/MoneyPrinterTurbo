from pathlib import Path

import streamlit as st

from app.config import config
from webui.studio import bootstrap
from webui.studio.assets import get_source_diagnostics, scan_asset_directory
from webui.studio.components import layout


def _render_assets_table(title: str, records) -> None:
    with layout.section_card():
        st.subheader(title)
        if not records:
            st.info("No assets found.")
            return
        st.dataframe(
            [
                {
                    "Name": item.name,
                    "Provider": item.provider,
                    "Size KB": round(item.size_bytes / 1024, 1),
                    "Path": layout.truncate_middle(item.path, 72),
                }
                for item in records
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_page() -> None:
    layout.page_header(
        "Assets",
        "Inspect local uploads, TikTok cache, and source configuration health.",
    )

    diagnostics = get_source_diagnostics(dict(config.app))
    with layout.section_card():
        st.subheader("Source diagnostics")
        st.dataframe(
            [
                {
                    "Source": item.name,
                    "State": item.state,
                    "Detail": layout.truncate_middle(item.detail, 88),
                }
                for item in diagnostics
            ],
            use_container_width=True,
            hide_index=True,
        )

    local_records = scan_asset_directory(
        Path(bootstrap.root_dir) / "storage" / "local_videos",
        provider="local",
    )
    tiktok_records = scan_asset_directory(
        Path(bootstrap.root_dir) / "storage" / "cache_videos" / "tiktok",
        provider="tiktok",
    )
    _render_assets_table("Local uploads", local_records)
    _render_assets_table("TikTok cache", tiktok_records)
