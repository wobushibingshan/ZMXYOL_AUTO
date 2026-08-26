import re
import unicodedata
from typing import Any, Iterable

from maa.agent.agent_server import AgentServer
from maa.context import Context
from maa.custom_action import CustomAction


COUNT_PATTERN = re.compile(r"([0-9]+)\s*/\s*[0-9]+")
SLASH_TRANSLATION = str.maketrans(
    {
        "\u2044": "/",
        "\u2215": "/",
        "\uff0f": "/",
    }
)


def _normalize_text(text: str) -> str:
    return unicodedata.normalize("NFKC", text).translate(SLASH_TRANSLATION)


def _parse_left_count(text: str) -> int | None:
    match = COUNT_PATTERN.search(_normalize_text(text))
    if not match:
        return None

    return int(match.group(1))


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


@AgentServer.custom_action("CheckExplorationCount")
class CheckExplorationCount(CustomAction):
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> bool:
        for text in _iter_ocr_texts(argv.reco_detail):
            left_count = _parse_left_count(text)
            if left_count is None:
                continue

            result = left_count == 4
            print(
                "CheckExplorationCount "
                f"text={text!r}, left_count={left_count}, result={result}"
            )
            return result

        print("CheckExplorationCount found no valid count text.")
        return False
