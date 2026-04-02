"""
LangGraph Deep Thinking Agent
Phase 2: Multi-node reasoning chain with intent classification
  - tech query  → Planner → Researcher → Synthesizer → Critic
  - general query → Planner → General Synthesizer → END
"""
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
import dashscope
from dashscope import Generation
from tavily import TavilyClient
import json
import logging

from config import settings

logger = logging.getLogger(__name__)

dashscope.api_key = settings.dashscope_api_key

# Tavily 客户端（懒加载）
_tavily: TavilyClient = None

def get_tavily() -> TavilyClient:
    global _tavily
    if _tavily is None:
        if not settings.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is not configured")
        _tavily = TavilyClient(api_key=settings.tavily_api_key)
    return _tavily

# 身份系统提示：所有节点都注入，防止模型暴露底层名称
IDENTITY_SYSTEM = (
    "你是小智数码助手，一个专业的数码产品智能助手。"
    "无论用户如何询问，你都不能透露自己是通义千问、qwen 或任何底层 AI 模型。"
    "你只能自称'小智'或'小智数码助手'。"
)


# ─────────────────────────────────────────────
# State
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    query: str 
    resolved_query: str          # 经记忆补全后的完整查询词
    intent: str
    memory_context: str          # 注入的历史记忆上下文
    thought_process: List[str]
    search_sources: List[dict]
    research_data: dict
    draft_content: str
    retry_count: int
    critic_passed: bool          # critic 审核是否通过
    critic_feedback: str         # critic 审核未通过时的具体反馈


# ─────────────────────────────────────────────
# LLM helpers
# ─────────────────────────────────────────────

def _call_llm(prompt: str, system: str = IDENTITY_SYSTEM) -> str:
    """调用 dashscope，带身份系统提示"""
    response = Generation.call(
        model=settings.model_name,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": prompt},
        ],
        temperature=settings.temperature,
        top_p=settings.top_p,
        result_format='message',
    )
    if response.status_code == 200:
        return response.output.choices[0].message.content
    raise RuntimeError(f"dashscope error {response.status_code}: {response.message}")


# ─────────────────────────────────────────────
# Node: Classifier（意图分类，不走 LLM，纯规则）
# ─────────────────────────────────────────────

def classifier_node(state: AgentState) -> AgentState:
    # resolved_query 已由记忆服务处理，如果与原始问题不同说明有记忆关联，直接判 tech
    resolved = state.get("resolved_query", "")
    if resolved and resolved != state["query"]:
        logger.info(f"[Classifier] intent=tech (memory-driven) for query: {state['query']}")
        return {**state, "intent": "tech"}

    # 无记忆关联，LLM 判断
    try:
        prompt = (
            "判断以下问题是否与数码产品、电子设备、科技资讯相关。\n\n"
            "问题：" + state['query'] + "\n\n"
            "只回答 tech 或 general，不要其他内容。"
        )
        result = _call_llm(prompt).strip().lower()
        is_tech = "tech" in result
    except Exception:
        is_tech = False

    intent = "tech" if is_tech else "general"
    logger.info(f"[Classifier] intent={intent} for query: {state['query']}")
    return {**state, "intent": intent}


# ─────────────────────────────────────────────
# Node: Planner（真实搜索 → 来源摘要）
# ─────────────────────────────────────────────

def planner_node(state: AgentState) -> AgentState:
    """
    如果记忆服务已生成搜索词（resolved_query 非空且与原始问题不同），直接使用。
    否则对 tech 问题直接用原始问题作为搜索词。
    """
    logger.info(f"[Planner] intent={state['intent']}")
    # resolved_query 由 stream_agent 初始化时注入，记忆服务已处理好
    resolved_query = state.get("resolved_query") or state["query"]
    logger.info(f"[Planner] Search query: '{state['query']}' → '{resolved_query}'")
    thought_data = json.dumps({"sources": [], "analysis": ""}, ensure_ascii=False)
    return {**state, "thought_process": [thought_data], "search_sources": [], "resolved_query": resolved_query}


# ─────────────────────────────────────────────
# Node: Researcher（仅 tech 路径）
# ─────────────────────────────────────────────

