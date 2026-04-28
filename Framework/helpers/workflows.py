import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx

from Framework.helpers.logger import LOGGER
from config import *


FEATURE_FLAG_SIGNATURE = "disable_signature_verification"
FEATURE_FLAG_CN_NOTIF = "cn_notification_fix"
FEATURE_FLAG_SECURE = "disable_secure_flag"
FEATURE_FLAG_KAORIOS = "kaorios_toolbox"
FEATURE_FLAG_GBOARD = "add_gboard"

FEATURE_CATALOG = (
    {
        "state_key": "enable_signature_bypass",
        "flag": FEATURE_FLAG_SIGNATURE,
        "callback_data": "feature_signature",
        "button_label": "Disable Signature Verification",
        "summary_label": "Signature Verification Bypass",
        "min_api": 33,
    },
    {
        "state_key": "enable_kaorios_toolbox",
        "flag": FEATURE_FLAG_KAORIOS,
        "callback_data": "feature_kaorios",
        "button_label": "Kaorios Toolbox (Play Integrity Fix)",
        "summary_label": "Kaorios Toolbox (Play Integrity Fix)",
        "min_api": 33,
    },
    {
        "state_key": "enable_add_gboard",
        "flag": FEATURE_FLAG_GBOARD,
        "callback_data": "feature_gboard",
        "button_label": "Add Gboard Support",
        "summary_label": "Add Gboard Support",
        "min_api": 33,
    },
    {
        "state_key": "enable_cn_notification_fix",
        "flag": FEATURE_FLAG_CN_NOTIF,
        "callback_data": "feature_cn_notif",
        "button_label": "CN Notification Fix",
        "summary_label": "CN Notification Fix",
        "min_api": 35,
    },
    {
        "state_key": "enable_disable_secure_flag",
        "flag": FEATURE_FLAG_SECURE,
        "callback_data": "feature_secure_flag",
        "button_label": "Disable Secure Flag",
        "summary_label": "Disable Secure Flag",
        "min_api": 35,
    },
)


