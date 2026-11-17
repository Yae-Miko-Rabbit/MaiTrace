"""面向使用者的配置文案和布局；显示分组仍读写原来的配置路径。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


# 只给 SDK 的原始选项补充中文说明，保留 TOML、校验和跨插件读取使用的原值。
CHOICE_LABELS = {
    'internal': 'MaiTrace 内置', 'maibot-community.mai-life': '麦生活（需安装）',
    'cover': '铺满背景（裁切边缘）', 'contain': '完整显示（可能留白）',
    'top': '靠上', 'center': '居中', 'bottom': '靠下',
    'adapter': '从适配器获取', 'napcat': '通过 OneBot HTTP 获取',
    'clientkey': '从本机 QQ 获取', 'qrcode': '扫码登录', 'local': '使用本地登录缓存',
    'whitelist': '只允许名单内的人', 'blacklist': '排除名单内的人',
    'all': '全部会话', 'today': '今天', 'last_n_hours': '最近几小时',
    'direct': '直接使用聊天片段', 'summary': '先整理成摘要', 'hybrid': '摘要加最近聊天片段',
    'only_ai': '只用 AI 图片', 'only_emoji': '只用表情包',
    'selfie': '角色自拍', 'illustration': '普通画图',
    'auto': '根据活动选择', 'standard': '前置自拍', 'mirror': '对镜自拍', 'photo': '他人拍摄',
    'owner': '主人（可读私人日记）', 'friend': '朋友',
    'sleeping': '睡觉', 'waking_up': '起床', 'eating': '吃饭', 'working': '工作',
    'studying': '学习', 'exercising': '运动', 'relaxing': '休息', 'socializing': '社交',
    'commuting': '出行', 'hobby': '兴趣活动', 'self_care': '照顾自己',
    'cooking': '做饭', 'shopping': '购物', 'gaming': '玩游戏', 'bathing': '洗澡', 'other': '其他',
}


LABELS = {
    'persona.self_description': '补充角色身份和外观',
    'persona.use_multiple_reply_style': '偶尔切换说话风格',
    'plugin.http_host': '空间登录服务地址', 'plugin.http_port': '空间登录服务端口',
    'plugin.http_token': '空间登录服务密钥', 'plugin.cookie_methods': '空间登录方式',
    'plugin.adapter_priority': '优先使用的 QQ 适配器',
    'schedule.adaptive_enabled': '空闲时补充必要的生活活动',
    'schedule.adaptive_interval_minutes': '生活活动调整间隔（分钟）',
    'schedule.inject_schedule': '决定是否聊天时参考生活状态',
    'schedule.inject_into_replyer': '聊天回复时参考生活状态',
    'schedule.auto_generate': '查看日程时自动补生成',
    'schedule.max_future_activities': '聊天背景中显示几个后续活动',
    'schedule.custom_prompt': '日程安排的额外要求',
    'schedule.use_multi_round': '生成不够好时尝试改进',
    'schedule.max_rounds': '最多生成几轮', 'schedule.quality_threshold': '提前结束生成的评分',
    'schedule.min_activities': '每天最少安排几个活动',
    'schedule.max_activities': '每天最多安排几个活动',
    'schedule.enable_detailed_description': '显示活动的详细描述',
    'schedule.min_description_length': '活动描述最少字数',
    'schedule.max_description_length': '活动描述最多字数',
    'schedule.max_tokens': '单轮 AI 输出长度上限（token）',
    'schedule.recent_schedule_days': '参考最近几天的日程',
    'schedule.auto_schedule_enabled': '每天自动生成日程',
    'schedule.auto_schedule_time': '每天几点生成日程',
    'schedule.auto_infer_next_day_prompt': '提前考虑明天的生活安排',
    'schedule.infer_time': '几点考虑明天的安排',
    'schedule.infer_lookback_days': '考虑明天时参考最近几天',
    'schedule.infer_max_prompt_chars': '明日安排建议的最多字数',
    'schedule.infer_use_completion_signal': '参考近期活动的完成情况',
    'schedule.history_message_limit': '安排日程时参考的聊天条数',
    'schedule.knowledge_search_limit': '安排日程时参考的知识条数',
    'schedule.cross_day_activity': '允许活动延续到第二天',
    'schedule.llm_task_name': '日程使用的模型任务',
    'schedule.llm_log_enabled': '保存日程 AI 请求记录',
    'schedule.llm_log_retention_days': '日程 AI 请求记录保留天数',
    'schedule.role_judge_enabled': '让角色按人设决定是否接受约定',
    'schedule.role_judge_temperature': '约定判断的随机程度',
    'schedule.cache_ttl': '日程背景缓存有效期（秒）',
    'schedule.admin_users': '额外限制日程命令的管理员',
    'schedule.allowed_streams': '允许使用日程的聊天',
    'schedule.proactive_streams': '允许日程主动联系的聊天',
    'schedule.enable_proactive_trigger': '约定到时间时提醒',
    'schedule.enable_frequency_modulation': '根据当前活动调整聊天频率',
    'schedule.activity_proactive_enabled': '根据当前日程主动聊天',
    'schedule.activity_proactive_cooldown_minutes': '日程主动聊天最短间隔（分钟）',
    'schedule.activity_proactive_daily_max': '每天最多提交几次日程主动任务',
    'schedule.activity_proactive_quiet_start': '日程主动聊天免打扰开始',
    'schedule.activity_proactive_quiet_end': '日程主动聊天免打扰结束',
    'life.provider': '生活状态由谁提供',
    'life.tick_seconds': '检查新生活内容的间隔（秒）',
    'life.offline_hours': '重启后最多补算几小时的生活',
    'life.initial_energy': '首次使用时的精力', 'life.initial_hunger': '首次使用时的饥饿程度',
    'life.outcomes_enabled': '记住活动结果和没做完的事',
    'life.scene_enabled': '补充正在做的事和生活场景',
    'life.dream_enabled': '睡醒后生成梦境', 'life.diary_enabled': '自动整理每天的生活日记',
    'life.diary_hour': '每天几点开始整理昨天的日记',
    'life.profiles': '可以联系和访问生活内容的人',
    'life.private_proactive_enabled': '允许主动发起生活私聊',
    'life.private_min_interval_minutes': '主动私聊最短间隔（分钟）',
    'life.private_silence_minutes': '对方多久没说话后才主动联系（分钟）',
    'life.private_min_energy': '主动私聊需要的最低精力',
    'life.claim_lease_seconds': '生活内容的发送占用时长（秒）',
    'life.private_pending_seconds': '主动私聊任务最多等待多久（秒）',
    'life.opportunity_retention_days': '过期生活分享内容保留天数',
    'messaging.enabled': '启用生活私聊与消息追踪',
    'messaging.turn_expire_seconds': '消息关联记录保留时间（秒）',
    'messaging.recall_enabled': '撤回消息时取消对应的待发送回复',
    'messaging.wake_probability': '休息时被普通私聊叫醒的概率',
    'messaging.awake_grace_minutes': '被叫醒后可继续聊天的时间（分钟）',
    'inject.enable_intent_classification': '按聊天话题决定是否使用生活背景',
    'inject.enable_state_analysis': '在聊天背景中补充活动进度',
    'inject.enable_inject_optimization': '减少重复加入生活背景',
    'inject.casual_chat_inject_probability': '普通闲聊参考生活背景的概率',
    'inject.context_max_turns': '判断话题延续时保留几轮聊天',
    'inject.context_ttl': '话题延续记录保留时间（秒）',
    'llm.text_model': '空间和生活使用的模型任务', 'llm.show_prompt': '在日志中显示空间 AI 请求内容',
    'send.permission_type': '谁能通过聊天请求发说说', 'send.permission': '发说说权限 QQ 名单',
    'send.prompt': '生成说说的额外写作模板', 'send.history_number': '写说说时参考几条旧动态',
    'send.custom_qqaccount': '直接发说说时读取谁的私聊',
    'send.custom_only_mai': '直接发说说时只用机器人自己的话',
    'send.enable_chat_memory': '写说说时参考聊天内容',
    'send.filter_mode': '哪些聊天可以作为参考', 'send.target_chats': '用于参考的聊天名单',
    'send.include_private_chat_memory': '允许参考私聊内容',
    'send.time_range': '参考哪个时间范围的聊天', 'send.last_hours': '参考最近几小时',
    'send.min_messages': '至少几条聊天才作为参考', 'send.max_messages': '最多参考几条聊天',
    'send.per_message_max_chars': '每条参考聊天最多保留几字',
    'send.chat_memory_mode': '聊天内容怎么整理', 'send.summary_model': '整理聊天摘要的模型任务',
    'send.summary_prompt': '整理聊天摘要的写作模板',
    'send.hybrid_recent_count': '摘要之外保留几条最近聊天',
    'send.fallback_prompt': '没有足够聊天可参考时的补充要求',
    'image.enable_image': '发说说时附带图片', 'image.ai_probability': '随机配图时选择 AI 图片的概率',
    'image.pic_plugin_model': '麦麦绘卷中的模型编号',
    'image.require_image': 'AI 图片失败时停止发布',
    'read.permission_type': '谁能通过聊天请求查看空间', 'read.permission': '查看空间权限 QQ 名单',
    'read.read_number': '每次手动查看几条动态',
    'read.allow_skip_comment': '没什么想说时可以不评论',
    'read.prompt': '评论动态的写作模板', 'read.rt_prompt': '评论转发动态的写作模板',
    'monitor.read_list_type': '自动互动的好友范围', 'monitor.read_list': '自动互动好友 QQ 名单',
    'monitor.silent_hours': '空间互动免打扰时段',
    'monitor.like_during_silent': '免打扰时仍允许点赞',
    'monitor.comment_during_silent': '免打扰时仍允许评论和回复',
    'monitor.self_read_number': '自动回复时检查几条自己的动态',
    'monitor.reply_prompt': '回复自己评论区的写作模板',
    'monitor.reply_to_reply_prompt': '回复好友评论区的写作模板',
    'monitor.processed_feeds_cache_size': '最多记住几条已处理动态',
    'monitor.processed_comments_cache_size': '最多记住几个动态的已回复评论',
    'routine.check_interval_minutes': '多久考虑一次空间活动（分钟）',
    'routine.post_cooldown_minutes': '自动发说说最短间隔（分钟）',
    'routine.browse_cooldown_minutes': '自动刷空间最短间隔（分钟）',
    'routine.respect_silent_hours': '免打扰时暂停自动空间活动',
    'routine.post_blocked_activities': '做哪些事时不自动发说说',
    'routine.browse_blocked_activities': '做哪些事时不自动刷空间',
    'routine.require_reason': '记录 AI 决定空间活动的理由',
    'goal_cleanup.cleanup_interval': '多久清理一次旧日程（秒）',
    'goal_cleanup.cleanup_old_goals_days': '已完成的旧日程保留天数',
}


HINTS = {
    'plugin.enabled': '打开后运行日程、生活和空间功能。关闭后停止整个插件。',
    'plugin.admin_qq': '填写能使用 /zn 命令的 QQ，每人一项。例如 123456789；留空时无人能使用命令。',
    'plugin.cookie_methods': '仅 QQ 空间需要登录。一般保持默认；只用官方机器人聊天时无需配置 OneBot HTTP。',
    'plugin.http_host': '使用 OneBot HTTP 登录空间时才填写。例如 127.0.0.1，不带 http:// 和端口。',
    'plugin.http_port': '填写空间登录服务的 HTTP 端口，例如 9999。只在选择 OneBot HTTP 登录时使用。',
    'plugin.http_token': '登录服务设置了认证密钥才填写，没有设置就留空。',
    'plugin.adapter_priority': '通常留空，自动寻找 QQ 适配器；多个适配器同时使用时才指定顺序。',
    'plugin.config_version': '由插件自动维护，无需填写或修改。',
    'persona.self_description': '可补充身份、外观和生活背景。基础人设仍读取主程序；留空时可使用绘卷的形象描述。',
    'persona.use_multiple_reply_style': '使用主程序已配置的多种说话风格。关闭后始终使用主程序的基础风格。',
    'schedule.enabled': '开启日程读取和聊天参考；内置模式还负责生成日程。关闭后自动空间活动无法参考日程。',
    'schedule.provider': '一般选 MaiTrace 内置。只有安装并启用麦生活后才选择麦生活。',
    'schedule.timezone': '日程和生活统一使用这个时区。中国用户通常保持 Asia/Shanghai。',
    'schedule.auto_schedule_enabled': '每天自动安排当天的生活。当天已有日程时跳过；不会因此发送聊天消息。',
    'schedule.auto_schedule_time': '使用 24 小时制，例如 00:30。启动时如果已过这个时间，也会检查今天的日程。',
    'schedule.auto_generate': '查看今天日程时，缺少日程就补生成。仅内置日程生效；与每天自动生成的开关独立。',
    'schedule.adaptive_enabled': '在真实空档中补充必要的进餐、喝水、休息或没做完的事；保留已有活动。仅内置模式生效。',
    'schedule.adaptive_interval_minutes': '两次补充生活活动至少相隔多久。单位分钟，通常保持默认。',
    'schedule.cross_day_activity': '允许睡眠等活动延续到次日。例如 23:00 到次日 08:30。',
    'schedule.repetition_check_enabled': '比较最近几天的主要活动，发现过于相似时让 AI 复核。吃饭、睡觉和合理接续可以重复。',
    'schedule.custom_prompt': '填写想额外强调的生活要求，例如“最近有点累，多留一些休息时间”。留空使用默认要求。',
    'schedule.min_activities': '每天活动数的下限。必须小于或等于最多活动数；一般保持默认。',
    'schedule.max_activities': '每天活动数的上限。数量越多，日程可能越细碎；一般保持默认。',
    'schedule.enable_detailed_description': '给活动补充具体内容，并在日程和聊天背景中显示。关闭后主要显示活动名称。',
    'schedule.recent_schedule_days': '生成日程时参考最近几天，用于衔接生活和减少重复。通常保留 3 天即可。',
    'schedule.use_multi_round': 'AI 生成不够好时按反馈再尝试。开启可能花费更多时间和模型调用；调整后重载插件。',
    'schedule.max_rounds': '包含第一次生成在内的最多轮数，例如 2 表示最多生成两轮。修改后重载插件。',
    'schedule.quality_threshold': '达到这个评分就结束多轮生成。0.85 表示 85%；通常保持默认。',
    'schedule.max_tokens': '控制单轮日程的 AI 输出长度。通常保持 8192；设得过小可能无法返回完整日程。',
    'schedule.generation_timeout': '日程生成、约定判断和明日安排建议的等待上限。普通日程主动话题最多等 60 秒；修改后重载插件。',
    'schedule.llm_task_name': '填写主程序中的模型任务名，例如 replyer；请使用主程序已经配置好的任务。',
    'schedule.inject_schedule': '让机器人决定是否说话时知道当前生活状态。不会因此强制机器人发消息。',
    'schedule.inject_into_replyer': '让机器人回复时知道当前活动和身体状态；具体是否提及仍由聊天内容决定。',
    'schedule.max_future_activities': '聊天背景里最多补充几个接下来的活动。填 0 只参考当前状态。',
    'schedule.allowed_streams': '留空允许全部聊天。需要限制时每项填一个，如 qq:group:123456 或 qq:private:123456。',
    'schedule.admin_users': '通常留空，沿用开始使用页的管理员 QQ。填写后使用日程命令的人必须同时在两份名单中。',
    'schedule.history_message_limit': '生成日程时最多参考多少条允许范围内的聊天。填 0 不使用聊天参考。',
    'schedule.knowledge_search_limit': '生成日程时最多参考多少条知识库内容。填 0 关闭，通常保持默认。',
    'schedule.auto_infer_next_day_prompt': '提前根据最近的生活整理明天的安排建议；到次日生成时使用，不会提前创建整天日程。',
    'schedule.infer_time': '使用 24 小时制，例如 23:00。只在开启提前考虑明日安排时使用。',
    'schedule.proactive_streams': '每项一个聊天，如 qq:private:123456。留空时不执行日程主动聊天和约定到点提醒。',
    'schedule.enable_proactive_trigger': '在已允许的聊天中提醒到点的约定，不负责安排整天的生活。',
    'schedule.activity_proactive_enabled': '根据当前日程选择话题并主动聊天；需填写允许联系的聊天。与生活主动私聊分别控制。',
    'schedule.activity_proactive_daily_max': '限制每天提交给聊天系统的日程主动任务数。提交不代表已经发送；填 0 关闭。',
    'life.enabled': '让角色的精力、饥饿、心情等状态随生活推进，并提供场景、日记等内容。',
    'life.provider': '通常选择 MaiTrace 内置。使用麦生活状态时，日程提供方也需要选择麦生活。',
    'life.offline_hours': '重启后按已保存的日程补算这段时间的生活状态；没有记录的活动不会补造。单位小时，通常保持默认。',
    'life.initial_energy': '只在第一次创建生活数据库时使用。0 很疲惫，100 精力充足；修改不会重置当前状态。',
    'life.initial_hunger': '只在第一次创建生活数据库时使用。0 不饿，100 很饿；修改不会重置当前状态。',
    'life.outcomes_enabled': '保留自身活动的结果和未完成事项，让之后的生活可以接着做。共同约定需要所在聊天确认。',
    'life.scene_enabled': '根据当前已有活动补充具体生活场景。会调用 AI；关闭后不再生成新场景。',
    'life.dream_enabled': '有睡眠结束记录时生成私人梦境。不会改变睡眠数值，也不会自动公开梦境。',
    'life.diary_enabled': '把昨天的生活场景、梦境和匿名互动整理成私人日记。不会自动发到 QQ 空间。',
    'life.diary_hour': '填写 0–23 的整点，例如 8 表示早上 8 点后整理。有生活内容时每天一篇。',
    'life.profiles': '每人添加一项并填写 QQ。主人可在本人私聊读取私人日记；朋友只能访问自己的和公开的内容。最多一位启用主人。',
    'life.important_dates': '为已添加的人记录生日等日期，例如 2026-12-01。发送提醒还需要允许主动联系。',
    'life.private_proactive_enabled': '允许根据生活内容主动联系。还需开启生活私聊与消息追踪，并在联系人中允许主动私聊。',
    'life.private_min_interval_minutes': '同一人两次生活主动私聊成功发送之间的最短时间。单位分钟，180 表示 3 小时。',
    'life.private_silence_minutes': '对方最近说过话就先等一等。填 15 表示至少等 15 分钟，填 0 不要求等待。',
    'life.private_min_energy': '精力低于这个值时不主动私聊。睡着时仍不会因为降低此值而强行醒来。',
    'life.private_pending_seconds': '主动私聊交给聊天系统后最多等待多久；到期仍未发送会释放占用的生活内容。通常保持默认。',
    'life.claim_lease_seconds': '生活内容交给发送任务后暂时占用多久，用于避免重复发送。通常保持默认。',
    'life.opportunity_retention_days': '过期且未被发送任务占用的分享内容额外保留多久；私人日记、梦境和待确认结果保留。',
    'messaging.enabled': '生活主动私聊、重要日期观察和发送结果确认需要此功能。修改后必须重载插件。',
    'messaging.rest_gate_enabled': '在已配置联系人的私聊中，根据角色睡眠和休息状态决定是否回复。命令仍可使用，群聊由主程序决定。',
    'messaging.wake_probability': '普通私聊在休息时叫醒角色的概率。0.1 表示 10%；明确叫醒或勿扰会另行判断。',
    'messaging.awake_grace_minutes': '被叫醒且回复发送成功后，允许继续聊多久。单位分钟；明确勿扰仍优先处理。',
    'messaging.recall_enabled': '你撤回消息后，取消对应的尚未发送的回复；已经发出的回复会保留。',
    'messaging.turn_expire_seconds': '暂时记住源消息与回复的关联，便于处理撤回。通常保持默认。',
    'llm.text_model': '填写主程序已有的模型任务名，例如 replyer 或 utils。用于空间文案和生活内容，日程模型另行设置。',
    'llm.llm_timeout_seconds': '空间、生活内容及聊天摘要每次请求 AI 的等待上限。单位秒；修改后重载插件。',
    'llm.show_prompt': '排查空间文案问题时开启，日志会显示完整 AI 请求内容。日常使用可关闭。',
    'schedule_image.background_path': '填写本地图片位置，例如 images/background.jpg；相对路径从插件目录开始。留空使用默认底色。',
    'schedule_image.background_fit': '铺满会裁切边缘；完整显示保留整张图，周围可能留白。长日程建议使用竖图。',
    'schedule_image.background_position': '图片被裁切时，选择优先保留靠上、居中还是靠下的部分。',
    'schedule_image.card_opacity': '0.9 表示卡片遮住约 90% 的背景。数值越大文字越清晰，越小越能看见背景；1 完全不透明。',
    'life_menstrual.enabled': '手动开启角色自身的周期模拟。需使用内置生活状态，并填写起算日期。',
    'life_menstrual.last_period_start': '填写模拟基准日期，例如 2026-11-08。此日期按周期持续计算，重启不会重新开始。',
    'life_menstrual.cycle_days': '从一次经期开始到下一次开始的天数，例如 30。可填写 21–40。',
    'life_menstrual.period_days': '每次经期持续几天，例如 4。可填写 2–8；结束后有两天过渡恢复。',
    'life_menstrual.symptom_level': '0 表示无明显不适，15 表示偏轻微；数值越大越需要休息和照护。不会强制痛经或情绪低落。',
    'send.permission_type': '控制通过聊天工具请求发说说的人。/zn 命令仍使用开始使用页的管理员 QQ。',
    'send.permission': '每项填写一个 QQ。只允许名单内的人时，空名单表示无人能通过聊天工具请求发布。',
    'send.custom_qqaccount': '仅 /zn custom 使用：填写要读取的私聊 QQ。留空停用这项直接发布方式。',
    'send.custom_only_mai': '开启时直接发布机器人最新的一条私聊正文；关闭时使用对方最新的一条正文。',
    'send.enable_chat_memory': '把允许范围内的聊天概括为说说背景；默认关闭，启用后继续设置下面的范围。',
    'send.filter_mode': '选择全部聊天、只允许名单内的聊天，或排除名单内的聊天。之后按需填写聊天名单。',
    'send.target_chats': '每项一个聊天，例如 group:123456 或 private:123456。仅设置按名单允许或排除时使用。',
    'send.include_private_chat_memory': '允许把选中的私聊作为匿名背景。关闭时，所有范围都排除私聊。',
    'send.time_range': '选择只参考今天的聊天，或参考最近几小时的聊天。',
    'send.chat_memory_mode': '可直接使用片段、先整理摘要，或用摘要加最近片段。整理摘要会额外请求 AI。',
    'image.enable_image': '开启后发说说时生成配图。AI 图片需要麦麦绘卷；关闭后可发纯文字说说。',
    'image.image_mode': '选择只用 AI 图片、只用表情包，或按概率随机选择一种；本次多张图共用同一种来源。',
    'image.ai_probability': '随机选择图片来源时生效。0.5 表示有 50% 的机会选择 AI 图片。',
    'image.ai_content_mode': '选择角色自拍、普通画图，或让每张图各有 50% 的机会选择其中一种。',
    'image.selfie_style': '选择前置自拍、对镜自拍、他人拍摄，或根据活动自动选择。普通画图时不使用此项。',
    'image.pic_plugin_model': '填写麦麦绘卷里已有的模型编号，例如 model3。使用 AI 图片时需要。',
    'image.image_number': '每条说说期望附带几张图，可填写 1–4。AI 图片越多等待越长；修改后重载插件。',
    'image.require_image': '开启后，AI 配图失败会停止本次发布；关闭后允许缺少失败图片继续发布。',
    'image.clear_image': '开启后不再保存 AI 图片的本地副本；关闭时保存在插件数据目录，旧副本会保留。',
    'read.read_number': '通过聊天请求查看空间时，一次读取几条最近动态。建议 3–10；修改后重载插件。',
    'read.permission_type': '控制谁能通过聊天工具查看空间和查询空间回忆；/zn 命令仍使用管理员 QQ。',
    'read.allow_skip_comment': '允许 AI 觉得没什么可补充时跳过评论。点赞仍按自己的概率设置处理。',
    'monitor.read_list': '每项一个好友 QQ。排除名单为空时处理全部；只允许名单内的人且名单为空时无人会被互动。',
    'monitor.read_list_type': '选择只和名单内的好友互动，或排除名单内的好友；也用于自己动态的评论区。',
    'monitor.silent_hours': '例如 23:00-08:00，多段用半角逗号分隔。留空表示全天允许；使用日程时区。',
    'monitor.enable_auto_reply': '自动浏览时回复自己动态下的新评论；还需要好友范围和免打扰设置允许。',
    'monitor.like_during_silent': '允许免打扰期间仍点赞；如果同时开启暂停整个空间活动，这里允许也不会执行。',
    'monitor.comment_during_silent': '允许免打扰期间仍评论和回复；需同时关闭暂停整个空间活动才可能执行。',
    'routine.post_enabled': '根据当前活动和可公开的生活内容决定是否发说说。需要启用日程、生活并完成空间登录。',
    'routine.browse_enabled': '根据当前日程决定是否查看和互动好友空间。需要启用日程并完成空间登录。',
    'routine.check_interval_minutes': '多久考虑一次发说说或刷空间，不代表每次都会执行。单位分钟。',
    'routine.respect_silent_hours': '在空间互动免打扰时段暂停整轮自动活动。手动命令仍可使用。',
    'routine.post_blocked_activities': '选择哪些活动期间不自动发说说。全部取消选择表示不按活动类型限制。',
    'routine.browse_blocked_activities': '选择哪些活动期间不自动刷空间。全部取消选择表示不按活动类型限制。',
    'routine.require_reason': '记录 AI 为什么选择发说说、浏览或保持安静，方便排查。不会改变执行概率。',
}


def build_friendly_config_schema(original: Dict[str, Any]) -> Dict[str, Any]:
    """只调整表单显示，虚拟卡片的 name 始终指向真实配置节。"""
    schema = deepcopy(original)
    sources = schema['sections']
    for section_name, section in sources.items():
        for field_name, field in section['fields'].items():
            path = f'{section_name}.{field_name}'
            if path in LABELS:
                field['label'] = LABELS[path]
            if path in HINTS:
                field['hint'] = HINTS[path]
            if field.get('input_type') == 'textarea':
                field['ui_type'] = 'textarea'
                field['rows'] = max(4, field.get('rows', 4))
            choices = field.get('choices') or []
            labels = {str(choice): CHOICE_LABELS.get(str(choice), str(choice)) for choice in choices}
            if 'random' in labels:
                labels['random'] = '随机选择 AI 或表情包' if path == 'image.image_mode' else '随机选择自拍或普通画图'
            if labels:
                explanation = '；'.join(f'{value} = {label}' for value, label in labels.items())
                field['hint'] = f"{field.get('hint') or field.get('description') or ''} 可选值：{explanation}。".strip()
            if field['type'] == 'number' and field.get('step') is None:
                field['step'] = 0.05 if field.get('max') == 1 else 0.1
    sources['plugin']['fields']['http_token']['ui_type'] = 'password'
    sources['plugin']['fields']['config_version']['hidden'] = True
    # 使用 SDK 已有的依赖元信息，同时写明启用条件；现有 WebUI 不需要额外显示代码。
    for source, toggle, fields in (
        ('schedule', 'auto_schedule_enabled', ('auto_schedule_time',)),
        ('schedule', 'adaptive_enabled', ('adaptive_interval_minutes',)),
        ('schedule', 'use_multi_round', ('max_rounds', 'quality_threshold')),
        ('schedule', 'enable_detailed_description', ('min_description_length', 'max_description_length')),
        ('schedule', 'auto_infer_next_day_prompt', ('infer_time', 'infer_lookback_days', 'infer_max_prompt_chars', 'infer_use_completion_signal')),
        ('life', 'diary_enabled', ('diary_hour',)),
        ('life_menstrual', 'enabled', ('last_period_start', 'cycle_days', 'period_days', 'symptom_level')),
        ('messaging', 'rest_gate_enabled', ('wake_probability', 'awake_grace_minutes')),
        ('monitor', 'enable_auto_reply', ('self_read_number',)),
    ):
        for name in fields:
            sources[source]['fields'][name].update(depends_on=f'{source}.{toggle}', depends_value=True)
    for name in ('http_host', 'http_port', 'http_token'):
        sources['plugin']['fields'][name].update(depends_on='plugin.cookie_methods', depends_value='napcat')
    for section in sources.values():
        for field in section['fields'].values():
            dependency = field.get('depends_on')
            if not dependency:
                continue
            source, name = dependency.split('.', 1)
            parent_label = sources[source]['fields'][name]['label']
            value = field.get('depends_value')
            if value is True or value is None:
                condition = f'需先开启“{parent_label}”。'
            else:
                condition = f'仅在“{parent_label}”选择 {value}（{CHOICE_LABELS.get(str(value), str(value))}）时生效。'
            field['hint'] = f"{field.get('hint') or field.get('description') or ''} {condition}".strip()
    contacts = sources['life']['fields']['profiles']['item_fields']
    for name, label in {
        'user_id': 'QQ 号', 'enabled': '启用联系人', 'role': '身份与可见内容',
        'proactive_enabled': '允许主动私聊', 'daily_proactive_max': '每天最多主动私聊几次',
        'quiet_start': '免打扰开始（如 23:00）', 'quiet_end': '免打扰结束（如 08:00）',
    }.items():
        contacts[name]['label'] = label
    contacts['user_id']['placeholder'] = '例如 123456789'
    contacts['role']['label'] += '（owner=主人，friend=朋友）'
    dates = sources['life']['fields']['important_dates']['item_fields']
    dates['date']['placeholder'] = '例如 2026-12-01'
    dates['lead_days']['label'] = '提前几天提醒（0 表示当天）'

    tabs = [{'id': key, 'title': title, 'sections': []} for key, title in (
        ('basic', '开始使用'), ('daily', '每日生活'), ('private', '主动私聊'),
        ('picture', '日程图片'), ('qzone', 'QQ 空间'), ('advanced', '高级设置'),
    )]
    tab_map = {tab['id']: tab for tab in tabs}
    sections: Dict[str, Any] = {}
    used = {name: set() for name in sources}

    def add(tab: str, source: str, key: str, title: str, description: str,
            fields: tuple[str, ...], *, collapsed: bool = False) -> None:
        if used[source].intersection(fields):
            raise ValueError(f'配置表单重复使用字段: {source}.{fields}')
        selected = {name: deepcopy(sources[source]['fields'][name]) for name in fields}
        for order, field in enumerate(selected.values()):
            field['order'] = order
        sections[key] = {**sources[source], 'name': source, 'title': title,
                         'description': description, 'fields': selected,
                         'collapsed': collapsed, 'order': len(sections)}
        used[source].update(fields)
        tab_map[tab]['sections'].append(key)

    add('basic', 'plugin', 'basics', '先填这两项', '开启插件，并添加能使用 /zn 命令的管理员 QQ。', ('enabled', 'admin_qq'))
    add('basic', 'persona', 'persona', '角色与说话风格（可选）', '基础人设读取主程序。需要补充形象或调整风格使用方式时再展开。', tuple(sources['persona']['fields']), collapsed=True)
    add('daily', 'schedule', 'daily_schedule', '每天怎么安排生活', '内置日程可独立使用；通常只需确认来源和每天生成时间。', (
        'enabled', 'provider', 'timezone', 'auto_schedule_enabled', 'auto_schedule_time', 'auto_generate',
        'cross_day_activity', 'repetition_check_enabled', 'adaptive_enabled', 'adaptive_interval_minutes'))
    add('daily', 'schedule', 'schedule_content', '日程内容（可选）', '默认会考虑身体需要、日常责任和兴趣；有额外偏好时再调整。', (
        'custom_prompt', 'min_activities', 'max_activities', 'enable_detailed_description',
        'min_description_length', 'max_description_length', 'recent_schedule_days'), collapsed=True)
    add('daily', 'life', 'daily_life', '生活状态与日记', '让角色的状态随活动变化，记住做过的事，生成场景、梦境和私人日记。', (
        'enabled', 'provider', 'outcomes_enabled', 'scene_enabled', 'dream_enabled', 'diary_enabled', 'diary_hour'))
    add('daily', 'life_menstrual', 'life_menstrual', '角色月经周期（可选）', '角色自身的可选生活模拟，仅内置状态生效；开启后填写起算日期。', tuple(sources['life_menstrual']['fields']), collapsed=True)
    add('daily', 'environment', 'environment', '节日与农历（可选）', '为生活背景补充中国节假日、农历和节气。', tuple(sources['environment']['fields']), collapsed=True)
    add('private', 'life', 'contacts', '联系人与重要日期', '先添加联系人；允许主动私聊和读取私人日记的权限分别设置。', ('profiles', 'important_dates'))
    add('private', 'messaging', 'private_messages', '私聊与休息时的回复', '生活主动私聊和消息追踪需要开启；休息回复闸门按需使用。', (
        'enabled', 'rest_gate_enabled', 'wake_probability', 'awake_grace_minutes', 'recall_enabled'))
    add('private', 'life', 'private_life', '生活主动私聊', '根据生活内容选择时机联系已授权的人；不需要主动联系时关闭即可。', (
        'private_proactive_enabled', 'private_min_interval_minutes', 'private_silence_minutes', 'private_min_energy', 'private_pending_seconds'))
    add('private', 'schedule', 'schedule_proactive', '约定提醒与日程主动聊天（可选）', '这组按日程联系指定聊天，与生活主动私聊分别控制。留空聊天名单时不执行。', (
        'proactive_streams', 'enable_proactive_trigger', 'enable_frequency_modulation', 'activity_proactive_enabled',
        'activity_proactive_cooldown_minutes', 'activity_proactive_daily_max', 'activity_proactive_quiet_start', 'activity_proactive_quiet_end'), collapsed=True)
    add('picture', 'schedule_image', 'schedule_image', '日程图片背景', '填写本地图片位置，再选择显示方式。背景较复杂时提高卡片不透明度。', tuple(sources['schedule_image']['fields']))
    add('qzone', 'plugin', 'qzone_login', 'QQ 空间登录', '发说说或刷空间时才需要。官方机器人的聊天登录不能直接提供 QQ 空间登录凭据。', (
        'cookie_methods', 'http_host', 'http_port', 'http_token'), collapsed=True)
    add('qzone', 'routine', 'qzone_auto', '自动发说说与刷空间', '先完成空间登录。开启后根据当前生活决定是否执行，不会每次检查都发布。', (
        'post_enabled', 'browse_enabled', 'check_interval_minutes', 'post_cooldown_minutes', 'browse_cooldown_minutes'))
    add('qzone', 'send', 'qzone_publish', '通过聊天发说说', '设置聊天工具的发布权限；直接发布指定私聊内容是可选功能。', (
        'permission_type', 'permission', 'history_number', 'custom_qqaccount', 'custom_only_mai'), collapsed=True)
    add('qzone', 'image', 'qzone_images', '说说配图（可选）', '可用 AI 图片或表情包。AI 配图需要安装麦麦绘卷，并填写其模型编号。', (
        'enable_image', 'image_mode', 'ai_probability', 'image_number', 'pic_plugin_model', 'ai_content_mode', 'selfie_style', 'require_image'), collapsed=True)
    add('qzone', 'read', 'qzone_read', '手动查看与评论', '设置通过聊天查看空间时的权限和互动方式。', (
        'permission_type', 'permission', 'read_number', 'like_probability', 'comment_probability', 'allow_skip_comment'), collapsed=True)
    add('qzone', 'monitor', 'qzone_interaction', '自动互动与免打扰', '自动刷空间开启后，按这里的好友范围、概率和免打扰时段处理。', (
        'read_list_type', 'read_list', 'like_probability', 'comment_probability', 'silent_hours',
        'like_during_silent', 'comment_during_silent', 'enable_auto_reply', 'self_read_number'), collapsed=True)
    add('advanced', 'llm', 'llm', '空间和生活模型', '通常保持默认。模型任务应在主程序中配置好；修改等待时间后重载插件。', tuple(sources['llm']['fields']), collapsed=True)
    add('advanced', 'schedule', 'schedule_model', '日程模型与生成改进', '通常保持默认。轮数越多可能等待越久；修改生成预算后重载插件。', (
        'llm_task_name', 'generation_timeout', 'max_tokens', 'use_multi_round', 'max_rounds', 'quality_threshold'), collapsed=True)
    add('advanced', 'schedule', 'schedule_infer', '提前考虑明天的安排', '只生成明日安排建议，到次日生成日程时使用。通常保持默认。', (
        'auto_infer_next_day_prompt', 'infer_time', 'infer_lookback_days', 'infer_max_prompt_chars', 'infer_use_completion_signal'), collapsed=True)
    add('advanced', 'schedule', 'schedule_context', '聊天参考与日程使用范围', '通常保持默认。只有需要限制使用范围或调整聊天背景时再展开。', (
        'inject_schedule', 'inject_into_replyer', 'max_future_activities', 'allowed_streams', 'admin_users',
        'history_message_limit', 'knowledge_search_limit', 'role_judge_enabled', 'role_judge_temperature'), collapsed=True)
    # 所有剩余参数仍可编辑；新增字段也保留在高级设置中，不丢弃配置。
    for source, title in (
        ('inject', '生活背景的使用方式'), ('life', '生活状态补算与内容保留'),
        ('send', '说说写作与聊天参考'), ('read', '评论写作模板'),
        ('monitor', '回复模板与已处理记录'), ('routine', '自动空间活动的限制'),
        ('image', 'AI 图片重试与保存'), ('schedule', '日程缓存与 AI 请求记录'),
        ('goal_cleanup', '旧日程清理'), ('messaging', '消息关联记录'), ('plugin', '适配器与版本信息'),
    ):
        fields = tuple(name for name in sources[source]['fields'] if name not in used[source])
        if fields:
            add('advanced', source, f'{source}_advanced', title, '通常保持默认；需要调整或排查对应功能时再展开。', fields, collapsed=True)
    for source, section in sources.items():
        if used[source] != set(section['fields']):
            raise ValueError(f'配置表单遗漏字段: {source}')
    schema['sections'] = sections
    schema['layout'] = {'type': 'tabs', 'tabs': tabs}
    return schema
