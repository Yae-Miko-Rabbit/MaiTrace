"""只通过麦生活公开 API 读取全局状态与当前场景。"""

from typing import Any, Dict
import asyncio
import math

from .models import LifeState, clean_text

PROVIDER_ID = 'maibot-community.mai-life'


async def read_state(ctx: Any) -> LifeState:
    async def call(name: str) -> Dict[str, Any]:
        async with asyncio.timeout(8):
            result = await ctx.call_capability('api.call', timeout_ms=8000,
                api_name=f'{PROVIDER_ID}.{name}', version='1', args={})
        # SDK 已解包 RPC；这两个 API 直接返回业务对象。
        if not isinstance(result, dict) or not result:
            raise RuntimeError(f'麦生活 {name} 尚未就绪或返回无效对象')
        return result

    raw, context = await asyncio.gather(call('get_life_state'), call('get_current_scene'))
    numbers = {}
    for key, low, high in (('energy', 0, 100), ('hunger', 0, 100), ('mood_valence', -1, 1), ('mood_arousal', 0, 1)):
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f'麦生活状态 {key} 无效')
        numbers[key] = float(value)
    phase = raw.get('sleep_phase')
    if phase not in {'awake', 'woken', 'falling_asleep', 'light_sleep', 'deep_sleep'}:
        raise ValueError('麦生活 sleep_phase 无效')
    timestamp = raw.get('last_updated_at')
    if isinstance(timestamp, bool) or not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp) or timestamp <= 0:
        raise ValueError('麦生活 last_updated_at 无效')
    scene = context.get('scene')
    if scene is not None and not isinstance(scene, dict):
        raise ValueError('麦生活当前场景格式错误')
    return LifeState(**numbers, sleep_phase=phase, last_updated_at=float(timestamp),
        current_activity=clean_text(raw.get('current_activity', '')),
        current_location=clean_text(raw.get('current_location', ''), 120),
        health_status=clean_text(raw.get('health_status', 'normal'), 80),
        health_note=clean_text(raw.get('health_note', ''), 200),
        scene=clean_text((scene or {}).get('scene', ''), 500))
