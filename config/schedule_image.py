"""日程图片配置的结构升级；保留旧嵌套配置及用户已编辑的新字段。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Tuple


def migrate_schedule_image_config(config_data: Mapping[str, Any]) -> Tuple[Dict[str, Any], bool]:
    config = dict(config_data)
    schedule = config.get('schedule')
    if not isinstance(schedule, Mapping) or 'image' not in schedule:
        return config, False
    old_image = schedule['image']
    new_image = config.get('schedule_image', {})
    if not isinstance(old_image, Mapping):
        raise ValueError('旧 [schedule.image] 必须是配置对象，请勿填写 [object Object] 文本')
    if not isinstance(new_image, Mapping):
        raise ValueError('[schedule_image] 必须是配置对象')
    config['schedule'] = {key: value for key, value in schedule.items() if key != 'image'}
    config['schedule_image'] = {**old_image, **new_image}
    return config, True
