"""MaiTrace v6 配置模型，按功能模块分段。

SDK 负责合并默认配置；这里只定义模板，不读取或改写实际 config.toml。
"""

from collections.abc import Mapping
from typing import Any

from maibot_sdk import Field, PluginConfigBase
from pydantic import model_validator

from .sections_proactive import RoutineSection
from .sections_qzone import ImageSection, LLMSection, MonitorSection, PersonaSection, PluginSection, ReadSection, SendSection
from .ui_sections import migrate_ui_sections_config
from ..services.life.config import EnvironmentSection, LifeSection, MenstrualSection, MessagingSection
from ..services.schedule.config import GoalCleanupSection, InjectSection, ScheduleImageSection, ScheduleSection


class MaiTracePluginConfig(PluginConfigBase):
    """MaiTrace 顶层配置。"""

    plugin: PluginSection = Field(default_factory=PluginSection)
    persona: PersonaSection = Field(default_factory=PersonaSection)
    llm: LLMSection = Field(default_factory=LLMSection)
    schedule: ScheduleSection = Field(default_factory=ScheduleSection)
    schedule_image: ScheduleImageSection = Field(default_factory=ScheduleImageSection)
    inject: InjectSection = Field(default_factory=InjectSection)
    goal_cleanup: GoalCleanupSection = Field(default_factory=GoalCleanupSection)
    life: LifeSection = Field(default_factory=LifeSection)
    life_menstrual: MenstrualSection = Field(
        default_factory=MenstrualSection,
        description='角色自身的可选月经周期；默认关闭，不根据性别自动启用，内置模式按配置日期持续模拟。',
    )
    environment: EnvironmentSection = Field(default_factory=EnvironmentSection)
    messaging: MessagingSection = Field(default_factory=MessagingSection)
    send: SendSection = Field(default_factory=SendSection)
    image: ImageSection = Field(default_factory=ImageSection)
    read: ReadSection = Field(default_factory=ReadSection)
    monitor: MonitorSection = Field(default_factory=MonitorSection)
    routine: RoutineSection = Field(default_factory=RoutineSection)

    @model_validator(mode='before')
    @classmethod
    def migrate_ui_sections(cls, value: Any) -> Any:
        if isinstance(value, Mapping):
            return migrate_ui_sections_config(value)[0]
        return value

    @model_validator(mode='after')
    def validate_life_provider(self) -> 'MaiTracePluginConfig':
        if self.life.provider == 'maibot-community.mai-life' and self.schedule.provider != self.life.provider:
            raise ValueError('使用麦生活状态时，日程来源也必须选择麦生活')
        return self