def _parse_iso8601(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_api_level(api_level: str) -> str:
    api_str = str(api_level).strip() if api_level is not None else ""

    if api_str in {"13", "14", "15", "16"} or (
        api_str.replace(".", "", 1).isdigit() and int(float(api_str)) in {13, 14, 15, 16}
    ):
        try:
            from Framework.helpers.provider import android_version_to_api_level
            return android_version_to_api_level(api_str)
        except Exception:
            mapping = {"13": "33", "14": "34", "15": "35", "16": "36"}
            return mapping.get(api_str, api_str)

    return str(int(float(api_str))) if api_str else api_str


def _feature_list_from_flags(features: dict | None = None) -> list[str]:
    features = features or {
        "enable_signature_bypass": True,
        "enable_cn_notification_fix": False,
        "enable_disable_secure_flag": False,
        "enable_kaorios_toolbox": False,
        "enable_add_gboard": False,
    }

    feature_list: list[str] = []
    if features.get("enable_signature_bypass", True):
        feature_list.append(FEATURE_FLAG_SIGNATURE)
    if features.get("enable_cn_notification_fix", False):
        feature_list.append(FEATURE_FLAG_CN_NOTIF)
    if features.get("enable_disable_secure_flag", False):
        feature_list.append(FEATURE_FLAG_SECURE)
    if features.get("enable_kaorios_toolbox", False):
        feature_list.append(FEATURE_FLAG_KAORIOS)
    if features.get("enable_add_gboard", False):
        feature_list.append(FEATURE_FLAG_GBOARD)

    if not feature_list:
        feature_list.append(FEATURE_FLAG_SIGNATURE)

    return feature_list


def _normalized_api_int(api_level: str) -> int:
    try:
        return int(_normalize_api_level(api_level))
    except Exception:
        return 0


def get_feature_catalog_for_api(api_level: str) -> list[dict[str, Any]]:
    api_int = _normalized_api_int(api_level)
    return [feature for feature in FEATURE_CATALOG if api_int >= feature["min_api"]]


def get_default_feature_state() -> dict[str, bool]:
    return {feature["state_key"]: False for feature in FEATURE_CATALOG}


def get_selected_feature_labels(features: dict | None = None) -> list[str]:
    features = features or {}
    selected = []

    for feature in FEATURE_CATALOG:
        if features.get(feature["state_key"], False):
            selected.append(feature["summary_label"])

    return selected


def _allowed_features_for_api(api_level: str) -> set[str]:
    return {feature["flag"] for feature in get_feature_catalog_for_api(api_level)}


def _required_inputs_for_features(feature_list: list[str]) -> set[str]:
    required = set()
    for feature in feature_list:
        if feature == FEATURE_FLAG_SIGNATURE:
            required.update({"framework_url", "services_url", "miui_services_url"})
        elif feature == FEATURE_FLAG_KAORIOS:
            required.add("framework_url")
        elif feature == FEATURE_FLAG_CN_NOTIF:
            required.add("miui_services_url")
        elif feature == FEATURE_FLAG_SECURE:
            required.update({"services_url", "miui_services_url"})
        elif feature == FEATURE_FLAG_GBOARD:
            required.update({"miui_services_url", "miui_framework_url"})
    return required


def _build_workflow_inputs(
    links: dict,
    device_name: str,
    device_codename: str,
    version_name: str,
    api_level: str,
    user_id: int,
    feature_list: list[str],
) -> dict[str, str]:
    inputs = {
        "api_level": api_level,
        "device_name": device_name,
        "device_codename": device_codename,
        "version_name": version_name,
        "user_id": str(user_id),
        "features": ",".join(feature_list),
    }

    url_mapping = {
        "framework.jar": "framework_url",
        "services.jar": "services_url",
        "miui-services.jar": "miui_services_url",
        "miui-framework.jar": "miui_framework_url",
    }
    for jar_name, input_key in url_mapping.items():
        url = links.get(jar_name)
        if url:
            inputs[input_key] = url

    return inputs


def _validate_dispatch_inputs(api_level: str, feature_list: list[str], inputs: dict[str, str]) -> None:
    unsupported = set(feature_list) - _allowed_features_for_api(api_level)
    if unsupported:
        raise ValueError(
            f"Unsupported features for API {api_level}: {', '.join(sorted(unsupported))}"
        )

    required = _required_inputs_for_features(feature_list)
    missing = [key for key in sorted(required) if not inputs.get(key)]
    if missing:
        raise ValueError(
            "Missing required input URLs for selected features: " + ", ".join(missing)
        )


def _headers() -> dict[str, str]:
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is not configured")

    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FrameworkPatcherBot/1.0",
    }


def _select_workflow_id(api_level: str) -> str:
    """Select the appropriate workflow file based on API level.

    Accepts either Android version (e.g., '16', 16, '15.0') or API level ('36'..'33').
    Always returns a non-empty workflow file name.
    """
    api_str = _normalize_api_level(api_level)

    # Map API levels to workflow files
    if api_str == "36":
        return WORKFLOW_ID_A16 or "android16.yml"
    if api_str == "35":
        return WORKFLOW_ID_A15 or "android15.yml"
    if api_str == "34":
        return WORKFLOW_ID_A14 or "android14.yml"
    if api_str == "33":
        return WORKFLOW_ID_A13 or "android13.yml"

    # Unknown input: fall back to explicit WORKFLOW_ID, then to latest known workflow
    if WORKFLOW_ID:
        return WORKFLOW_ID

    # Safe default
    return WORKFLOW_ID_A16 or WORKFLOW_ID_A15 or WORKFLOW_ID_A14 or WORKFLOW_ID_A13 or "android15.yml"


