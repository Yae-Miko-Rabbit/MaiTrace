"""活动时段、结果来源和未完成事项分别保存；查询 Hook 只使用缓存。"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List
import json

from .models import activity_kind, anonymous_text, generate_object, required_text, stable_id


class ContinuityService:
    def __init__(self, engine: Any) -> None:
        self.engine = engine
        self.records: List[Dict[str, Any]] = []

    @staticmethod
    def pending(segments: List[Dict[str, Any]], completed: List[str], now: datetime) -> List[Dict[str, Any]]:
        from .state import LifeStateEngine
        result = []
        for segment in segments:
            key = LifeStateEngine.segment_key(segment)
            if key not in completed:
                continue
            target = str(segment.get('target_stream_id', ''))
            result.append({'id': stable_id('experience', key), 'goal_id': segment['goal_id'],
                'day': segment['end'].date().isoformat(), 'target_stream_id': target,
                'source': 'reported' if target else 'simulated',
                'status': 'awaiting_confirmation' if target else 'pending',
                'activity': segment.get('record_name', segment['name']),
                'description': segment.get('record_description', segment['description']),
                'kind': activity_kind(segment['goal_type'], segment['description'], segment['name']),
                'start_at': segment['start'].isoformat(), 'end_at': segment['end'].isoformat(),
                'continuation_id': str(segment.get('continuation_id', '')),
                'result': '', 'continuation': '', 'importance': 1, 'evidence': '',
                'updated_at': now.timestamp()})
        return result

    async def refresh(self) -> None:
        # 私有记录按已验证会话逐个读取；公共缓存永远不包含私人约定。
        records = await self.engine.store.experiences(limit=30)
        records.extend(await self.engine.store.experiences(status='unfinished', limit=100))
        for user in self.engine._users.values():
            if user['enabled'] and user['stream_id']:
                records.extend(await self.engine.store.experiences(stream_id=user['stream_id'], limit=20))
        self.records = sorted({row['id']: row for row in records}.values(), key=lambda row: row['updated_at'], reverse=True)

    def peek(self, stream_id: str = '') -> List[Dict[str, Any]]:
        if not self.engine.plugin.config.life.outcomes_enabled:
            return []
        return deepcopy([{key: value for key, value in row.items() if key not in {'evidence', 'history', 'actor_user_id', 'source_message_id'}}
            for row in self.records if row['status'] != 'pending' and row['target_stream_id'] in ('', stream_id)][:10])

    def unfinished(self, *, include_scheduled: bool = False) -> List[Dict[str, Any]]:
        if not self.engine.plugin.config.life.outcomes_enabled:
            return []
        return deepcopy([row for row in self.records if not row['target_stream_id']
            and row['status'] == 'unfinished' and row['continuation']
            and (include_scheduled or not row.get('continued_by'))])

    def public_context(self, *, exclude_id: str = '') -> List[Dict[str, Any]]:
        return [{key: row[key] for key in ('activity', 'kind', 'source', 'status', 'result', 'continuation')}
            for row in self.peek() if row['id'] != exclude_id and row['status'] in {'completed', 'unfinished'}]

    async def process(self, now: datetime) -> None:
        if not self.engine.plugin.config.life.outcomes_enabled or self.engine.plugin.config.life.provider != 'internal':
            return
        # 每轮最多生成一个结果，避免大量离线活动挤占场景、日记与日期巡检。
        rows = await self.engine.store.experiences(status='pending', limit=1)
        if rows:
            record = rows[0]
            if record['kind'] in {'sleep', 'meal', 'hydration', 'hygiene'}:
                data = {'status': 'completed', 'result': f"结束了{record['activity']}这段模拟活动。",
                        'continuation': '', 'importance': 1}
            else:
                scenes = await self.engine.store.scenes_for_day(record['day'])
                scenes = [row for row in scenes if row['description'] == record['description']]
                data = await generate_object(self.engine.generator,
                    '以下是角色自身已经结束的模拟活动时段及已有场景。只整理小而具体的模拟结果；'
                    '参考近期结果承接上次进度。相同兴趣和习惯可以重复，写清这次实际推进到哪里；'
                    '平淡或没有明显进展也正常，不必每次都有新发现、感悟、遗憾或待办。'
                    '不得加入用户、重大事件或把约定当成实际完成。未完成时写下一次空档可以接着做的小事。'
                    '返回 JSON：status（completed/unfinished）、result、continuation（完成时空字符串）、'
                    'importance（1到10整数，普通起居1到2，有具体感受或进展3到6，重要成果7到10）。\n'
                    + json.dumps({'activity': record, 'scenes': scenes,
                        'recent_results': self.public_context(exclude_id=record['id'])}, ensure_ascii=False))
            await self.finish(record, data, now, source='simulated')
        await self.refresh()

    async def finish(self, record: Dict[str, Any], data: Dict[str, Any], now: datetime,
                     *, source: str, evidence: str = '') -> None:
        async with self.engine._experience_lock:
            await self._finish(record, data, now, source=source, evidence=evidence)

    async def _finish(self, record: Dict[str, Any], data: Dict[str, Any], now: datetime,
                      *, source: str, evidence: str = '') -> None:
        status = data.get('status')
        importance = data.get('importance', 3)
        if status not in {'completed', 'unfinished'} or type(importance) is not int or not 1 <= importance <= 10:
            raise ValueError('活动结果状态或分享价值无效')
        result = required_text(data.get('result'), 'result', 500)
        continuation = required_text(data.get('continuation'), 'continuation', 240) if status == 'unfinished' else ''
        forbidden = [str(user[field]) for user in self.engine._users.values() for field in ('user_id', 'display_name') if user[field]]
        if not record['target_stream_id']:
            result, continuation = anonymous_text(result, 500, forbidden), anonymous_text(continuation, 240, forbidden)
            if not result or (status == 'unfinished' and not continuation):
                raise ValueError('去身份后的活动结果或接续事项为空')
        updated = {**record, 'source': source, 'status': status, 'result': result,
                   'continuation': continuation, 'importance': importance, 'evidence': evidence,
                   'updated_at': now.timestamp()}
        opportunity = None
        if not record['target_stream_id'] and importance >= 3:
            opportunity = {'source': 'activity_result', 'source_key': record['id'], 'topic': result[:240],
                'motive': f"{record['activity']}有了新的进展", 'privacy': 'public',
                'now': now.timestamp(), 'expires_at': now.timestamp() + 24 * 3600,
                'weight': importance / 10, 'payload': {'result': result, 'source': source, 'status': status,
                    'continuation': continuation, 'importance': importance}}
        resolved = None
        if record.get('continuation_id') and status == 'completed':
            previous = await self.engine.store.get_experience(record['continuation_id'], record['target_stream_id'])
            if previous and previous['target_stream_id'] == record['target_stream_id']:
                previous['history'] = [*previous.get('history', []),
                    {key: previous.get(key) for key in ('source', 'status', 'result', 'updated_at')}][-10:]
                previous['result'] = result
                previous.update(status='completed', continuation='', updated_at=now.timestamp(), continued_by=record['goal_id'])
                resolved = previous
        # 新结果、公开素材和前一次未完成事项一同提交，重启不会留下半结算状态。
        await self.engine.store.save_experience(updated, opportunity=opportunity, resolved=resolved)
        await self.refresh()
