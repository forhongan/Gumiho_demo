import json
import re
from datetime import datetime

from PNT import PNT
from TranslateFile import TranslateFile
from Config import Config
from Project import Project
from ai import Call_Ai


class KeywordExpression:
	"""
	Simple keyword logic evaluator.

	Grammar (case-insensitive operators):
	  expr   := term (OR term)*
	  term   := factor (AND factor)*
	  factor := NOT factor | '(' expr ')' | keyword

	Keyword can be quoted with double quotes to include spaces, e.g. "alien language".
	Operators: AND / OR / NOT, or symbols && / || / !

	Empty expr means always True.
	"""

	_token_re = re.compile(r'\s*(\(|\)|&&|\|\||!|AND|OR|NOT|"[^"]+"|\S+)')

	def tokenize(self, expr):
		if not expr or not str(expr).strip():
			return []
		tokens = []
		for match in self._token_re.finditer(expr):
			tok = match.group(1)
			tokens.append(tok)
		return tokens

	def to_rpn(self, tokens):
		prec = {"NOT": 3, "!": 3, "AND": 2, "&&": 2, "OR": 1, "||": 1}
		output = []
		stack = []
		for tok in tokens:
			upper = tok.upper()
			if upper in ("AND", "OR", "NOT") or tok in ("&&", "||", "!"):
				while stack:
					top = stack[-1]
					top_u = top.upper()
					if top in ("(", ")"):
						break
					if prec.get(top_u, prec.get(top, 0)) >= prec.get(upper, prec.get(tok, 0)):
						output.append(stack.pop())
					else:
						break
				stack.append(tok)
			elif tok == "(":
				stack.append(tok)
			elif tok == ")":
				while stack and stack[-1] != "(":
					output.append(stack.pop())
				if stack and stack[-1] == "(":
					stack.pop()
			else:
				output.append(tok)
		while stack:
			output.append(stack.pop())
		return output

	def eval_rpn(self, rpn, text, case_sensitive=False):
		if not rpn:
			return True
		stack = []
		haystack = text if case_sensitive else text.lower()
		for tok in rpn:
			upper = tok.upper()
			if upper in ("AND", "OR") or tok in ("&&", "||"):
				if len(stack) < 2:
					return False
				b = stack.pop()
				a = stack.pop()
				if upper == "AND" or tok == "&&":
					stack.append(a and b)
				else:
					stack.append(a or b)
			elif upper == "NOT" or tok == "!":
				if not stack:
					return False
				a = stack.pop()
				stack.append(not a)
			else:
				keyword = tok
				if keyword.startswith('"') and keyword.endswith('"') and len(keyword) >= 2:
					keyword = keyword[1:-1]
				needle = keyword if case_sensitive else keyword.lower()
				stack.append(needle in haystack)
		return bool(stack[-1]) if stack else False

	def evaluate(self, expr, text, case_sensitive=False):
		tokens = self.tokenize(expr)
		rpn = self.to_rpn(tokens)
		return self.eval_rpn(rpn, text, case_sensitive=case_sensitive)