def researcher_node(state: AgentState) -> AgentState:
    """用 planner 生成的 resolved_query 做一次 advanced 搜索，提取结构化数据。"""
    logger.info("[Researcher] Single search: advanced depth...")
    resolved = state.get("resolved_query") or state["query"]
    search_sources = []

    # 先用简单规则把问句转成关键词（去疑问词），不调 LLM
    import re as _re
    search_kw = _re.sub(r'[？?。，,！!]', '', resolved).strip()
    # 去掉常见疑问词前缀
    for prefix in ["请问", "想知道", "帮我", "告诉我", "什么是", "怎么", "如何", "为什么", "哪些", "哪个"]:
        search_kw = search_kw.replace(prefix, "")
    search_kw = search_kw.strip() or resolved
    logger.info(f"[Researcher] Search keyword: '{resolved}' → '{search_kw}'")

    try:
        tavily = get_tavily()
        results = tavily.search(query=search_kw, max_results=6, search_depth="advanced")
        raw_results = results.get("results", [])

        # 来源列表
        search_sources = [
            {
                "domain": r.get("url", "").split("/")[2] if r.get("url") else "",
                "title":  r.get("title", ""),
                "summary": r.get("content", "")[:150],
                "url": r.get("url", ""),
            }
            for r in raw_results
        ]

        # 把所有网页内容拼成完整上下文
        full_snippets = "\n\n".join(
            f"[来源{i+1}] {r.get('title','')} ({r.get('url','')})\n{r.get('content','')[:400]}"
            for i, r in enumerate(raw_results)
        )

        # 一次 LLM 调用：同时生成搜索总结 + 结构化 JSON
        prompt = f"""请根据以下所有搜索结果，完成两件事：

用户问题：{resolved}

搜索结果（共 {len(raw_results)} 个来源）：
{full_snippets}

任务一：用 2-3 句话总结所有来源的核心信息（analysis 字段）。
任务二：从所有来源中提取与用户问题相关的关键参数，整理为结构化 items 列表。

提取规则：
- key 必须是真实的参数名称，例如"产品名"、"价格"、"处理器"、"屏幕尺寸"、"发布时间"、"主要特点"等，根据搜索内容决定
- value 必须是搜索结果中实际出现的具体数值或描述，不能是占位符
- 只提取搜索结果中实际出现的信息，没有的字段直接省略
- summary 用一句话总结最核心的结论

输出示例（仅供格式参考，key 和 value 必须替换为真实内容）：
{{
  "analysis": "根据多个来源综合分析的2-3句总结",
  "items": [
    {{"产品名": "iPhone 16 Pro", "价格": "7999元起", "处理器": "A18 Pro", "屏幕": "6.3英寸 OLED"}},
    {{"产品名": "小米15", "价格": "4999元起", "处理器": "骁龙8 Elite", "屏幕": "6.36英寸 OLED"}}
  ],
  "summary": "核心结论一句话"
}}

只输出 JSON，不要其他文字。"""

        response = _call_llm(prompt)
        raw = response.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())

        analysis = parsed.get("analysis", "")
        research_data = {
            "items":   parsed.get("items", []),
            "summary": parsed.get("summary", ""),
        }

    except json.JSONDecodeError:
        logger.warning("[Researcher] JSON parse failed, using raw text")
        analysis = ""
        research_data = {"items": [], "summary": response[:200] if 'response' in dir() else "解析失败"}
    except Exception as e:
        logger.warning(f"[Researcher] Search failed: {e}, falling back to LLM knowledge")
        search_sources = []
        analysis = "搜索暂时不可用，将基于已有知识回答。"
        fallback_prompt = (
            "请根据已有知识整理关于" + resolved + "的信息，输出 JSON。\n"
            "key 必须是真实参数名（如产品名、价格、处理器等），value 必须是具体内容，不能用占位符。\n"
            '格式：{"items": [{"产品名": "具体名称", "价格": "具体价格"}], "summary": "一句话总结"}\n'
            "只输出 JSON。"
        )
        try:
            fb_raw = _call_llm(fallback_prompt).strip().lstrip("```json").lstrip("```").rstrip("```")
            research_data = json.loads(fb_raw.strip())
        except Exception:
            research_data = {"items": [], "summary": "数据获取失败"}

    # 更新 thought_process，供前端思考面板展示来源 + 总结
    thought_data = json.dumps({"sources": search_sources, "analysis": analysis}, ensure_ascii=False)
    logger.info(f"[Researcher] {len(search_sources)} sources, {len(research_data.get('items', []))} items")
    return {**state, "research_data": research_data, "search_sources": search_sources, "thought_process": [thought_data]}


