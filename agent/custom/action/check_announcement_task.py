import json  # 导入该模块供后续逻辑使用。
import re  # 导入该模块供后续逻辑使用。
import unicodedata  # 导入该模块供后续逻辑使用。
from dataclasses import dataclass  # 从依赖模块导入后续要用的类型或类。
from typing import Any, Iterable  # 从依赖模块导入后续要用的类型或类。

from maa.agent.agent_server import AgentServer  # 从依赖模块导入后续要用的类型或类。
from maa.context import Context  # 从依赖模块导入后续要用的类型或类。
from maa.custom_action import CustomAction  # 从依赖模块导入后续要用的类型或类。


OCR_DIGIT_TRANSLATION = str.maketrans(  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
    {  # 开始一个多行结构。
        "O": "0",  # 执行通告任务自定义动作的一行逻辑。
        "o": "0",  # 执行通告任务自定义动作的一行逻辑。
        "I": "1",  # 执行通告任务自定义动作的一行逻辑。
        "l": "1",  # 执行通告任务自定义动作的一行逻辑。
        "|": "1",  # 执行通告任务自定义动作的一行逻辑。
        "S": "5",  # 执行通告任务自定义动作的一行逻辑。
        "s": "5",  # 执行通告任务自定义动作的一行逻辑。
        "B": "8",  # 执行通告任务自定义动作的一行逻辑。
        "G": "6",  # 执行通告任务自定义动作的一行逻辑。
        "Z": "2",  # 执行通告任务自定义动作的一行逻辑。
        "z": "2",  # 执行通告任务自定义动作的一行逻辑。
    }  # 结束当前多行结构。
)  # 结束当前多行结构。
SLASH_TRANSLATION = str.maketrans(  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
    {  # 开始一个多行结构。
        "\u2044": "/",  # 执行通告任务自定义动作的一行逻辑。
        "\u2215": "/",  # 执行通告任务自定义动作的一行逻辑。
        "\uff0f": "/",  # 执行通告任务自定义动作的一行逻辑。
    }  # 结束当前多行结构。
)  # 结束当前多行结构。
COUNT_PATTERN = re.compile(r"([0-9]+)\s*/\s*([0-9]+)")  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。

COMPLETE_LIMIT_RECO = "通告任务_检查完成次数"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
BACK_TO_FIRST_ACTION = "通告任务_回到第一页"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
SWIPE_TO_SECOND_ACTION = "通告任务_滑动到第二页"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
CARD_TEXT_RECO = "通告任务_识别卡片文本"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
SUBMIT_RECO = "通告任务_识别提交按钮"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
CLAIM_RECO = "通告任务_识别领取按钮"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
SUBMIT_CLICK_ACTION = "通告任务_点击提交按钮"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
CLAIM_CLICK_ACTION = "通告任务_点击领取按钮"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
SUBMIT_WINDOW_TASK = "通告任务_提交窗口流程"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
SUBMIT_WINDOW_CLOSE_RECO = "通告任务_识别提交窗口关闭按钮"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
SUBMIT_WINDOW_CLOSE_ACTION = "通告任务_点击提交窗口关闭按钮"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
SUBMIT_WINDOW_CLOSE_NODE = "通告任务_提交窗口_关闭道具页"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。

SUBMIT_TEMPLATE = "Alliance/公告_提交.png"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
CLAIM_TEMPLATE = "Alliance/公告_领取.png"  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。

_SKIPPED_TASKS: set[str] = set()  # 定义模块级缓存，记录本轮任务跳过状态。
_LAST_TASK_BY_SLOT: dict[str, str] = {}  # 定义模块级缓存，记录本轮任务跳过状态。


@dataclass(frozen=True)  # 声明数据类，减少手写初始化代码。
class AnnouncementSlot:  # 定义一个类，封装相关数据或自定义动作。
    page: str  # 声明数据字段及其类型。
    slot: str  # 声明数据字段及其类型。
    name: str  # 声明数据字段及其类型。
    card_roi: list[int]  # 声明数据字段及其类型。
    button_roi: list[int]  # 声明数据字段及其类型。