class KnowledgeAwakener:
	"""
	Knowledge awaken module.
	Stores knowledge in Proper_nouns_table.json -> knowledge_awaken_table.
	"""

	def __init__(self, project_name, sse_callback=None):
		self.project_name = project_name
		self.Project = Project(project_name)
		pnt_path = self.Project.get_pnt_path()
		translatefile_path = self.Project.get_translate_file_path()
		config_path = self.Project.get_config_path()

		self.PNT = PNT(pnt_path)
		self.TranslateFile = TranslateFile(translatefile_path)
		self.Config = Config(config_path)
		self.Call_Ai = Call_Ai(sse_callback=sse_callback)
		self.expr = KeywordExpression()

	def _make_call_ai_config(self, status="translating", json_or_not=True, force_stream=None):
		"""将 Config.get_ai_config 的返回映射为 Call_Ai.call_ai 需要的字段名。"""
		cfg = self.Config.get_ai_config(status=status)
		cfg = dict(cfg) if isinstance(cfg, dict) else {}
		call_cfg = {
			"api_key": cfg.get("key", ""),
			"base_url": cfg.get("api", ""),
			"model_name": cfg.get("model_name", ""),
			"temperature": cfg.get("temperature", 0.3),
			"stream": cfg.get("stream", False),
			"json_or_not": bool(json_or_not),
			"max_tokens": cfg.get("max_tokens", 8152),
			"timeout": cfg.get("timeout", 1800),
		}
		if force_stream is not None:
			call_cfg["stream"] = bool(force_stream)
		return call_cfg

	def _ensure_table(self, data):
		if not isinstance(data, dict):
			data = {}
		table = data.get("knowledge_awaken_table")
		if not isinstance(table, list):
			table = []
			data["knowledge_awaken_table"] = table
		return data, table

	def _next_id(self, table):
		max_num = 0
		for item in table:
			raw = str(item.get("id", ""))
			m = re.match(r"ka_(\d+)", raw)
			if m:
				max_num = max(max_num, int(m.group(1)))
		return f"ka_{max_num + 1:04d}"

	def add_knowledge_awaken_rule(self, keyword_expr, knowledge_content, meta=None, enabled=True):
		"""
		Add one knowledge card to PNT.json.
		keyword_expr: logic string
		knowledge_content: string
		"""
		data = self.PNT.read_pnt()
		data, table = self._ensure_table(data)
		entry = {
			"id": self._next_id(table),
			"keyword_expr": keyword_expr or "",
			"knowledge_content": knowledge_content or "",
			"enabled": bool(enabled),
			"created_at": datetime.utcnow().isoformat(timespec="seconds") + "Z"
		}
		if meta:
			entry["meta"] = meta
		table.append(entry)
		data["knowledge_awaken_table"] = table
		self.PNT.write_pnt(data)
		return entry

	def list_knowledge_cards(self):
		data = self.PNT.read_pnt()
		_, table = self._ensure_table(data)
		return table

	def get_applicable_knowledge(self, text, case_sensitive=False, limit=None):
		"""
		Evaluate all cards against given text and return matching cards.
		"""
		data = self.PNT.read_pnt()
		_, table = self._ensure_table(data)
		results = []
		for item in table:
			if not item.get("enabled", True):
				continue
			expr = item.get("keyword_expr", "")
			if self.expr.evaluate(expr, text, case_sensitive=case_sensitive):
				results.append(item)
				if limit and len(results) >= limit:
					break
		return results

	def build_material_from_range(self, start_id, end_id, include_translation=True):
		"""从 TranslateFile 的 id 范围构建 AI 可读的材料字符串。"""
		pairs = self.TranslateFile.get_texts_in_range(start_id, end_id, include_empty=False)
		if not pairs:
			return ""

		blocks = []
		for item in pairs:
			blocks.append(f"ID {item['id']}")
			blocks.append(f"Original: {item.get('original', '')}")
			if include_translation and item.get("translation"):
				blocks.append(f"Translation: {item.get('translation', '')}")
			blocks.append("")
		return "\n".join(blocks).strip()

	def _normalize_text_input(self, text_or_list):
		"""允许 str 或 list[str] 输入，统一为单个字符串。"""
		if text_or_list is None:
			return ""
		if isinstance(text_or_list, list):
			return "\n".join([str(x) for x in text_or_list if x is not None]).strip()
		return str(text_or_list).strip()

	def build_ai_knowledge(self, original_text, translated_text, requirement, keyword_hint=None, status="translating"):
		"""
		Use AI to summarize knowledge content (and optional keyword expr).
		输入直接为原文/译文字符串（或 list[str]）。
		返回 dict: {keyword_expr, knowledge_content, raw_response}
		"""
		original_text = self._normalize_text_input(original_text)
		translated_text = self._normalize_text_input(translated_text)
		if not original_text and not translated_text:
			return None

		material_lines = []
		if original_text:
			material_lines.append("Original:\n" + original_text)
		if translated_text:
			material_lines.append("Translation:\n" + translated_text)
		material = "\n\n".join(material_lines).strip()

		sys_prompt = [
			"您是一名翻译知识摘要员。你将会收到一些翻译文本（一般包含原文和译文）。",
			"你需要根据给出的要求，提炼与翻译一致性直接相关的核心信息，写成非常精炼的 knowledge_content。",
			"这是因为后续翻译请求可能无法携带完整上下文；当后续文本满足 keyword_expr 触发条件时，会附带本 knowledge_content 作为补充知识。",
			"请返回 JSON，字段必须包含：keyword_expr、knowledge_content。",
			"keyword_expr 使用 AND/OR/NOT 运算符、括号，以及可用双引号包裹的关键词短语（例如 \"alien language\"）。",
			"如果用户已经明确指定了 keyword_expr（通过 keyword_hint 或要求中明确给出），请将 keyword_expr 设置为空字符串。"
		]

		user_lines = [
			"你将收到一段材料与总结要求。",
			"如果没有给出明确的 keyword_expr，你必须给出一个合理的 keyword_expr，用于标明后续翻译在遇到什么关键词时需要调用该知识点。",
			f"要求: {requirement}",
		]
		if keyword_hint:
			user_lines.append(f"keyword_hint: {keyword_hint}")
		user_lines.append("Materials:")
		user_lines.append(material)

		# JSON 输出更适合非流式，以降低截断/拼接带来的解析风险
		ai_config = self._make_call_ai_config(status=status, json_or_not=True, force_stream=False)

		response = self.Call_Ai.call_ai(ai_config, sys_prompt, ["\n".join(user_lines)])
		content = response.get("content", "") if isinstance(response, dict) else ""
		parsed = self._parse_json_block(content)
		if not parsed:
			return {
				"keyword_expr": "",
				"knowledge_content": "",
				"raw_response": content
			}
		return {
			"keyword_expr": str(parsed.get("keyword_expr", "")),
			"knowledge_content": str(parsed.get("knowledge_content", "")),
			"raw_response": content
		}

	def build_ai_knowledge_from_range(self, start_id, end_id, requirement, keyword_hint=None, status="translating"):
		"""兼容封装：从 TranslateFile 的 id 范围取材，然后调用 build_ai_knowledge。"""
		material = self.build_material_from_range(start_id, end_id, include_translation=True)
		if not material:
			return None
		# 将材料整体放入 original_text 参数，保持 build_ai_knowledge 的输入模型稳定
		return self.build_ai_knowledge(material, "", requirement, keyword_hint=keyword_hint, status=status)

	def add_ai_knowledge(self, original_text, translated_text, requirement, keyword_hint=None, status="translating"):
		result = self.build_ai_knowledge(original_text, translated_text, requirement, keyword_hint, status=status)
		if not result:
			return None
		return self.add_knowledge_awaken_rule(
			result.get("keyword_expr", ""),
			result.get("knowledge_content", ""),
			meta={"source": "ai"}
		)

	def add_ai_knowledge_from_range(self, start_id, end_id, requirement, keyword_hint=None, status="translating"):
		"""兼容封装：保留原先按 id 范围生成并写入知识卡片的接口。"""
		result = self.build_ai_knowledge_from_range(start_id, end_id, requirement, keyword_hint, status=status)
		if not result:
			return None
		return self.add_knowledge_awaken_rule(
			result.get("keyword_expr", ""),
			result.get("knowledge_content", ""),
			meta={"source": "ai", "start_id": start_id, "end_id": end_id}
		)

	def _parse_json_block(self, content):
		if not content:
			return None
		# Try to find the first JSON object
		m = re.search(r"\{.*\}", content, re.DOTALL)
		if not m:
			return None
		try:
			return json.loads(m.group(0))
		except Exception:
			return None