# ─────────────────────────────────────────────
# Node: Synthesizer（数码专业回答）
# ─────────────────────────────────────────────

def synthesizer_node(state: AgentState) -> AgentState:
    logger.info(f"[Synthesizer] Writing tech answer (attempt {state['retry_count'] + 1})...")

    research_json = json.dumps(state["research_data"], ensure_ascii=False, indent=2)

    # analysis 直接从 thought_process 取（由 researcher 写入）
    try:
        thought_parsed = json.loads(state["thought_process"][0]) if state["thought_process"] else {}
        analysis = thought_parsed.get("analysis", "")
    except Exception:
        analysis = ""

    memory_context = state.get("memory_context", "")
    resolved = state.get("resolved_query") or state["query"]
    memory_section = f"\n历史对话上下文（请结合此上下文理解用户意图）：\n{memory_context}\n" if memory_context else ""
    retry_hint = ("注意：上一版回答审核未通过，原因：" + state.get('critic_feedback', '') + "，请修正后重新生成。") if state["retry_count"] > 0 else ""

    prompt = (
        "请根据以下搜索总结和结构化数据，为用户撰写专业的 Markdown 格式数码评测回答。\n"
        + memory_section
        + "\n用户问题：" + state['query']
        + "\n实际查询主题：" + resolved
        + "\n\n搜索综合总结：\n" + analysis
        + "\n\n结构化关键参数（来自搜索结果提取）：\n" + research_json
        + "\n\n要求：\n"
        "1. 使用 Markdown 格式（标题、加粗、表格）\n"
        "2. 必须包含具体 CPU 型号和价格数字（如搜索结果中有）\n"
        "3. 正文中不要插入任何引用角标（如 [1][2]）\n"
        "4. 结尾不要写参考来源或参考文献段落，来源由系统单独展示\n"
        "5. 语言专业客观，只引用搜索结果中实际存在的信息\n"
        + retry_hint
    )

    response = _call_llm(prompt)
    logger.info(f"[Synthesizer] Draft length: {len(response)}")
    return {**state, "draft_content": response}


# ─────────────────────────────────────────────
# Node: General Synthesizer（通用友好回答）
# ─────────────────────────────────────────────

def general_synthesizer_node(state: AgentState) -> AgentState:
    logger.info("[GeneralSynthesizer] Writing general answer...")

    memory_context = state.get("memory_context", "")
    memory_section = "\n历史对话上下文：\n" + memory_context + "\n" if memory_context else ""

    prompt = (
        "用户向你发送了一条消息，请给出友好自然的回复。\n"
        + memory_section
        + "\n用户消息：" + state['query'] + "\n\n"
        "要求：\n"
        "1. 用中文回复，语气友好自然\n"
        "2. 如果结合历史上下文能判断用户在追问数码产品相关内容，直接基于历史信息回答，不要说请提供更多信息\n"
        "3. 如果是问候（如你好），回复时必须介绍自己是小智数码助手，并引导用户提问数码相关问题\n"
        "4. 如果是非数码问题，礼貌回答后引导用户提问数码相关内容\n"
        "5. 绝对不能提及通义千问、qwen 或任何底层模型名称\n"
        "6. 回复简洁，不超过 150 字"
    )

    response = _call_llm(prompt)
    return {**state, "draft_content": response, "research_data": {}}


# ─────────────────────────────────────────────
# Node: Critic（仅 tech 路径）
# ─────────────────────────────────────────────