FIRST_PAGE_SLOTS = (  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
    AnnouncementSlot(  # 创建一个通告任务卡片槽位配置。
        page="first",  # 标记该槽位所在页面。
        slot="slot_1",  # 标记该槽位的稳定编号。
        name="任务一",  # 记录日志中显示的任务名称。
        card_roi=[283, 189, 219, 279],  # 配置该卡片文本识别区域。
        button_roi=[290, 389, 203, 70],  # 配置该卡片按钮所在区域。
    ),  # 结束当前多行结构。
    AnnouncementSlot(  # 创建一个通告任务卡片槽位配置。
        page="first",  # 标记该槽位所在页面。
        slot="slot_2",  # 标记该槽位的稳定编号。
        name="任务二",  # 记录日志中显示的任务名称。
        card_roi=[556, 187, 213, 282],  # 配置该卡片文本识别区域。
        button_roi=[556, 390, 209, 76],  # 配置该卡片按钮所在区域。
    ),  # 结束当前多行结构。
)  # 结束当前多行结构。
SECOND_PAGE_SLOTS = (  # 定义 pipeline 节点名或模板路径常量，避免到处写硬编码字符串。
    AnnouncementSlot(  # 创建一个通告任务卡片槽位配置。
        page="second",  # 标记该槽位所在页面。
        slot="slot_3",  # 标记该槽位的稳定编号。
        name="任务三",  # 记录日志中显示的任务名称。
        card_roi=[486, 189, 216, 281],  # 配置该卡片文本识别区域。
        button_roi=[491, 392, 206, 70],  # 配置该卡片按钮所在区域。
    ),  # 结束当前多行结构。
    AnnouncementSlot(  # 创建一个通告任务卡片槽位配置。
        page="second",  # 标记该槽位所在页面。
        slot="slot_4",  # 标记该槽位的稳定编号。
        name="任务四",  # 记录日志中显示的任务名称。
        card_roi=[756, 187, 219, 282],  # 配置该卡片文本识别区域。
        button_roi=[754, 393, 222, 79],  # 配置该卡片按钮所在区域。
    ),  # 结束当前多行结构。
)  # 结束当前多行结构。


def _parse_params(raw: Any) -> dict[str, Any]:  # 定义辅助函数，供通告任务流程复用。
    if raw is None:  # 判断条件是否满足。
        return {}  # 返回计算结果给调用方。

    if isinstance(raw, dict):  # 判断条件是否满足。
        return raw  # 返回计算结果给调用方。

    if not isinstance(raw, str) or not raw:  # 判断条件是否满足。
        return {}  # 返回计算结果给调用方。

    try:  # 尝试执行可能失败的 Maa 调用。
        params = json.loads(raw)  # 解析 pipeline 传入的 JSON 参数。
    except json.JSONDecodeError:  # 捕获异常，避免自定义动作直接崩溃。
        return {}  # 返回计算结果给调用方。

    return params if isinstance(params, dict) else {}  # 返回计算结果给调用方。


def _normalize_text(text: str) -> str:  # 定义辅助函数，供通告任务流程复用。
    normalized = unicodedata.normalize("NFKC", text)  # 统一文本宽窄字符，降低 OCR 噪声影响。
    return normalized.translate(SLASH_TRANSLATION)  # 返回计算结果给调用方。


def _normalize_digits(text: str) -> str:  # 定义辅助函数，供通告任务流程复用。
    return _normalize_text(text).translate(OCR_DIGIT_TRANSLATION)  # 返回计算结果给调用方。


def _iter_strings(value: Any) -> Iterable[str]:  # 定义辅助函数，供通告任务流程复用。
    if value is None:  # 判断条件是否满足。
        return  # 执行通告任务自定义动作的一行逻辑。

    if isinstance(value, str):  # 判断条件是否满足。
        yield value  # 产出当前解析到的文本。
        return  # 执行通告任务自定义动作的一行逻辑。

    if isinstance(value, dict):  # 判断条件是否满足。
        for item in value.values():  # 遍历候选结果或槽位。
            yield from _iter_strings(item)  # 继续产出嵌套结构中的文本。
        return  # 执行通告任务自定义动作的一行逻辑。

    if isinstance(value, (list, tuple, set)):  # 判断条件是否满足。
        for item in value:  # 遍历候选结果或槽位。
            yield from _iter_strings(item)  # 继续产出嵌套结构中的文本。


def _iter_result_texts(results: Any) -> Iterable[str]:  # 定义辅助函数，供通告任务流程复用。
    for result in results or ():  # 遍历候选结果或槽位。
        text = getattr(result, "text", None)  # 安全读取对象属性，兼容 Maa 返回结构差异。
        if isinstance(text, str):  # 判断条件是否满足。
            yield text  # 产出当前解析到的文本。

        for sub_result in getattr(result, "sub_results", None) or ():  # 遍历候选结果或槽位。
            yield from _iter_ocr_texts(sub_result)  # 继续产出嵌套结构中的文本。


def _iter_ocr_texts(reco_detail: Any) -> Iterable[str]:  # 定义辅助函数，供通告任务流程复用。
    if reco_detail is None:  # 判断条件是否满足。
        return  # 执行通告任务自定义动作的一行逻辑。

    best_result = getattr(reco_detail, "best_result", None)  # 安全读取对象属性，兼容 Maa 返回结构差异。
    best_text = getattr(best_result, "text", None)  # 安全读取对象属性，兼容 Maa 返回结构差异。
    if isinstance(best_text, str):  # 判断条件是否满足。
        yield best_text  # 产出当前解析到的文本。

    for sub_result in getattr(best_result, "sub_results", None) or ():  # 遍历候选结果或槽位。
        yield from _iter_ocr_texts(sub_result)  # 继续产出嵌套结构中的文本。

    yield from _iter_result_texts(getattr(reco_detail, "filtered_results", None))  # 继续产出嵌套结构中的文本。
    yield from _iter_result_texts(getattr(reco_detail, "all_results", None))  # 继续产出嵌套结构中的文本。
    yield from _iter_strings(getattr(reco_detail, "raw_detail", None))  # 继续产出嵌套结构中的文本。


