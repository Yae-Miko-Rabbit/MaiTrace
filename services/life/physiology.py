"""基础身体需要与逐步恢复；数值只由时间、已有活动及显式周期配置驱动。"""

from datetime import date, datetime
from typing import Any, Dict, Optional
import math

from .config import MenstrualSection
from .models import LifeState


def clamp(value: float) -> float:
    return max(0.0, min(100.0, value))


def update_cycle(state: LifeState, moment: datetime, config: Optional[MenstrualSection]) -> None:
    if config is None or not config.enabled:
        state.menstrual_phase, state.menstrual_cycle_day, state.menstrual_discomfort = "disabled", 0, 0.0
        return
    elapsed = (moment.date() - date.fromisoformat(config.last_period_start)).days
    if elapsed < 0:
        state.menstrual_phase, state.menstrual_cycle_day, state.menstrual_discomfort = "waiting", 0, 0.0
        return
    day = elapsed % config.cycle_days
    state.menstrual_cycle_day = day + 1
    if day < config.period_days:
        state.menstrual_phase = "period"
        # 次日可更明显，后续逐渐减轻；无不适的配置不会制造疼痛。
        factor = 0.7 if day == 0 else max(0.15, 1.0 - (day - 1) / max(1, config.period_days - 1))
    elif day < config.period_days + 2:
        state.menstrual_phase = "recovery"
        factor = 0.1 * (config.period_days + 2 - day)
    elif day >= config.cycle_days - 3:
        state.menstrual_phase = "premenstrual"
        factor = 0.15
    else:
        state.menstrual_phase, factor = "ordinary", 0.0
    state.menstrual_discomfort = config.symptom_level * factor


def advance_body(state: LifeState, hours: float, kind: str, sleeping: bool) -> None:
    """随活动累计需求；不适在诱因缓解后渐退，进食/喝水不瞬间治愈。"""
    state.thirst = clamp(state.thirst + (1.5 if sleeping else 12 if kind == "exercise" else 7) * hours)
    fatigue_rate = (-9 if sleeping else {
        "exercise": 8, "chores": 3, "travel": 2, "work": 1.2, "study": 0.7,
        "rest": -5, "leisure": -0.5, "meal": -1,
    }.get(kind, 0.5))
    state.fatigue = clamp(state.fatigue + fatigue_rate * hours)
    state.sleep_pressure = clamp(state.sleep_pressure + (-10 if sleeping else 4.5) * hours)
    state.hygiene_need = clamp(state.hygiene_need + (0.5 if sleeping else 5 if kind == "exercise" else 2.2) * hours)
    burden = max(
        max(0.0, 25 - state.energy), max(0.0, state.hunger - 80),
        max(0.0, state.thirst - 75), max(0.0, state.fatigue - 65),
        max(0.0, state.sleep_pressure - 75), state.menstrual_discomfort,
    )
    previous = state.discomfort
    # 指数收敛避免轮询次数影响恢复速度；短时休息不会直接抹掉持续不适。
    rate = 0.8 if burden >= previous else 0.35 if sleeping or kind == "rest" else 0.15
    state.discomfort = clamp(burden + (previous - burden) * math.exp(-rate * hours))
    state.recovery_status = ("recovering" if state.discomfort > burden + 1 and state.discomfort >= 5
                             else "discomfort" if state.discomfort >= 5 else "well")


def complete_care(state: LifeState, kind: str, parameters: Dict[str, Any]) -> None:
    # 小动作可合并进餐或洗漱，只接受明确结构标记，不从“想喝水”之类描述臆造完成。
    actions = parameters.get("care_actions", [])
    actions = set(actions) if isinstance(actions, list) and all(isinstance(item, str) for item in actions) else set()
    if kind == "meal":
        state.thirst = clamp(state.thirst - 12)
    if kind == "hydration" or "drink" in actions:
        state.thirst = clamp(state.thirst - 65)
    if kind == "hygiene" or "wash" in actions:
        state.hygiene_need = clamp(state.hygiene_need - 75)


def health_summary(state: LifeState) -> None:
    notes = []
    if state.energy < 20 or state.fatigue >= 65:
        notes.append("身体疲惫，需要减少负荷")
    if state.hunger > 80:
        notes.append("有些饿，需要进餐")
    if state.thirst > 75:
        notes.append("有些口渴，需要补水")
    if state.sleep_pressure >= 75:
        notes.append("困意明显，需要睡眠")
    if state.hygiene_need >= 65:
        notes.append("该安排洗漱了")
    if state.menstrual_discomfort >= 5:
        notes.append("经期相关的轻微不适" if state.menstrual_discomfort < 40 else "经期不适，需要照护和休息")
    if state.recovery_status == "recovering":
        notes.append("不适正在缓解，还需慢慢恢复")
    elif state.discomfort >= 5:
        notes.append("有些身体不适")
    state.health_status = ("recovering" if state.recovery_status == "recovering" else
                           "mild_discomfort" if state.discomfort >= 5 or state.hunger > 88 or state.thirst > 85 else
                           "tired" if state.energy < 20 or state.fatigue >= 65 or state.sleep_pressure >= 75 else "normal")
    state.health_note = "；".join(notes) if notes else "状态正常"