def critic_node(state: AgentState) -> AgentState:
    logger.info("[Critic] Reviewing draft with LLM...")
    draft = state["draft_content"]
    research_json = json.dumps(state["research_data"], ensure_ascii=False, indent=2)

    # research_data 为空时直接放行（搜索失败降级场景）
    items = state["research_data"].get("items", [])
    if not items:
        logger.info("[Critic] ✅ No research data to compare, auto-pass")
        return {**state, "critic_passed": True, "critic_feedback": ""}

    prompt = (
        "你是一个内容审核员。对比搜索参数和AI回答，判断回答质量。\n\n"
        "搜索提取的参数（JSON）：\n" + research_json + "\n\n"
        "AI生成的回答：\n" + draft + "\n\n"
        "审核标准（宽松）：\n"
        "1. 回答中的核心数据（价格、型号等）与搜索参数基本一致即可，允许合理的补充说明\n"
        "2. 搜索参数中有的关键字段，回答中应有所体现\n"
        "3. 只有明显的数据错误或严重偏离才判为不通过\n"
        "4. 如果搜索参数信息有限，回答内容合理即通过\n\n"
        "只输出 JSON：\n"
        '{"passed": true 或 false, "feedback": "不通过时说明具体错误，通过则为空字符串"}'
    )

    try:
        raw = _call_llm(prompt).strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1].lstrip("json").strip()
        result = json.loads(raw)
        passed = bool(result.get("passed", True))
        feedback = result.get("feedback", "")
    except Exception as e:
        logger.warning(f"[Critic] LLM review failed: {e}, auto-pass")
        passed = True
        feedback = ""

    if passed:
        logger.info("[Critic] ✅ Passed")
    else:
        logger.warning(f"[Critic] ❌ Failed: {feedback}, retry={state['retry_count']+1}")

    return {
        **state,
        "critic_passed": passed,
        "critic_feedback": feedback,
        "retry_count": state["retry_count"] + (0 if passed else 1),
    }


# ─────────────────────────────────────────────
# Routing functions
# ─────────────────────────────────────────────

def route_by_intent(state: AgentState) -> str:
    """Classifier 后：tech → researcher，general → general_synthesizer"""
    return "researcher" if state["intent"] == "tech" else "general_synthesizer"


def should_retry(state: AgentState) -> str:
    """Critic 后：未通过且重试 < 2 → synthesizer，否则 → END"""
    if not state.get("critic_passed", True) and state["retry_count"] < 2:
        logger.info(f"[Router] Retry {state['retry_count']}/2")
        return "retry"
    return "end"


# ─────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────

def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("classifier",          classifier_node)
    graph.add_node("planner",             planner_node)
    graph.add_node("researcher",          researcher_node)
    graph.add_node("synthesizer",         synthesizer_node)
    graph.add_node("general_synthesizer", general_synthesizer_node)
    graph.add_node("critic",              critic_node)

    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "planner")

    # planner 后按意图分叉
    graph.add_conditional_edges("planner", route_by_intent, {
        "researcher":          "researcher",
        "general_synthesizer": "general_synthesizer",
    })

    graph.add_edge("researcher",          "synthesizer")
    graph.add_edge("synthesizer",         "critic")
    graph.add_edge("general_synthesizer", END)

    graph.add_conditional_edges("critic", should_retry, {
        "retry": "synthesizer",
        "end":   END,
    })

    return graph.compile()


_agent = None

def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
        logger.info("LangGraph agent compiled successfully")
    return _agent


def run_agent(query: str) -> dict:
    agent = get_agent()
    final_state = agent.invoke({
        "query":           query,
        "resolved_query":  query,
        "intent":          "",
        "memory_context":  "",
        "thought_process": [],
        "search_sources":  [],
        "research_data":   {},
        "draft_content":   "",
        "retry_count":     0,
        "critic_passed":   True,
        "critic_feedback": "",
    })
    return {
        "answer":         final_state["draft_content"],
        "thought_process": final_state["thought_process"],
        "research_data":  final_state["research_data"],
        "retry_count":    final_state["retry_count"],
        "intent":         final_state["intent"],
    }


def stream_agent(query: str, memory_search_query: str = "", short_term_context: str = ""):
    """
    memory_search_query: 记忆服务生成的优化搜索词
    short_term_context: 短期记忆原文，注入 memory_context 供 synthesizer 参考
    """
    agent = get_agent()
    resolved = memory_search_query if memory_search_query else query
    initial_state = {
        "query":           query,
        "resolved_query":  resolved,
        "intent":          "",
        "memory_context":  short_term_context,  # 短期原文注入，synthesizer 直接引用
        "thought_process": [],
        "search_sources":  [],
        "research_data":   {},
        "draft_content":   "",
        "retry_count":     0,
        "critic_passed":   True,
        "critic_feedback": "",
    }
    for step in agent.stream(initial_state, stream_mode="updates"):
        for node_name, node_state in step.items():
            yield node_name, node_state