if __name__ == "__main__":
	import os
#-------------------test code-------------------
	def _read_text_file(path):
		with open(path, "r", encoding="utf-8") as f:
			return f.read()

	def _find_file(*candidates):
		for p in candidates:
			if p and os.path.exists(p):
				return p
		return None

	this_dir = os.path.dirname(os.path.abspath(__file__))
	repo_dir = os.path.dirname(this_dir)

	org_path = _find_file(
		os.path.join(repo_dir, "testKAorg.txt"),
		os.path.join(this_dir, "testKAorg.txt"),
		os.path.join(this_dir, "..", "testKAorg.txt"),
	)
	tra_path = _find_file(
		os.path.join(repo_dir, "testKAtra.txt"),
		os.path.join(this_dir, "testKAtra.txt"),
		os.path.join(this_dir, "..", "testKAtra.txt"),
	)

	if not org_path or not tra_path:
		raise FileNotFoundError(
			"未找到测试文件 testKAorg.txt / testKAtra.txt。"
			"请确认它们位于仓库根目录或 backend/ 目录。"
		)

	original_text = _read_text_file(org_path)
	translated_text = _read_text_file(tra_path)

	print("[KA TEST] Loaded test files:")
	print(" - org:", org_path)
	print(" - tra:", tra_path)
	print(" - org length:", len(original_text))
	print(" - tra length:", len(translated_text))

	# -------------------- 2) Construct awakener with test project --------------------
	project_name = "test超时空辉耀姬"
	awakener = KnowledgeAwakener(project_name=project_name, sse_callback=None)

	# -------------------- 3) Run build_ai_knowledge only (no write-back) --------------------
	requirement = (
		"请总结‘思裔(Thinker)心灵感应多线程通信的 SAH 人类化’这一翻译规范。"
		"重点提炼：哪些符号/结构属于该通信格式、哪些必须原样保留、如何处理段落与线程分隔、"
		"以及遇到速记符号(如≈)时的翻译策略。"
		"输出应尽量短，但包含可执行的翻译规则。"
	)

	result = awakener.build_ai_knowledge(
		original_text=original_text,
		translated_text=translated_text,
		requirement=requirement,
		keyword_hint=None,
		status="translating",
	)

	print("\n[KA TEST] build_ai_knowledge result:")
	print(json.dumps(result, ensure_ascii=False, indent=2))
