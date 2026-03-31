"""
对话记忆管理服务
策略：滑动窗口（最近 10 轮）+ 超出部分自动压缩为摘要
- 短期记忆：最近 MAX_TURNS 轮完整对话，供 LLM 直接引用
- 长期记忆：超出窗口的历史压缩成一段摘要，保留关键实体和结论
"""
import logging
from typing import List
import dashscope
from dashscope import Generation
from config import settings

logger = logging.getLogger(__name__)

dashscope.api_key = settings.dashscope_api_key

# 滑动窗口大小：保留最近 N 轮（1轮 = 1问 + 1答）
MAX_TURNS = 10
# 触发压缩的阈值：超过此轮数时，将最早的 COMPRESS_BATCH 轮压缩进摘要
COMPRESS_BATCH = 5


class MemoryManager:
    """
    单会话记忆管理器。
    每个 WebSocket 连接持有一个实例。
    """

    def __init__(self):
        # 短期记忆：[(user_msg, assistant_msg), ...]
        self._turns: List[tuple] = []
        # 长期摘要：将早期对话压缩后的文字
        self._summary: str = ""

    # ── 公开接口 ──────────────────────────────

    def add_turn(self, user_msg: str, assistant_msg: str):
        """记录一轮对话，超出窗口时触发压缩"""
        self._turns.append((user_msg, assistant_msg))
        if len(self._turns) > MAX_TURNS:
            self._compress_oldest(COMPRESS_BATCH)

    def build_context(self) -> str:
        """
        构建注入 prompt 的上下文字符串。
        格式：
          [历史摘要]（如有）
          [近期对话]
        """
        parts = []

        if self._summary:
            parts.append(f"【历史对话摘要】\n{self._summary}")

        if self._turns:
            recent_lines = []
            for u, a in self._turns:
                recent_lines.append(f"用户：{u}")
                # 助手回复可能很长，截取前 300 字避免 token 过多
                a_short = a[:300] + "…" if len(a) > 300 else a
                recent_lines.append(f"小智：{a_short}")
            parts.append("【近期对话】\n" + "\n".join(recent_lines))

        return "\n\n".join(parts) if parts else ""

    def has_context(self) -> bool:
        return bool(self._turns or self._summary)

    def clear(self):
        self._turns = []
        self._summary = ""

    # ── 内部压缩 ──────────────────────────────

    def _compress_oldest(self, n: int):
        """将最早的 n 轮对话压缩进 _summary，从 _turns 中移除"""
        to_compress = self._turns[:n]
        self._turns = self._turns[n:]

        dialog_text = "\n".join(
            f"用户：{u}\n小智：{a}" for u, a in to_compress
        )

        prompt = f"""请将以下对话片段压缩为一段简洁的摘要（不超过200字），
保留关键实体（产品名、价格、参数、用户偏好等）和重要结论，去掉寒暄和无关内容。

{'已有摘要：' + self._summary + chr(10) if self._summary else ''}对话片段：
{dialog_text}

只输出摘要文字，不要标题或前缀。"""

        try:
            resp = Generation.call(
                model=settings.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                result_format="message",
            )
            if resp.status_code == 200:
                self._summary = resp.output.choices[0].message.content.strip()
                logger.info(f"[Memory] Compressed {n} turns → summary({len(self._summary)} chars)")
            else:
                # 压缩失败时退化：直接拼接旧摘要
                self._summary = (self._summary + "\n" + dialog_text[:400]).strip()
        except Exception as e:
            logger.warning(f"[Memory] Compression failed: {e}, using fallback")
            self._summary = (self._summary + "\n" + dialog_text[:400]).strip()
