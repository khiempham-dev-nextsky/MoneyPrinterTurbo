import streamlit as st

from app.config import config
from webui.studio.components import layout

LLM_PROVIDERS = [
    "OpenAI",
    "Moonshot",
    "Azure",
    "Qwen",
    "DeepSeek",
    "ModelScope",
    "Gemini",
    "Ollama",
    "G4f",
    "OneAPI",
    "Cloudflare",
    "ERNIE",
    "Pollinations",
    "LiteLLM",
]


def _keys_to_text(value) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value or "")


def _save_keys(name: str, value: str) -> None:
    cleaned = value.replace(" ", "")
    config.app[name] = cleaned.split(",") if cleaned else []


def render_page() -> None:
    layout.page_header(
        "Settings",
        "Configure LLM, TTS, video sources, and advanced runtime settings.",
    )

    with st.form("studio_llm_settings"):
        st.subheader("LLM Providers")
        saved_provider = config.app.get("llm_provider", "OpenAI").lower()
        provider_labels = LLM_PROVIDERS
        provider_values = [provider.lower() for provider in provider_labels]
        provider_index = provider_values.index(saved_provider) if saved_provider in provider_values else 0
        provider = st.selectbox(
            "LLM Provider",
            options=provider_labels,
            index=provider_index,
        ).lower()
        api_key = st.text_input(
            "API Key",
            value=config.app.get(f"{provider}_api_key", ""),
            type="password",
        )
        base_url = st.text_input("Base Url", value=config.app.get(f"{provider}_base_url", ""))
        model_name = st.text_input(
            "Model Name",
            value=config.app.get(f"{provider}_model_name", ""),
        )
        account_id = ""
        if provider == "cloudflare":
            account_id = st.text_input(
                "Account ID",
                value=config.app.get(f"{provider}_account_id", ""),
            )
        secret_key = ""
        if provider == "ernie":
            secret_key = st.text_input(
                "Secret Key",
                value=config.app.get(f"{provider}_secret_key", ""),
                type="password",
            )
        if st.form_submit_button("Save LLM Settings"):
            config.app["llm_provider"] = provider
            config.app[f"{provider}_api_key"] = api_key
            config.app[f"{provider}_base_url"] = base_url
            if model_name:
                config.app[f"{provider}_model_name"] = model_name
            if account_id:
                config.app[f"{provider}_account_id"] = account_id
            if secret_key:
                config.app[f"{provider}_secret_key"] = secret_key
            config.save_config()
            st.success("LLM settings saved")

    with st.form("studio_video_source_settings"):
        st.subheader("Video Sources")
        pexels_keys = st.text_input(
            "Pexels API Keys",
            value=_keys_to_text(config.app.get("pexels_api_keys", [])),
            type="password",
        )
        pixabay_keys = st.text_input(
            "Pixabay API Keys",
            value=_keys_to_text(config.app.get("pixabay_api_keys", [])),
            type="password",
        )
        tiktok_provider = st.selectbox(
            "TikTok Search Provider",
            options=["serpapi", "openai_web_search"],
            index=0
            if config.app.get("tiktok_search_provider", "serpapi") == "serpapi"
            else 1,
        )
        tiktok_key = st.text_input(
            "TikTok Search API Key",
            value=config.app.get("tiktok_search_api_key", ""),
            type="password",
        )
        tiktok_cookie_file = st.text_input(
            "TikTok Cookie File",
            value=config.app.get("tiktok_cookie_file", ""),
        )
        tiktok_timeout = st.number_input(
            "TikTok OpenAI Web Search Timeout",
            min_value=30,
            max_value=900,
            value=int(config.app.get("tiktok_openai_web_search_timeout", 300)),
            step=30,
        )
        if st.form_submit_button("Save Source Settings"):
            _save_keys("pexels_api_keys", pexels_keys)
            _save_keys("pixabay_api_keys", pixabay_keys)
            config.app["tiktok_search_provider"] = tiktok_provider
            config.app["tiktok_search_api_key"] = tiktok_key
            config.app["tiktok_cookie_file"] = tiktok_cookie_file
            config.app["tiktok_openai_web_search_timeout"] = int(tiktok_timeout)
            config.save_config()
            st.success("Source settings saved")

    with st.form("studio_tts_settings"):
        st.subheader("TTS Providers")
        config.ui["tts_server"] = st.selectbox(
            "TTS Server",
            options=["azure-tts-v1", "azure-tts-v2", "siliconflow", "gemini-tts"],
            index=["azure-tts-v1", "azure-tts-v2", "siliconflow", "gemini-tts"].index(
                config.ui.get("tts_server", "azure-tts-v1")
            )
            if config.ui.get("tts_server", "azure-tts-v1")
            in ["azure-tts-v1", "azure-tts-v2", "siliconflow", "gemini-tts"]
            else 0,
        )
        config.azure["speech_region"] = st.text_input(
            "Azure Speech Region",
            value=config.azure.get("speech_region", ""),
        )
        config.azure["speech_key"] = st.text_input(
            "Azure Speech Key",
            value=config.azure.get("speech_key", ""),
            type="password",
        )
        config.siliconflow["api_key"] = st.text_input(
            "SiliconFlow API Key",
            value=config.siliconflow.get("api_key", ""),
            type="password",
        )
        if st.form_submit_button("Save TTS Settings"):
            config.save_config()
            st.success("TTS settings saved")

