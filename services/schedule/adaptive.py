"""仅在内置日程真实空档中补充需要，不移动已有活动或约定。"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .planner.goal_manager import GoalStatus
from .query import _extract_time_window
from .utils.time_utils import parse_time_window


class AdaptiveSchedule:
    def __init__(self, plugin: Any) -> None:
        self.plugin = plugin

    async def patrol(self) -> Optional[Dict[str, Any]]:
        plugin, cfg = self.plugin, self.plugin.config.schedule
        life, schedule = plugin.life_engine, plugin.schedule_engine
        if not cfg.enabled or not cfg.adaptive_enabled or cfg.provider != 'internal' or life is None or not life.started:
            return None
        state = life.peek_state()
        if not state.get('enabled') or state.get('activity_kind') == 'sleep' or state.get('sleep_phase') in {'falling_asleep', 'light_sleep', 'deep_sleep'}:
            return None
        now = schedule.timezone_manager.get_now()
        previous = await life.store.get_value('adaptive.last')
        if previous and now.timestamp() - previous['at'] < cfg.adaptive_interval_minutes * 60:
            return None
        async with schedule.mutation_lock, life._experience_lock:
            previous = await life.store.get_value('adaptive.last')
            if previous and now.timestamp() - previous['at'] < cfg.adaptive_interval_minutes * 60:
                return None
            candidate = None
            if state.get('thirst', 0) >= 80:
                title, kind, minutes = '喝水，缓解口渴', 'hydration', 15
            elif state['hunger'] >= 80:
                title, kind, minutes = '吃点东西，缓解饥饿', 'meal', 30
            elif state.get('sleep_pressure', 0) >= 85:
                title, kind, minutes = '小睡片刻，缓解困意', 'sleep', 30
            elif state.get('fatigue', 0) >= 70 or state.get('discomfort', 0) >= 30:
                title, kind, minutes = '减轻负担，休息恢复', 'rest', 30
            elif state['energy'] <= 25:
                title, kind, minutes = '休息一会儿，恢复精力', 'rest', 30
            elif state.get('hygiene_need', 0) >= 75:
                title, kind, minutes = '洗漱，整理一下自己', 'hygiene', 15
            else:
                for cached in life.continuity.unfinished(include_scheduled=True):
                    record = await life.store.get_experience(cached['id'], '')
                    if record is None or record['status'] != 'unfinished':
                        continue
                    if record.get('continued_by'):
                        goal = await schedule.run_db(schedule.goal_manager.get_goal, record['continued_by'])
                        # 删除或取消的接续活动可再安排；已结束活动先等待结果结算。
                        if goal is not None and goal.status in {GoalStatus.ACTIVE, GoalStatus.COMPLETED}:
                            continue
                    candidate = record
                    break
                if candidate is None:
                    return None
                title, kind, minutes = candidate['continuation'], candidate['kind'], 30
            created = await schedule.run_db(self._insert, schedule, now, title, kind, minutes, candidate)
            if created is None:
                return None
            # 写入日程成功后立即记录冷却；已写日程本身也参与空档检查。
            await life.store.set_value('adaptive.last', {'at': now.timestamp(), 'goal_id': created['goal_id']})
            if candidate:
                candidate.update(continued_by=created['goal_id'], updated_at=now.timestamp())
                await life.store.save_experience(candidate)
                await life.continuity.refresh()
            await schedule.refresh(force=True)
        return created

    @staticmethod
    def _insert(schedule: Any, now: datetime, title: str, kind: str, minutes: int,
                candidate: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        manager = schedule.goal_manager
        start = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        boundary = midnight + timedelta(days=1)
        with manager.db._transaction():
            goals = manager.get_all_goals(chat_id='global')
            if candidate and any(goal.parameters.get('continuation_id') == candidate['id']
                                 and goal.status in {GoalStatus.ACTIVE, GoalStatus.COMPLETED} for goal in goals):
                return None
            for goal in goals:
                window = _extract_time_window(goal)
                if window is None or goal.created_at is None or goal.status not in {GoalStatus.ACTIVE, GoalStatus.COMPLETED}:
                    continue
                begin, end = parse_time_window(window)
                if begin is None or end is None:
                    raise ValueError(f'日程 {goal.goal_id} 时间窗口无效')
                day = goal.created_at.replace(tzinfo=now.tzinfo) if goal.created_at.tzinfo is None else goal.created_at.astimezone(now.tzinfo)
                day = day.replace(hour=0, minute=0, second=0, microsecond=0)
                left, right = day + timedelta(minutes=begin), day + timedelta(minutes=end)
                if left <= start < right:
                    return None
                if left > start:
                    boundary = min(boundary, left)
            end_at = min(start + timedelta(minutes=minutes), boundary)
            if (end_at - start).total_seconds() < 15 * 60:
                return None
            goal = manager.create_goal(name=title, description=title, goal_type=kind,
                creator_id='maitrace-life', chat_id='global', parameters={
                    'time_window': [int((start-midnight).total_seconds()/60), int((end_at-midnight).total_seconds()/60)],
                    'adaptive': True, 'continuation_id': candidate['id'] if candidate else ''})
            return {'goal_id': goal.goal_id, 'name': goal.name, 'start_at': start.isoformat(), 'end_at': end_at.isoformat()}