def _compact_text(texts: Iterable[str]) -> str:  # 定义辅助函数，供通告任务流程复用。
    parts: list[str] = []  # 执行通告任务自定义动作的一行逻辑。
    seen: set[str] = set()  # 执行通告任务自定义动作的一行逻辑。

    for text in texts:  # 遍历候选结果或槽位。
        compact = re.sub(r"\s+", "", _normalize_text(text))  # 压缩空白字符，便于比较和缓存。
        if not compact or compact in seen:  # 判断条件是否满足。
            continue  # 跳过本轮循环，继续检查下一个候选项。
        seen.add(compact)  # 调用对象方法或更新对象状态。
        parts.append(compact)  # 调用对象方法或更新对象状态。

    return "|".join(parts)  # 返回计算结果给调用方。


def _slot_key(params: dict[str, Any]) -> str:  # 定义辅助函数，供通告任务流程复用。
    page = str(params.get("page", ""))  # 写入槽位所在页面参数。
    slot = str(params.get("slot", ""))  # 写入槽位编号参数。
    return f"{page}:{slot}"  # 返回计算结果给调用方。


def _slot_params(slot: AnnouncementSlot) -> dict[str, str]:  # 定义辅助函数，供通告任务流程复用。
    return {"page": slot.page, "slot": slot.slot}  # 返回计算结果给调用方。


def _task_key(params: dict[str, Any], reco_detail: Any) -> str:  # 定义辅助函数，供通告任务流程复用。
    slot_key = _slot_key(params)  # 计算并保存中间结果。
    text = _compact_text(_iter_ocr_texts(reco_detail))  # 计算并保存中间结果。
    if text:  # 判断条件是否满足。
        return f"{slot_key}:{text}"  # 返回计算结果给调用方。

    return slot_key  # 返回计算结果给调用方。


def _markable_task_key(params: dict[str, Any], reco_detail: Any) -> str:  # 定义辅助函数，供通告任务流程复用。
    slot_key = _slot_key(params)  # 计算并保存中间结果。
    key = _task_key(params, reco_detail)  # 计算并保存中间结果。
    if key != slot_key:  # 判断条件是否满足。
        return key  # 返回计算结果给调用方。

    return _LAST_TASK_BY_SLOT.get(slot_key, slot_key)  # 返回计算结果给调用方。


def _parse_complete_count(text: str) -> int | None:  # 定义辅助函数，供通告任务流程复用。
    normalized = _normalize_digits(text)  # 计算并保存中间结果。
    match = COUNT_PATTERN.search(normalized)  # 从文本中查找类似 1/3 的次数格式。
    if not match:  # 判断条件是否满足。
        return None  # 返回 None 表示未拿到可用结果。

    return int(match.group(1))  # 返回计算结果给调用方。


def _is_hit(reco_detail: Any) -> bool:  # 定义辅助函数，供通告任务流程复用。
    return bool(reco_detail and getattr(reco_detail, "hit", False))  # 返回计算结果给调用方。


def _take_screenshot(context: Context) -> Any:  # 定义辅助函数，供通告任务流程复用。
    try:  # 尝试执行可能失败的 Maa 调用。
        return context.tasker.controller.post_screencap().wait().get()  # 返回计算结果给调用方。
    except Exception as exc:  # 捕获异常，避免自定义动作直接崩溃。
        print(f"RunAnnouncementTaskLoop screencap failed: {exc!r}")  # 输出调试日志，便于运行时定位流程。
        return None  # 返回 None 表示未拿到可用结果。


def _run_recognition(  # 定义辅助函数，供通告任务流程复用。
    context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
    entry: str,  # 声明数据字段及其类型。
    image: Any,  # 声明数据字段及其类型。
    pipeline_override: dict[str, Any] | None = None,  # 处理空值或缺省情况。
) -> Any:  # 声明返回 Maa 对象或任意结构。
    if image is None:  # 判断条件是否满足。
        return None  # 返回 None 表示未拿到可用结果。

    try:  # 尝试执行可能失败的 Maa 调用。
        return context.run_recognition(entry, image, pipeline_override or {})  # 返回计算结果给调用方。
    except Exception as exc:  # 捕获异常，避免自定义动作直接崩溃。
        print(f"RunAnnouncementTaskLoop recognition {entry!r} failed: {exc!r}")  # 输出调试日志，便于运行时定位流程。
        return None  # 返回 None 表示未拿到可用结果。


def _run_action(  # 定义辅助函数，供通告任务流程复用。
    context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
    entry: str,  # 声明数据字段及其类型。
    pipeline_override: dict[str, Any] | None = None,  # 处理空值或缺省情况。
) -> bool:  # 声明该动作返回布尔结果给 Maa。
    try:  # 尝试执行可能失败的 Maa 调用。
        detail = context.run_action(entry, pipeline_override=pipeline_override or {})  # 调用 Maa 动作节点但不执行后续 next。
    except Exception as exc:  # 捕获异常，避免自定义动作直接崩溃。
        print(f"RunAnnouncementTaskLoop action {entry!r} failed: {exc!r}")  # 输出调试日志，便于运行时定位流程。
        return False  # 向调用方报告本步骤失败或条件不成立。

    return bool(detail and getattr(detail, "success", False))  # 返回计算结果给调用方。


