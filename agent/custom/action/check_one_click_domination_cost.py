import json
import re
import unicodedata
from typing import Any, Callable, Iterable

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction

from utils import logger


DIGIT_ALIASES = str.maketrans(
    {
        "O": "0",
        "o": "0",
        "I": "1",
        "l": "1",
        "|": "1",
        "S": "5",
        "s": "5",
        "B": "8",
        "G": "6",
        "Z": "2",
        "z": "2",
    }
)
SLASH_ALIASES = str.maketrans(
    {
        "\u2044": "/",
        "\u2215": "/",
        "\uff0f": "/",
    }
)
CURRENT_COUNT_PATTERN = re.compile(r"(\d+)\s*/\s*\d+")
DIGIT_GROUP_PATTERN = re.compile(r"\d+")


def _parse_params(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}

    try:
        params = json.loads(raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(params, dict):
        return {}

    return params


def _int_param(params: dict[str, Any], key: str, default: int) -> int:
    value = params.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text)
    return normalized.translate(SLASH_ALIASES).translate(DIGIT_ALIASES)


def _digit_groups(text: str) -> list[str]:
    return DIGIT_GROUP_PATTERN.findall(_normalize_text(text))


def _parse_current_count(text: str) -> int | None:
    normalized = _normalize_text(text)
    match = CURRENT_COUNT_PATTERN.search(normalized)
    if match:
        return int(match.group(1))

    groups = DIGIT_GROUP_PATTERN.findall(normalized)
    if not groups:
        return None

    return int(groups[0])


def _parse_cost_count(text: str) -> int | None:
    groups = _digit_groups(text)
    if not groups:
        return None

    return int(groups[-1])


def _iter_strings(value: Any) -> Iterable[str]:
    if value is None:
        return

    if isinstance(value, str):
        yield value
        return

    if isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)
        return

    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_strings(item)


def _unique_texts(texts: Iterable[str]) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()

    for text in texts:
        normalized = text.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)

    return unique


def _iter_result_texts(results: Any) -> Iterable[str]:
    for result in results or ():
        text = getattr(result, "text", None)
        if isinstance(text, str):
            yield text


def _iter_ocr_texts(reco_detail: Any) -> Iterable[str]:
    if reco_detail is None:
        return

    best_result = getattr(reco_detail, "best_result", None)
    best_text = getattr(best_result, "text", None)
    if isinstance(best_text, str):
        yield best_text

    yield from _iter_result_texts(getattr(reco_detail, "filtered_results", None))
    yield from _iter_result_texts(getattr(reco_detail, "all_results", None))
    yield from _iter_strings(getattr(reco_detail, "raw_detail", None))


def _get_sub_results(reco_detail: Any) -> list[Any]:
    if reco_detail is None:
        return []

    candidates = [getattr(reco_detail, "best_result", None)]
    candidates.extend(getattr(reco_detail, "filtered_results", None) or [])
    candidates.extend(getattr(reco_detail, "all_results", None) or [])

    for candidate in candidates:
        sub_results = getattr(candidate, "sub_results", None)
        if isinstance(sub_results, list):
            return sub_results

    return []


def _get_indexed_result(results: list[Any], index: int) -> Any | None:
    try:
        return results[index]
    except IndexError:
        return None


def _parse_from_texts(
    reco_detail: Any,
    parser: Callable[[str], int | None],
) -> tuple[int | None, str | None]:
    for text in _iter_ocr_texts(reco_detail):
        value = parser(text)
        if value is not None:
            return value, text

    return None, None


def _parse_from_text_list(
    texts: Iterable[str],
    parser: Callable[[str], int | None],
) -> tuple[int | None, str | None]:
    for text in texts:
        value = parser(text)
        if value is not None:
            return value, text

    return None, None


def _parse_cost_from_raw_texts(texts: Iterable[str]) -> tuple[int | None, str | None]:
    last_value: int | None = None
    last_text: str | None = None

    for text in texts:
        value = _parse_cost_count(text)
        if value is not None:
            last_value = value
            last_text = text

    return last_value, last_text


def _log_reco_state(
    reason: str,
    reco_detail: Any,
    sub_results: list[Any],
    current_index: int,
    cost_index: int,
) -> list[str]:
    parent_texts = _unique_texts(_iter_ocr_texts(reco_detail))
    sub_texts = [
        _unique_texts(_iter_ocr_texts(sub_result))
        for sub_result in sub_results
    ]
    logger.warning(
        "CheckOneClickDominationCost %s: current_index=%s, cost_index=%s, "
        "sub_result_count=%s, parent_texts=%r, sub_texts=%r",
        reason,
        current_index,
        cost_index,
        len(sub_results),
        parent_texts,
        sub_texts,
    )
    return parent_texts


@AgentServer.custom_action("CheckOneClickDominationCost")
class CheckOneClickDominationCost(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        params = _parse_params(argv.custom_action_param)
        current_index = _int_param(params, "current_index", 0)
        cost_index = _int_param(params, "cost_index", 1)

        sub_results = _get_sub_results(argv.reco_detail)
        current_detail = _get_indexed_result(sub_results, current_index)
        cost_detail = _get_indexed_result(sub_results, cost_index)

        if not sub_results:
            fallback_texts = _log_reco_state(
                "missing OCR sub results",
                argv.reco_detail,
                sub_results,
                current_index,
                cost_index,
            )
            current_count, current_text = _parse_from_text_list(
                fallback_texts,
                _parse_current_count,
            )
            cost_count, cost_text = _parse_cost_from_raw_texts(fallback_texts)
        elif current_detail is None or cost_detail is None:
            _log_reco_state(
                "OCR sub result index out of range",
                argv.reco_detail,
                sub_results,
                current_index,
                cost_index,
            )
            return False
        else:
            current_count, current_text = _parse_from_texts(
                current_detail,
                _parse_current_count,
            )
            cost_count, cost_text = _parse_from_texts(cost_detail, _parse_cost_count)

        if current_count is None or cost_count is None:
            _log_reco_state(
                "failed to parse counts",
                argv.reco_detail,
                sub_results,
                current_index,
                cost_index,
            )
            logger.warning(
                "CheckOneClickDominationCost parse failure: "
                "current_text=%r, cost_text=%r",
                current_text,
                cost_text,
            )
            return False

        result = 0 < cost_count < current_count
        logger.info(
            "CheckOneClickDominationCost "
            "current_text=%r, current=%s, cost_text=%r, cost=%s, result=%s",
            current_text,
            current_count,
            cost_text,
            cost_count,
            result,
        )
        return result
