"""
三层记忆服务

写入（每轮对话结束后）：
  - 短期：原文存内存
  - 中期：LLM 提炼摘要存 SQLite
  - 长期：摘要存 Chroma 向量库

读取（每轮对话开始前）：
  1. 短期记忆：直接取最近几轮完整对话注入 prompt，最准确
  2. 中期记忆：取最近一条摘要，LLM 判断是否是追问，生成搜索词
  3. 长期记忆：向量检索语义相关历史，LLM 生成搜索词
  4. 都无关：返回空，走正常工作流
"""
import logging
import uuid
import dashscope
from dashscope import Generation

from config import settings
from services.memory_db import (
    add_short_term, get_short_term,
    save_mid_term, load_last_mid_term, load_all_mid_term,
    save_long_term, search_long_term,
    init_db,
)

logger = logging.getLogger(__name__)
dashscope.api_key = settings.dashscope_api_key


def _call_llm(prompt: str) -> str:
    resp = Generation.call(
        model=settings.model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        result_format="message",
    )
    if resp.status_code == 200:
        return resp.output.choices[0].message.content.strip()
    raise RuntimeError(f"LLM error {resp.status_code}")


# ─────────────────────────────────────────────
# 写入：每轮对话结束后调用
# ─────────────────────────────────────────────

def save_turn_memory(session_id: str, user_query: str, assistant_reply: str):
    # 短期：原文存内存
    add_short_term(session_id, user_query, assistant_reply)

    # 中期 + 长期：LLM 提炼摘要
    prompt = (
        "请根据以下 AI 回答内容，提炼出核心信息摘要，不超过150字。\n"
        "要求：保留关键的产品名、参数、价格、结论等实体信息，语言简洁。\n"
        "只输出摘要文字，不要任何标题或解释。\n\n"
        "AI 回答全文：\n" + assistant_reply
    )
    try:
        summary = _call_llm(prompt)
    except Exception as e:
        logger.warning(f"[Memory] Summarize failed: {e}")
        summary = assistant_reply[:150]

    # 中期存 SQLite
    save_mid_term(session_id, user_query, summary)

    # 长期存 Chroma
    doc_id = f"{session_id}_{uuid.uuid4().hex[:8]}"
    save_long_term(session_id, user_query, summary, doc_id)
    logger.info(f"[Memory] Saved all layers for session {session_id[:8]}…")


# ─────────────────────────────────────────────
# 读取：每轮对话开始前调用
# 返回 (short_term_context, search_query)
#   short_term_context: 注入 prompt 的短期对话原文（可能为空）
#   search_query: 优化后的搜索词（空字符串表示走正常流程）
# ─────────────────────────────────────────────

def build_memory_context(session_id: str, current_query: str):
    """
    返回 (short_term_context: str, search_query: str)
    """
    # ── 短期记忆：直接取最近几轮完整对话 ──
    short_turns = get_short_term(session_id)
    short_term_context = ""
    if short_turns:
        lines = []
        for t in short_turns:
            lines.append(f"用户：{t['user_query']}")
            lines.append(f"助手：{t['assistant_reply'][:200]}")  # 截取前200字避免过长
        short_term_context = "\n".join(lines)

    # ── 中期 + 长期记忆：合并为一次 LLM 调用 ──
    last = load_last_mid_term(session_id)
    long_results = search_long_term(current_query, session_id) if last is None else []

    # 先用中期，如果中期存在就不查长期；中期不存在才查长期
    if last is None:
        long_results = search_long_term(current_query, session_id)

    context_parts = []
    if last:
        context_parts.append(
            "最近一轮对话：\n提问：" + last["user_query"] + "\n摘要：" + last["summary"]
        )
    if long_results:
        history_text = "\n".join(
            f"提问：{m['user_query']} / 摘要：{m['summary']} (相似度:{m['score']:.2f})"
            for m in long_results
        )
        context_parts.append("语义相关历史：\n" + history_text)

    if context_parts:
        prompt = (
            "\n\n".join(context_parts) + "\n\n"
            "短期对话原文（最近几轮）：\n" + (short_term_context or "无") + "\n\n"
            "用户当前提问：" + current_query + "\n\n"
            "判断当前提问是否是上述对话的追问或延续（含指代词/追问细节/区别/对比/相关话题等）。\n"
            "如果是，结合具体的产品名/主题生成完整的搜索词（不超过20字，必须包含具体产品名或主题）。\n"
            "如果完全无关，输出：UNRELATED\n"
            "只输出搜索词或UNRELATED。"
        )
        try:
            result = _call_llm(prompt).strip().strip('"').strip("'")
            if result and "UNRELATED" not in result.upper() and len(result) < 60:
                logger.info(f"[Memory] Memory hit: '{current_query}' → '{result}'")
                return short_term_context, result
        except Exception as e:
            logger.warning(f"[Memory] Memory check failed: {e}")

    logger.info(f"[Memory] No relevant memory for: {current_query}")
    return short_term_context, ""