async def trigger_github_workflow_async(links: dict, device_name: str, device_codename: str, version_name: str,
                                        api_level: str,
                                        user_id: int, features: dict = None) -> dict[str, Any]:
    """Trigger GitHub workflow and return structured dispatch metadata."""
    workflow_id = _select_workflow_id(api_level)
    if not workflow_id:
        LOGGER.error(f"Could not determine workflow ID for API level: {api_level}")
        raise ValueError(f"Could not determine workflow ID for API level: {api_level}")

    api_level_clean = _normalize_api_level(api_level)
    feature_list = _feature_list_from_flags(features)
    inputs = _build_workflow_inputs(
        links=links,
        device_name=device_name,
        device_codename=device_codename,
        version_name=version_name,
        api_level=api_level_clean,
        user_id=user_id,
        feature_list=feature_list,
    )
    _validate_dispatch_inputs(api_level_clean, feature_list, inputs)

    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_id}/dispatches"
    headers = _headers()
    data = {"ref": "master", "inputs": inputs}

    workflow_api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_id}"
    dispatch_ts = _now_utc()

    LOGGER.info(
        "Attempting workflow dispatch: workflow=%s api=%s user=%s device=%s version=%s features=%s",
        workflow_id,
        api_level_clean,
        user_id,
        device_name,
        version_name,
        ",".join(feature_list),
    )

    max_attempts = 3
    base_timeout = 60

    for attempt in range(max_attempts):
        try:
            timeout = base_timeout + (attempt * 20)
            LOGGER.info(f"GitHub workflow trigger attempt {attempt + 1}/{max_attempts} with timeout {timeout}s")

            async with httpx.AsyncClient(
                    timeout=httpx.Timeout(
                        connect=20.0,
                        read=timeout,
                        write=timeout,
                        pool=10.0
                    ),
                    limits=httpx.Limits(max_connections=5, max_keepalive_connections=2)
            ) as client:
                # Fail fast if workflow id/file is wrong.
                workflow_resp = await client.get(workflow_api_url, headers=headers)
                workflow_resp.raise_for_status()

                resp = await client.post(url, json=data, headers=headers)
                resp.raise_for_status()

                LOGGER.info(
                    "Workflow dispatched successfully on attempt %s: workflow=%s user=%s",
                    attempt + 1,
                    workflow_id,
                    user_id,
                )
                return {
                    "status_code": resp.status_code,
                    "workflow_id": workflow_id,
                    "api_level": api_level_clean,
                    "features": feature_list,
                    "dispatch_time": dispatch_ts.isoformat().replace("+00:00", "Z"),
                    "workflow_page_url": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_id}",
                }

        except httpx.TimeoutException as e:
            LOGGER.error(f"GitHub API timeout on attempt {attempt + 1}: {e}")
            if attempt == max_attempts - 1:
                raise e

        except httpx.HTTPStatusError as e:
            LOGGER.error(f"GitHub API error {e.response.status_code} on attempt {attempt + 1}: {e.response.text}")
            if e.response.status_code in [429, 502, 503, 504]:  # Retry on these status codes
                if attempt < max_attempts - 1:
                    wait_time = min(2 ** attempt, 30)
                    LOGGER.info(f"Retrying GitHub API call in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
            raise e

        except httpx.RequestError as e:
            LOGGER.error(f"GitHub API request error on attempt {attempt + 1}: {e}")
            if attempt < max_attempts - 1:
                wait_time = min(2 ** attempt, 30)
                LOGGER.info(f"Retrying GitHub API call in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
            raise e

        except Exception as e:
            LOGGER.error(f"Unexpected error triggering GitHub workflow on attempt {attempt + 1}: {e}", exc_info=True)
            if attempt < max_attempts - 1:
                wait_time = min(2 ** attempt, 30)
                LOGGER.info(f"Retrying GitHub API call in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
                continue
            raise e

        # Wait before retry (except on last attempt)
        if attempt < max_attempts - 1:
            wait_time = min(2 ** attempt, 30)
            LOGGER.info(f"Retrying GitHub API call in {wait_time} seconds...")
            await asyncio.sleep(wait_time)

    raise Exception("Failed to trigger GitHub workflow after all attempts")


async def discover_dispatched_workflow_run(
    workflow_id: str,
    dispatch_time_iso: str,
    timeout_seconds: int | None = None,
) -> dict[str, Any] | None:
    """Find the run created from a recent workflow_dispatch call."""
    timeout_seconds = timeout_seconds or WORKFLOW_RUN_DISCOVERY_TIMEOUT
    headers = _headers()
    dispatch_time = _parse_iso8601(dispatch_time_iso)
    deadline = _now_utc().timestamp() + timeout_seconds

    runs_url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_id}/runs"
        "?event=workflow_dispatch&branch=master&per_page=20"
    )

    async with httpx.AsyncClient(timeout=30.0) as client:
        while _now_utc().timestamp() < deadline:
            try:
                resp = await client.get(runs_url, headers=headers)
                resp.raise_for_status()
                runs = resp.json().get("workflow_runs", [])

                candidates = []
                for run in runs:
                    created_at = run.get("created_at")
                    if not created_at:
                        continue
                    created_dt = _parse_iso8601(created_at)
                    if created_dt >= dispatch_time:
                        candidates.append(run)

                if candidates:
                    candidates.sort(key=lambda r: r.get("created_at", ""), reverse=True)
                    run = candidates[0]
                    LOGGER.info(
                        "Discovered workflow run: workflow=%s run_id=%s html_url=%s",
                        workflow_id,
                        run.get("id"),
                        run.get("html_url"),
                    )
                    return run
            except Exception as e:
                LOGGER.warning("Run discovery retry due to error: %s", e)

            await asyncio.sleep(5)

    LOGGER.warning("Workflow run discovery timed out: workflow=%s", workflow_id)
    return None


async def poll_workflow_run_until_terminal(
    run_id: int,
    timeout_seconds: int | None = None,
    poll_interval: int | None = None,
) -> dict[str, Any]:
    """Poll a run until completed/terminal or timeout."""
    timeout_seconds = timeout_seconds or WORKFLOW_RUN_POLL_TIMEOUT
    poll_interval = poll_interval or WORKFLOW_RUN_POLL_INTERVAL

    headers = _headers()
    run_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs/{run_id}"
    deadline = _now_utc().timestamp() + timeout_seconds

    async with httpx.AsyncClient(timeout=30.0) as client:
        while _now_utc().timestamp() < deadline:
            resp = await client.get(run_url, headers=headers)
            resp.raise_for_status()
            run = resp.json()

            status = run.get("status")
            conclusion = run.get("conclusion")
            LOGGER.info(
                "Workflow poll: run_id=%s status=%s conclusion=%s",
                run_id,
                status,
                conclusion,
            )

            if status == "completed":
                return {
                    "state": "completed",
                    "status": status,
                    "conclusion": conclusion,
                    "run_id": run.get("id"),
                    "run_url": run.get("html_url"),
                }

            await asyncio.sleep(poll_interval)

    return {
        "state": "timeout",
        "status": "timed_out",
        "conclusion": None,
        "run_id": run_id,
        "run_url": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions/runs/{run_id}",
    }


async def track_dispatched_workflow(
    workflow_id: str,
    dispatch_time_iso: str,
) -> dict[str, Any]:
    """Discover and monitor a dispatched workflow until terminal state."""
    run = await discover_dispatched_workflow_run(workflow_id, dispatch_time_iso)
    if not run:
        return {
            "state": "discovery_timeout",
            "status": "unknown",
            "conclusion": None,
            "run_id": None,
            "run_url": f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_id}",
        }

    run_id = run.get("id")
    if not run_id:
        return {
            "state": "discovery_error",
            "status": "unknown",
            "conclusion": None,
            "run_id": None,
            "run_url": run.get("html_url") or f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/actions/workflows/{workflow_id}",
        }

    return await poll_workflow_run_until_terminal(int(run_id))