def _ocr_override(node: str, roi: list[int]) -> dict[str, Any]:  # 定义辅助函数，供通告任务流程复用。
    return {  # 返回计算结果给调用方。
        node: {  # 声明数据字段及其类型。
            "recognition": {  # 开始构造字典结构。
                "type": "OCR",  # 指定 pipeline 节点使用的类型。
                "param": {  # 开始构造字典结构。
                    "roi": roi,  # 指定识别区域。
                    "expected": ".+",  # 指定 OCR 期望至少识别到文本。
                    "only_rec": True,  # 要求 OCR 只识别文本而不做额外动作。
                },  # 结束当前多行结构。
            }  # 结束当前多行结构。
        }  # 结束当前多行结构。
    }  # 结束当前多行结构。


def _template_override(node: str, roi: list[int], template: str) -> dict[str, Any]:  # 定义辅助函数，供通告任务流程复用。
    return {  # 返回计算结果给调用方。
        node: {  # 声明数据字段及其类型。
            "recognition": {  # 开始构造字典结构。
                "type": "TemplateMatch",  # 指定 pipeline 节点使用的类型。
                "param": {  # 开始构造字典结构。
                    "roi": roi,  # 指定识别区域。
                    "template": [template],  # 指定模板匹配使用的图片。
                },  # 结束当前多行结构。
            }  # 结束当前多行结构。
        }  # 结束当前多行结构。
    }  # 结束当前多行结构。


