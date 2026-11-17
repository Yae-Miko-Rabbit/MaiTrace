"""日程图片布局与本地背景读取；文件和图片处理仅在线程中执行。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from html import escape
from io import BytesIO
from pathlib import Path
from typing import List, Literal
import asyncio
import base64

from PIL import Image, ImageOps, UnidentifiedImageError

from .config import ScheduleImageSection


_MAX_BACKGROUND_BYTES = 10 * 1024 * 1024
_MAX_BACKGROUND_PIXELS = 20_000_000
_PLUGIN_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ScheduleImageRow:
    index: int
    time: str
    name: str
    description: str
    status: str
    state: Literal['ongoing', 'upcoming', 'finished', 'paused'] = 'upcoming'


def _read_background(raw_path: str, plugin_dir: Path) -> str:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = plugin_dir / path
    try:
        with path.open('rb') as file:
            data = file.read(_MAX_BACKGROUND_BYTES + 1)
    except OSError as exc:
        raise ValueError(f'读取日程背景失败：{path}；{exc}') from exc
    if len(data) > _MAX_BACKGROUND_BYTES:
        raise ValueError('日程背景超过 10 MiB，请先压缩图片')
    try:
        with Image.open(BytesIO(data)) as original:
            if original.format not in {'PNG', 'JPEG', 'WEBP'}:
                raise ValueError('日程背景仅支持 PNG、JPEG 和 WebP 图片')
            if original.width * original.height > _MAX_BACKGROUND_PIXELS:
                raise ValueError('日程背景超过 2000 万像素，请先缩小图片')
            # 背景只取首帧，纠正手机照片方向并缩小后嵌入 HTML，不暴露本地文件路径。
            image = ImageOps.exif_transpose(original)
            has_alpha = image.mode in {'RGBA', 'LA'} or 'transparency' in image.info
            image = image.convert('RGBA' if has_alpha else 'RGB')
            image.thumbnail((2048, 2048), Image.Resampling.LANCZOS)
            output = BytesIO()
            if has_alpha:
                image.save(output, format='PNG')
                mime = 'image/png'
            else:
                image.save(output, format='JPEG', quality=88)
                mime = 'image/jpeg'
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('日程背景无法解码，请检查图片是否完整有效') from exc
    return f'data:{mime};base64,{base64.b64encode(output.getvalue()).decode("ascii")}'


async def load_schedule_background(raw_path: str, *, plugin_dir: Path = _PLUGIN_DIR) -> str:
    """留空时无需读取文件；显式配置的无效背景报告错误，不静默忽略。"""
    raw_path = raw_path.strip()
    if not raw_path:
        return ''
    return await asyncio.to_thread(_read_background, raw_path, plugin_dir)


def build_schedule_image_html(
    bot_name: str, day: date, rows: List[ScheduleImageRow],
    style: ScheduleImageSection, *, background: str = '',
) -> str:
    """构建可离线渲染的日程卡片，名字、描述和时间仅作为文本插入。"""
    background_css = f'background-image:url("{background}");' if background else ''
    position = {'top': 'center top', 'center': 'center center', 'bottom': 'center bottom'}[style.background_position]
    cards = []
    for row in rows:
        description = f'<p class="description">{escape(row.description)}</p>' if row.description else ''
        cards.append(
            f'<article class="entry {row.state}">'
            f'<div class="time-column"><span class="number">{row.index:02d}</span>'
            f'<span class="time">{escape(row.time)}</span></div>'
            f'<div class="activity"><div class="activity-heading"><h2>{escape(row.name)}</h2>'
            f'<span class="badge">{escape(row.status)}</span></div>{description}</div></article>'
        )
    weekday = ('周一', '周二', '周三', '周四', '周五', '周六', '周日')[day.weekday()]
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><style>'
        f':root{{--paper:rgba(255,253,249,{style.card_opacity:.3f});}}'
        '*{box-sizing:border-box}body{margin:0;padding:38px;position:relative;isolation:isolate;'
        'min-height:600px;background:#f0eee5;color:#35463f;'
        'font-family:"Microsoft YaHei","PingFang SC",sans-serif;font-size:18px}'
        '.backdrop{position:absolute;inset:0;z-index:-2;'
        f'{background_css}background-size:{style.background_fit};background-position:{position};background-repeat:no-repeat;}}'
        '.wash{position:absolute;inset:0;z-index:-1;background:linear-gradient(145deg,'
        'rgba(236,242,229,.20),rgba(249,237,228,.14))}'
        'body.default .backdrop{background-image:radial-gradient(ellipse at 0 0,#dce8d7,transparent 65%),'
        'radial-gradient(ellipse at 100% 100%,#eddbd2,transparent 65%);background-size:auto}'
        'main{max-width:1000px;margin:0 auto}.page-header{position:relative;overflow:hidden;'
        'padding:30px 34px;margin-bottom:22px;background:var(--paper);border:1px solid rgba(255,255,255,.72);'
        'border-radius:24px;box-shadow:0 8px 28px rgba(57,66,49,.07)}'
        '.eyebrow{display:flex;align-items:center;gap:9px;font-size:14px;color:#617468;letter-spacing:2px;'
        'margin:0 0 12px}.eyebrow:before{content:"";width:7px;height:7px;border-radius:50%;background:#839b80}'
        'h1{font-size:34px;line-height:1.35;margin:0 0 16px;font-weight:700;overflow-wrap:anywhere;'
        'padding-right:70px}.meta{display:flex;align-items:center;justify-content:space-between;gap:18px;'
        'font-size:15px;color:#66746b}.count{padding:5px 11px;background:rgba(105,134,101,.10);'
        'border-radius:30px;white-space:nowrap}.header-mark{position:absolute;right:32px;top:35px;'
        'color:#84987a;width:48px;height:48px;opacity:.70}'
        '.agenda{display:grid;gap:12px}.entry{display:grid;grid-template-columns:228px minmax(0,1fr);'
        'padding:24px 26px;border:1px solid rgba(255,255,255,.70);border-left:4px solid #afbaaa;'
        'border-radius:18px;background:var(--paper);box-shadow:0 4px 16px rgba(49,62,42,.05)}'
        '.time-column{display:flex;flex-direction:column;gap:12px;padding-right:20px;'
        'border-right:1px solid rgba(92,115,93,.16)}.number{font-size:13px;letter-spacing:2px;color:#758471}'
        '.time{font-size:18px;font-variant-numeric:tabular-nums;line-height:1.6;white-space:nowrap}'
        '.activity{padding-left:24px;min-width:0}.activity-heading{display:flex;align-items:flex-start;'
        'justify-content:space-between;gap:14px}h2{font-size:21px;line-height:1.5;margin:0;font-weight:600;'
        'overflow-wrap:anywhere}.description{margin:10px 0 0;color:#647166;font-size:16px;line-height:1.8;'
        'white-space:pre-wrap;overflow-wrap:anywhere}.badge{font-size:12px;line-height:1.6;padding:4px 9px;'
        'border-radius:8px;background:#edf0e8;color:#66765f;white-space:nowrap}'
        '.entry.ongoing{border-left-color:#63886d}.ongoing .badge{background:#e1eddf;color:#43634d}'
        '.entry.finished{border-left-color:#c1baad}.finished .badge{background:#efede7;color:#797366}'
        '.entry.paused{border-left-color:#b39783}.paused .badge{background:#f2e7dc;color:#876951}'
        '</style></head>'
        f'<body class="{"custom" if background else "default"}"><div class="backdrop"></div><div class="wash"></div>'
        '<main><header class="page-header"><p class="eyebrow">今日安排</p>'
        '<svg class="header-mark" viewBox="0 0 48 48" fill="none" aria-hidden="true">'
        '<path d="M9 20h25v9c0 8-5 11-12 11S9 37 9 29v-9Z" stroke="currentColor" stroke-width="2"/>'
        '<path d="M34 22h3c7 0 7 11 0 11h-4M7 43h31M17 14c-5-4 4-5 0-9M25 14c-5-4 4-5 0-9" '
        'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
        f'<h1>{escape(bot_name)}的一天</h1><div class="meta"><span>{day:%Y-%m-%d} · {weekday}</span>'
        f'<span class="count">共 {len(rows)} 个活动</span></div></header>'
        f'<section class="agenda">{"".join(cards)}</section></main></body></html>'
    )
