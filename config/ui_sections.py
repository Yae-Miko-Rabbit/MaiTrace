"""将 WebUI 无法编辑的嵌套配置迁移为独立配置区，保留用户设置。"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Dict, Tuple

from .schedule_image import migrate_schedule_image_config


def migrate_life_menstrual_config(config_data: Mapping[str, Any]) -> Tuple[Dict[str, Any], bool]:
    config = dict(config_data)
    life = config.get('life')
    if not isinstance(life, Mapping) or 'menstrual' not in life:
        return config, False
    old_menstrual = life['menstrual']
    new_menstrual = config.get('life_menstrual', {})
    if not isinstance(old_menstrual, Mapping):
        raise ValueError('旧 [life.menstrual] 必须是配置对象，请勿填写 [object Object] 文本')
    if not isinstance(new_menstrual, Mapping):
        raise ValueError('[life_menstrual] 必须是配置对象')
    config['life'] = {key: value for key, value in life.items() if key != 'menstrual'}
    config['life_menstrual'] = {**old_menstrual, **new_menstrual}
    return config, True


def migrate_ui_sections_config(config_data: Mapping[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """宿主裁剪旧字段前及直接加载配置时使用相同的迁移规则。"""
    config, image_changed = migrate_schedule_image_config(config_data)
    config, menstrual_changed = migrate_life_menstrual_config(config)
    return config, image_changed or menstrual_changed