def _center_target(rect: list[int]) -> list[int]:  # 定义辅助函数，供通告任务流程复用。
    x, y, width, height = rect  # 执行通告任务自定义动作的一行逻辑。
    return [x + width // 2, y + height // 2]  # 返回计算结果给调用方。


def _click_override(node: str, target: list[int], wait_freezes: int = 300) -> dict[str, Any]:  # 定义辅助函数，供通告任务流程复用。
    return {  # 返回计算结果给调用方。
        node: {  # 声明数据字段及其类型。
            "action": {  # 开始构造字典结构。
                "type": "Click",  # 指定 pipeline 节点使用的类型。
                "param": {  # 开始构造字典结构。
                    "target": target,  # 指定点击目标位置。
                },  # 结束当前多行结构。
            },  # 结束当前多行结构。
            "post_wait_freezes": wait_freezes,  # 动作后等待画面稳定。
        }  # 结束当前多行结构。
    }  # 结束当前多行结构。


def _recognize_template(  # 定义辅助函数，供通告任务流程复用。
    context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
    image: Any,  # 声明数据字段及其类型。
    entry: str,  # 声明数据字段及其类型。
    roi: list[int],  # 声明数据字段及其类型。
    template: str,  # 声明数据字段及其类型。
) -> Any:  # 声明返回 Maa 对象或任意结构。
    return _run_recognition(context, entry, image, _template_override(entry, roi, template))  # 返回计算结果给调用方。


def _recognize_card_text(context: Context, image: Any, slot: AnnouncementSlot) -> Any:  # 定义辅助函数，供通告任务流程复用。
    return _run_recognition(  # 返回计算结果给调用方。
        context,  # 执行通告任务自定义动作的一行逻辑。
        CARD_TEXT_RECO,  # 执行通告任务自定义动作的一行逻辑。
        image,  # 执行通告任务自定义动作的一行逻辑。
        _ocr_override(CARD_TEXT_RECO, slot.card_roi),  # 执行通告任务自定义动作的一行逻辑。
    )  # 结束当前多行结构。


def _remember_slot_task(slot: AnnouncementSlot, reco_detail: Any) -> str:  # 定义辅助函数，供通告任务流程复用。
    params = _slot_params(slot)  # 计算并保存中间结果。
    key = _task_key(params, reco_detail)  # 计算并保存中间结果。
    slot_key = _slot_key(params)  # 计算并保存中间结果。
    if key != slot_key:  # 判断条件是否满足。
        _LAST_TASK_BY_SLOT[slot_key] = key  # 执行通告任务自定义动作的一行逻辑。

    return key  # 返回计算结果给调用方。


def _is_task_skipped(slot: AnnouncementSlot, key: str) -> bool:  # 定义辅助函数，供通告任务流程复用。
    slot_key = _slot_key(_slot_params(slot))  # 计算并保存中间结果。
    return key in _SKIPPED_TASKS or slot_key in _SKIPPED_TASKS  # 返回计算结果给调用方。


def _mark_task_skipped(slot: AnnouncementSlot, key: str, reason: str) -> None:  # 定义辅助函数，供通告任务流程复用。
    fallback = _slot_key(_slot_params(slot))  # 计算并保存中间结果。
    _SKIPPED_TASKS.add(key or fallback)  # 调用对象方法或更新对象状态。
    print(  # 输出调试日志，便于运行时定位流程。
        "RunAnnouncementTaskLoop marked skipped "  # 执行通告任务自定义动作的一行逻辑。
        f"name={slot.name!r}, key={key or fallback!r}, reason={reason!r}"  # 执行通告任务自定义动作的一行逻辑。
    )  # 结束当前多行结构。


def _task_completed_node(task_detail: Any, node_name: str) -> bool:  # 定义辅助函数，供通告任务流程复用。
    try:  # 尝试执行可能失败的 Maa 调用。
        nodes = getattr(task_detail, "nodes", None) or []  # 安全读取对象属性，兼容 Maa 返回结构差异。
    except Exception as exc:  # 捕获异常，避免自定义动作直接崩溃。
        print(f"RunAnnouncementTaskLoop cannot inspect task nodes: {exc!r}")  # 输出调试日志，便于运行时定位流程。
        return False  # 向调用方报告本步骤失败或条件不成立。

    for node in nodes:  # 遍历候选结果或槽位。
        if getattr(node, "name", None) == node_name and getattr(node, "completed", False):  # 判断条件是否满足。
            return True  # 向调用方报告本步骤成功或条件成立。

    return False  # 向调用方报告本步骤失败或条件不成立。


def _submit_failure_reason(task_detail: Any) -> str:  # 定义辅助函数，供通告任务流程复用。
    if task_detail is None:  # 判断条件是否满足。
        return "submit_flow_failed"  # 返回计算结果给调用方。

    if _task_completed_node(task_detail, SUBMIT_WINDOW_CLOSE_NODE):  # 判断条件是否满足。
        return "no_item"  # 返回计算结果给调用方。

    status = getattr(task_detail, "status", None)  # 安全读取对象属性，兼容 Maa 返回结构差异。
    if getattr(status, "failed", False):  # 判断条件是否满足。
        return "submit_flow_failed"  # 返回计算结果给调用方。

    return "not_enough"  # 返回计算结果给调用方。


def _check_complete_limit(context: Context, limit: int) -> bool:  # 定义辅助函数，供通告任务流程复用。
    image = _take_screenshot(context)  # 获取当前画面截图。
    reco_detail = _run_recognition(context, COMPLETE_LIMIT_RECO, image)  # 通过统一封装执行识别并处理失败。
    for text in _iter_ocr_texts(reco_detail):  # 遍历候选结果或槽位。
        current = _parse_complete_count(text)  # 计算并保存中间结果。
        if current is None:  # 判断条件是否满足。
            continue  # 跳过本轮循环，继续检查下一个候选项。

        result = current >= limit  # 计算并保存中间结果。
        print(  # 输出调试日志，便于运行时定位流程。
            "RunAnnouncementTaskLoop complete count "  # 执行通告任务自定义动作的一行逻辑。
            f"text={text!r}, current={current}, limit={limit}, result={result}"  # 执行通告任务自定义动作的一行逻辑。
        )  # 结束当前多行结构。
        return result  # 返回计算结果给调用方。

    print("RunAnnouncementTaskLoop found no valid complete count.")  # 输出调试日志，便于运行时定位流程。
    return False  # 向调用方报告本步骤失败或条件不成立。


def _go_first_page(context: Context) -> None:  # 定义辅助函数，供通告任务流程复用。
    _run_action(context, BACK_TO_FIRST_ACTION)  # 通过统一封装执行动作并处理失败。


def _go_second_page(context: Context) -> None:  # 定义辅助函数，供通告任务流程复用。
    _run_action(context, SWIPE_TO_SECOND_ACTION)  # 通过统一封装执行动作并处理失败。


def _click_slot_button(context: Context, entry: str, slot: AnnouncementSlot) -> bool:  # 定义辅助函数，供通告任务流程复用。
    wait_freezes = 500 if entry == CLAIM_CLICK_ACTION else 300  # 计算并保存中间结果。
    return _run_action(  # 返回计算结果给调用方。
        context,  # 执行通告任务自定义动作的一行逻辑。
        entry,  # 执行通告任务自定义动作的一行逻辑。
        _click_override(entry, _center_target(slot.button_roi), wait_freezes),  # 生成点击动作的 pipeline 覆盖参数。
    )  # 结束当前多行结构。


def _try_close_submit_window(context: Context) -> None:  # 定义辅助函数，供通告任务流程复用。
    image = _take_screenshot(context)  # 获取当前画面截图。
    close_reco = _run_recognition(context, SUBMIT_WINDOW_CLOSE_RECO, image)  # 通过统一封装执行识别并处理失败。
    if not _is_hit(close_reco):  # 判断条件是否满足。
        return  # 执行通告任务自定义动作的一行逻辑。

    print("RunAnnouncementTaskLoop closing leftover submit window.")  # 输出调试日志，便于运行时定位流程。
    box = getattr(close_reco, "box", None)  # 安全读取对象属性，兼容 Maa 返回结构差异。
    try:  # 尝试执行可能失败的 Maa 调用。
        if box is None:  # 判断条件是否满足。
            _run_action(context, SUBMIT_WINDOW_CLOSE_ACTION)  # 通过统一封装执行动作并处理失败。
        else:  # 处理前面条件都不满足的情况。
            context.run_action(SUBMIT_WINDOW_CLOSE_ACTION, box)  # 调用 Maa 动作节点但不执行后续 next。
    except Exception as exc:  # 捕获异常，避免自定义动作直接崩溃。
        print(f"RunAnnouncementTaskLoop close fallback failed: {exc!r}")  # 输出调试日志，便于运行时定位流程。


def _claim_first_available(context: Context, slots: tuple[AnnouncementSlot, ...]) -> bool:  # 定义辅助函数，供通告任务流程复用。
    image = _take_screenshot(context)  # 获取当前画面截图。
    for slot in slots:  # 遍历候选结果或槽位。
        claim_reco = _recognize_template(  # 开始多行调用或元组定义。
            context,  # 执行通告任务自定义动作的一行逻辑。
            image,  # 执行通告任务自定义动作的一行逻辑。
            CLAIM_RECO,  # 执行通告任务自定义动作的一行逻辑。
            slot.button_roi,  # 调用对象方法或更新对象状态。
            CLAIM_TEMPLATE,  # 执行通告任务自定义动作的一行逻辑。
        )  # 结束当前多行结构。
        if not _is_hit(claim_reco):  # 判断条件是否满足。
            continue  # 跳过本轮循环，继续检查下一个候选项。

        if _click_slot_button(context, CLAIM_CLICK_ACTION, slot):  # 判断条件是否满足。
            print(f"RunAnnouncementTaskLoop claimed {slot.name}.")  # 输出调试日志，便于运行时定位流程。
            return True  # 向调用方报告本步骤成功或条件成立。

        print(f"RunAnnouncementTaskLoop failed to click claim for {slot.name}.")  # 输出调试日志，便于运行时定位流程。

    return False  # 向调用方报告本步骤失败或条件不成立。


def _claim_all_available(context: Context, slots: tuple[AnnouncementSlot, ...]) -> int:  # 领取当前页面所有已经完成的通告任务。
    claimed = 0  # 记录当前页面成功领取的任务数量。
    for _ in range(len(slots)):  # 最多按当前页面槽位数尝试，避免识别异常导致无限循环。
        if not _claim_first_available(context, slots):  # 每次重新截图，只领取当前画面中第一个可领取任务。
            break  # 当前页面没有可领取任务或点击失败时结束本页预扫。
        claimed += 1  # 成功领取后累计数量，并在下一轮重新截图识别。

    return claimed  # 返回当前页面实际领取数量供日志记录。


def _claim_initial_available(context: Context) -> None:  # 在主循环开始前预扫两页并领取已有奖励。
    print("RunAnnouncementTaskLoop initial claim scan started.")  # 输出开场领取预扫开始日志。
    _go_first_page(context)  # 先向右滑动，确保通告任务列表回到第一页。
    first_claimed = _claim_all_available(context, FIRST_PAGE_SLOTS)  # 领取第一页两个槽位中所有可领取任务。
    _go_second_page(context)  # 再向左滑动，进入通告任务第二页。
    second_claimed = _claim_all_available(context, SECOND_PAGE_SLOTS)  # 领取第二页两个槽位中所有可领取任务。
    print(  # 输出本次开场预扫的领取统计。
        "RunAnnouncementTaskLoop initial claim scan finished "  # 说明开场领取预扫已经结束。
        f"first_page={first_claimed}, second_page={second_claimed}"  # 记录两页分别领取的任务数量。
    )  # 结束日志输出。


def _try_submit_first_available(context: Context, slots: tuple[AnnouncementSlot, ...]) -> bool:  # 定义辅助函数，供通告任务流程复用。
    image = _take_screenshot(context)  # 获取当前画面截图。
    for slot in slots:  # 遍历候选结果或槽位。
        card_reco = _recognize_card_text(context, image, slot)  # 计算并保存中间结果。
        task_key = _remember_slot_task(slot, card_reco)  # 计算并保存中间结果。
        if _is_task_skipped(slot, task_key):  # 判断条件是否满足。
            print(f"RunAnnouncementTaskLoop skipped cached task {slot.name}: {task_key!r}")  # 输出调试日志，便于运行时定位流程。
            continue  # 跳过本轮循环，继续检查下一个候选项。

        submit_reco = _recognize_template(  # 开始多行调用或元组定义。
            context,  # 执行通告任务自定义动作的一行逻辑。
            image,  # 执行通告任务自定义动作的一行逻辑。
            SUBMIT_RECO,  # 执行通告任务自定义动作的一行逻辑。
            slot.button_roi,  # 调用对象方法或更新对象状态。
            SUBMIT_TEMPLATE,  # 执行通告任务自定义动作的一行逻辑。
        )  # 结束当前多行结构。
        if not _is_hit(submit_reco):  # 判断条件是否满足。
            continue  # 跳过本轮循环，继续检查下一个候选项。

        print(f"RunAnnouncementTaskLoop submitting {slot.name}: {task_key!r}")  # 输出调试日志，便于运行时定位流程。
        if not _click_slot_button(context, SUBMIT_CLICK_ACTION, slot):  # 判断条件是否满足。
            _mark_task_skipped(slot, task_key, "submit_click_failed")  # 记录当前任务应跳过，避免重复尝试。
            return True  # 向调用方报告本步骤成功或条件成立。

        try:  # 尝试执行可能失败的 Maa 调用。
            submit_task = context.run_task(SUBMIT_WINDOW_TASK)  # 调用 Maa 子任务，执行提交窗口 pipeline 流程。
        except Exception as exc:  # 捕获异常，避免自定义动作直接崩溃。
            print(f"RunAnnouncementTaskLoop submit subtask failed: {exc!r}")  # 输出调试日志，便于运行时定位流程。
            submit_task = None  # 处理空值或缺省情况。

        _try_close_submit_window(context)  # 尝试关闭可能残留的提交窗口。

        after_image = _take_screenshot(context)  # 获取当前画面截图。
        claim_reco = _recognize_template(  # 开始多行调用或元组定义。
            context,  # 执行通告任务自定义动作的一行逻辑。
            after_image,  # 执行通告任务自定义动作的一行逻辑。
            CLAIM_RECO,  # 执行通告任务自定义动作的一行逻辑。
            slot.button_roi,  # 调用对象方法或更新对象状态。
            CLAIM_TEMPLATE,  # 执行通告任务自定义动作的一行逻辑。
        )  # 结束当前多行结构。
        if _is_hit(claim_reco):  # 判断条件是否满足。
            if _click_slot_button(context, CLAIM_CLICK_ACTION, slot):  # 判断条件是否满足。
                print(f"RunAnnouncementTaskLoop submitted and claimed {slot.name}.")  # 输出调试日志，便于运行时定位流程。
                return True  # 向调用方报告本步骤成功或条件成立。

            print(f"RunAnnouncementTaskLoop submit succeeded but claim click failed for {slot.name}.")  # 输出调试日志，便于运行时定位流程。
            return True  # 向调用方报告本步骤成功或条件成立。

        _mark_task_skipped(slot, task_key, _submit_failure_reason(submit_task))  # 记录当前任务应跳过，避免重复尝试。
        return True  # 向调用方报告本步骤成功或条件成立。

    return False  # 向调用方报告本步骤失败或条件不成立。


@AgentServer.custom_action("CheckAnnouncementCompleteLimit")  # 把下面的类注册为 Maa 可调用的 Custom Action。
class CheckAnnouncementCompleteLimit(CustomAction):  # 定义一个类，封装相关数据或自定义动作。
    def run(  # 定义辅助函数，供通告任务流程复用。
        self,  # 接收当前 CustomAction 实例。
        context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
        argv: CustomAction.RunArg,  # 接收 Maa 传入的自定义动作运行参数。
    ) -> bool:  # 声明该动作返回布尔结果给 Maa。
        params = _parse_params(argv.custom_action_param)  # 计算并保存中间结果。
        limit = int(params.get("limit", 3))  # 读取或传递完成次数上限。

        for text in _iter_ocr_texts(argv.reco_detail):  # 遍历候选结果或槽位。
            current = _parse_complete_count(text)  # 计算并保存中间结果。
            if current is None:  # 判断条件是否满足。
                continue  # 跳过本轮循环，继续检查下一个候选项。

            result = current >= limit  # 计算并保存中间结果。
            print(  # 输出调试日志，便于运行时定位流程。
                "CheckAnnouncementCompleteLimit "  # 执行通告任务自定义动作的一行逻辑。
                f"text={text!r}, current={current}, limit={limit}, result={result}"  # 执行通告任务自定义动作的一行逻辑。
            )  # 结束当前多行结构。
            return result  # 返回计算结果给调用方。

        print("CheckAnnouncementCompleteLimit found no valid progress text.")  # 输出调试日志，便于运行时定位流程。
        return False  # 向调用方报告本步骤失败或条件不成立。


@AgentServer.custom_action("CheckAnnouncementSkipped")  # 把下面的类注册为 Maa 可调用的 Custom Action。
class CheckAnnouncementSkipped(CustomAction):  # 定义一个类，封装相关数据或自定义动作。
    def run(  # 定义辅助函数，供通告任务流程复用。
        self,  # 接收当前 CustomAction 实例。
        context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
        argv: CustomAction.RunArg,  # 接收 Maa 传入的自定义动作运行参数。
    ) -> bool:  # 声明该动作返回布尔结果给 Maa。
        params = _parse_params(argv.custom_action_param)  # 计算并保存中间结果。
        key = _task_key(params, argv.reco_detail)  # 计算并保存中间结果。
        slot_key = _slot_key(params)  # 计算并保存中间结果。
        if key != slot_key:  # 判断条件是否满足。
            _LAST_TASK_BY_SLOT[slot_key] = key  # 执行通告任务自定义动作的一行逻辑。

        result = key not in _SKIPPED_TASKS and slot_key not in _SKIPPED_TASKS  # 计算并保存中间结果。
        print(f"CheckAnnouncementSkipped key={key!r}, result={result}")  # 输出调试日志，便于运行时定位流程。
        return result  # 返回计算结果给调用方。


@AgentServer.custom_action("MarkAnnouncementSkipped")  # 把下面的类注册为 Maa 可调用的 Custom Action。
class MarkAnnouncementSkipped(CustomAction):  # 定义一个类，封装相关数据或自定义动作。
    def run(  # 定义辅助函数，供通告任务流程复用。
        self,  # 接收当前 CustomAction 实例。
        context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
        argv: CustomAction.RunArg,  # 接收 Maa 传入的自定义动作运行参数。
    ) -> bool:  # 声明该动作返回布尔结果给 Maa。
        params = _parse_params(argv.custom_action_param)  # 计算并保存中间结果。
        key = _markable_task_key(params, argv.reco_detail)  # 计算并保存中间结果。
        reason = params.get("reason", "unknown")  # 记录跳过该任务的原因。
        _SKIPPED_TASKS.add(key)  # 调用对象方法或更新对象状态。
        print(f"MarkAnnouncementSkipped key={key!r}, reason={reason!r}")  # 输出调试日志，便于运行时定位流程。
        return True  # 向调用方报告本步骤成功或条件成立。


@AgentServer.custom_action("ResetAnnouncementSkipped")  # 把下面的类注册为 Maa 可调用的 Custom Action。
class ResetAnnouncementSkipped(CustomAction):  # 定义一个类，封装相关数据或自定义动作。
    def run(  # 定义辅助函数，供通告任务流程复用。
        self,  # 接收当前 CustomAction 实例。
        context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
        argv: CustomAction.RunArg,  # 接收 Maa 传入的自定义动作运行参数。
    ) -> bool:  # 声明该动作返回布尔结果给 Maa。
        _SKIPPED_TASKS.clear()  # 调用对象方法或更新对象状态。
        _LAST_TASK_BY_SLOT.clear()  # 调用对象方法或更新对象状态。
        print("ResetAnnouncementSkipped cleared skipped task state.")  # 输出调试日志，便于运行时定位流程。
        return True  # 向调用方报告本步骤成功或条件成立。


@AgentServer.custom_action("RunAnnouncementTaskLoop")  # 把下面的类注册为 Maa 可调用的 Custom Action。
class RunAnnouncementTaskLoop(CustomAction):  # 定义一个类，封装相关数据或自定义动作。
    def run(  # 定义辅助函数，供通告任务流程复用。
        self,  # 接收当前 CustomAction 实例。
        context: Context,  # 接收 Maa 上下文，用于截图、识别、动作和子任务。
        argv: CustomAction.RunArg,  # 接收 Maa 传入的自定义动作运行参数。
    ) -> bool:  # 声明该动作返回布尔结果给 Maa。
        params = _parse_params(argv.custom_action_param)  # 计算并保存中间结果。
        limit = int(params.get("limit", 3))  # 读取或传递完成次数上限。
        max_rounds = int(params.get("max_rounds", 30))  # 读取最大循环轮数，防止无限循环。

        _SKIPPED_TASKS.clear()  # 调用对象方法或更新对象状态。
        _LAST_TASK_BY_SLOT.clear()  # 调用对象方法或更新对象状态。
        print("RunAnnouncementTaskLoop started.")  # 输出调试日志，便于运行时定位流程。
        _claim_initial_available(context)  # 清空本轮缓存后只执行一次两页领取预扫。

        for round_index in range(1, max_rounds + 1):  # 遍历候选结果或槽位。
            print(f"RunAnnouncementTaskLoop round={round_index}")  # 输出调试日志，便于运行时定位流程。
            _go_first_page(context)  # 滑回通告任务第一页。
            if _check_complete_limit(context, limit):  # 判断条件是否满足。
                print("RunAnnouncementTaskLoop reached complete limit.")  # 输出调试日志，便于运行时定位流程。
                return True  # 向调用方报告本步骤成功或条件成立。

            if _claim_first_available(context, FIRST_PAGE_SLOTS):  # 判断条件是否满足。
                continue  # 跳过本轮循环，继续检查下一个候选项。

            if _try_submit_first_available(context, FIRST_PAGE_SLOTS):  # 判断条件是否满足。
                continue  # 跳过本轮循环，继续检查下一个候选项。

            _go_second_page(context)  # 滑到通告任务第二页。
            if _claim_first_available(context, SECOND_PAGE_SLOTS):  # 判断条件是否满足。
                continue  # 跳过本轮循环，继续检查下一个候选项。

            if _try_submit_first_available(context, SECOND_PAGE_SLOTS):  # 判断条件是否满足。
                continue  # 跳过本轮循环，继续检查下一个候选项。

            print("RunAnnouncementTaskLoop found no actionable announcement task.")  # 输出调试日志，便于运行时定位流程。
            return True  # 向调用方报告本步骤成功或条件成立。

        print(f"RunAnnouncementTaskLoop reached max_rounds={max_rounds}.")  # 输出调试日志，便于运行时定位流程。
        return True  # 向调用方报告本步骤成功或条件成立。
