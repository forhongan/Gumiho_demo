"""
人工翻译内容解析(reading)功能
从 originmix_*.txt 中读取原文-译文对照文本，提取已翻译的人名/专有名词及描述。
生成 reading 类型的记录并更新 Proper_nouns_table。
"""

from __future__ import annotations

import glob
import os
import re
from typing import List, Tuple

from dotenv import load_dotenv

from Project import Project
from Config import Config
from Record import Record
from PNT import PNT
from ai import Call_Ai
from TranslateFile import TranslateFile


class Reading(Project):
	"""
	从人工翻译对照文本中抽取专有名词/人物描述的解析流程
	"""

	def __init__(self, project_name: str, sse_callback=None, sourcefile_name: str | None = None):
		super().__init__(project_name)
		self.project_name = project_name
		self.sourcefile_name = sourcefile_name
		self.sse_callback = sse_callback

		self.Config = Config(self.config_path)
		# 统一使用单一记录文件（与翻译流程一致）
		self.record_path = self.f_record_path
		self.Record = Record(self.record_path)
		self.PNT = PNT(self.PNT_path)
		self.TranslateFile = TranslateFile(self.translate_file_path)
		self.Call_Ai = Call_Ai(sse_callback=sse_callback)

		self.sys_prompt: List[str] = []
		self.user_prompt: List[str] = []
		self.ai_config: dict = {}
		self.response: dict = {}

	def reading(self):
		"""
		执行一次 reading：读取对照文本，构建 prompt，调用 AI，写入记录并更新专有名词表。
		"""
		self.Config.data = self.Config.read_config()
		reading_cfg = self.Config.data.get("reading_setting", {})
		if not reading_cfg.get("enable", True):
			print("Reading disabled by config.")
			return None

		if reading_cfg.get("generate_TranslateFile", False) and self._is_done_flag(reading_cfg.get("gTF_done")):
			return self._reading_from_translatefile(reading_cfg)

		if reading_cfg.get("double_file", False) and not reading_cfg.get("line_pair_mode", True):
			return self._reading_double_file(reading_cfg)

		return self._reading_mixfile_simple(reading_cfg)

	def _resolve_sourcefile_path(self, reading_cfg: dict) -> str:
		if self.sourcefile_name:
			candidate = os.path.join(self.sourcefile_path, self.sourcefile_name)
			if os.path.exists(candidate):
				return candidate
			raise FileNotFoundError(f"指定的文件不存在: {candidate}")

		pattern = reading_cfg.get("mixfile_pattern", "originmix_*.txt")
		matches = glob.glob(os.path.join(self.sourcefile_path, pattern))
		if not matches:
			raise FileNotFoundError(f"未在 sourcefile 中找到匹配文件: {pattern}")
		# 取第一个匹配项
		return matches[0]

	def _resolve_double_file_paths(self, reading_cfg: dict) -> Tuple[str, str]:
		origin_pattern = reading_cfg.get("originfile_pattern", "origin_*.txt")
		translate_pattern = reading_cfg.get("Translatefile_pattern", "translate_*.txt")
		origin_matches = glob.glob(os.path.join(self.sourcefile_path, origin_pattern))
		translate_matches = glob.glob(os.path.join(self.sourcefile_path, translate_pattern))
		if not origin_matches:
			raise FileNotFoundError(f"未在 sourcefile 中找到原文文件: {origin_pattern}")
		if not translate_matches:
			raise FileNotFoundError(f"未在 sourcefile 中找到译文文件: {translate_pattern}")
		return origin_matches[0], translate_matches[0]

	def _load_line_pairs(self, file_path: str, reading_cfg: dict) -> List[Tuple[str, str]]:
		line_pair_mode = bool(reading_cfg.get("line_pair_mode", True))
		skip_empty = bool(reading_cfg.get("skip_empty_lines", False))

		with open(file_path, "r", encoding="utf-8") as f:
			raw_lines = [line.rstrip("\n") for line in f]

		if skip_empty:
			raw_lines = [line for line in raw_lines if line.strip()]

		if not line_pair_mode:
			# 仅支持逐行成对模式，其他模式暂不启用
			return []

		pairs: List[Tuple[str, str]] = []
		for i in range(0, len(raw_lines) - 1, 2):
			original = raw_lines[i].strip()
			translated = raw_lines[i + 1].strip()
			# 跳过完全空白对
			if not original and not translated:
				continue
			pairs.append((original, translated))
		return pairs

	def _select_current_group(self, pairs: List[Tuple[str, str]], reading_cfg: dict):
		group_size = int(reading_cfg.get("Number of pairs per group", 60))
		start_idx = self._find_next_start_index()
		if start_idx is None or start_idx > len(pairs):
			return None, None, []
		end_idx = min(start_idx + group_size - 1, len(pairs))
		current_pairs = pairs[start_idx - 1:end_idx]
		return start_idx, end_idx, current_pairs

	def _find_next_start_index(self) -> int | None:
		records = self.Record.read_record().get("record", [])
		max_end = 0
		for rec in records:
			if rec.get("type") != "reading":
				continue
			if rec.get("status") == "abandoned":
				continue
			try:
				rec_end = int(rec.get("range", 0))
			except Exception:
				rec_end = 0
			if rec_end > max_end:
				max_end = rec_end
		return max_end + 1 if max_end >= 0 else 1

	def _build_system_prompt(self, reading_cfg: dict) -> List[str]:
		base_prompt = reading_cfg.get("base_prompt", "")
		return base_prompt.splitlines()

	def _build_user_prompt(self, reading_cfg: dict, pairs: List[Tuple[str, str]], start_idx: int) -> List[str]:
		prompt_lines: List[str] = []

		if self.Config.data.get("type", "") not in {"", "default"} and self.Config.data.get("Name", "") not in {"", "default"}:
			prompt_lines.append(f"# 你需要执行{self.Config.data['type']}:<{self.Config.data['Name']}>的人工翻译解析工作")

		prompt_lines.append("\n## 本次需要解析的原文-译文对照内容：")
		for offset, (original, translated) in enumerate(pairs):
			idx = start_idx + offset
			prompt_lines.append(f"\n### ID：{idx}")
			prompt_lines.append(f"原文：{original}")
			prompt_lines.append(f"译文：{translated}")

		if reading_cfg.get("include_existing_terms", True):
			prompt_lines.append("\n## 已确定的人物/专有名词翻译：\n")
			name_list = self._get_existing_name_list()
			if name_list:
				prompt_lines.extend([f"- {name}" for name in name_list])

		prompt_lines.append(f"\n#请严格按照以下格式输出:\n{reading_cfg.get('Output structure', '')}")
		prompt_lines.append(f"\n#其他注意点:\n{reading_cfg.get('Checklist', '')}")

		final_prompt = "\n".join([line.strip() for line in prompt_lines if line.strip()])
		return [final_prompt]

	def _get_existing_name_list(self) -> List[str]:
		data = self.PNT.read_pnt()
		name_list = []
		for item in data.get("translation_table", []):
			name = item.get("name", "")
			translation = item.get("translation", "")
			describe = item.get("describe", "")
			if name and translation:
				if describe:
					name_list.append(f"原名:{name}  译名:{translation}  描述:{describe}")
				else:
					name_list.append(f"原名:{name}  译名:{translation}")
		return name_list

	def _build_ai_config(self, reading_cfg: dict) -> dict:
		ai_cfg = reading_cfg.get("ai_config", {}).copy()

		# 解析环境变量形式的 key
		load_dotenv(self.Config.env_path, override=True)
		key_value = ai_cfg.get("key", "")
		if isinstance(key_value, str) and key_value.startswith("${") and key_value.endswith("}"):
			env_key = key_value[2:-1]
			ai_cfg["key"] = os.environ.get(env_key, "")

		# 兼容默认AI密钥为空时的回退
		if not ai_cfg.get("key"):
			default_cfg = self.Config.get_ai_config()
			ai_cfg["key"] = default_cfg.get("key", "")
			ai_cfg["api"] = ai_cfg.get("api", default_cfg.get("api"))
			ai_cfg["model_name"] = ai_cfg.get("model_name", default_cfg.get("model_name"))

		ai_config = {
			"api_key": ai_cfg.get("key", ""),
			"base_url": ai_cfg.get("api", ""),
			"model_name": ai_cfg.get("model_name", ""),
			"temperature": ai_cfg.get("temperature", 0.3),
			"stream": ai_cfg.get("stream", False),
			"json_or_not": ai_cfg.get("json_or_not", True),
			"max_tokens": ai_cfg.get("max_tokens", ai_cfg.get("max_len", 8192)),
		}
		return ai_config

	def _reading_mixfile_simple(self, reading_cfg: dict):
		source_path = self._resolve_sourcefile_path(reading_cfg)
		lines = self._load_lines(source_path, reading_cfg)
		if not lines:
			print("No valid content in mix file.")
			return None

		start_idx, end_idx, chunk_lines = self._select_line_chunk(lines, reading_cfg)
		if not chunk_lines:
			print("Reading completed: no remaining lines.")
			return None

		self.sys_prompt = self._build_system_prompt(reading_cfg)
		self.user_prompt = self._build_pairless_prompt(reading_cfg, chunk_lines, start_idx)
		self.ai_config = self._build_ai_config(reading_cfg)

		self.response = self.Call_Ai.call_ai(self.ai_config, self.sys_prompt, self.user_prompt)

		title = f"reading:{os.path.basename(source_path)}:{start_idx}-{end_idx}"
		new_record = self.Record.recording(self.response, title, start_idx, end_idx, "reading")

		self.Record.update_record(new_record)
		self._update_pnt_from_record(new_record)
		self._mark_record_written(new_record)

		return new_record

	def _reading_double_file(self, reading_cfg: dict):
		origin_path, translate_path = self._resolve_double_file_paths(reading_cfg)
		origin_text = self._load_text(origin_path, reading_cfg)
		translate_text = self._load_text(translate_path, reading_cfg)
		if not origin_text.strip() and not translate_text.strip():
			print("No valid content in origin/translate files.")
			return None

		max_chars = self._get_context_char_limit(reading_cfg)
		origin_chunks, translate_chunks = self._split_double_by_ratio(origin_text, translate_text, max_chars)
		chunk_total = max(len(origin_chunks), len(translate_chunks))
		chunk_index = self._find_next_start_index()
		if chunk_index is None or chunk_index > chunk_total:
			print("Reading completed: no remaining chunks.")
			return None

		origin_chunk = origin_chunks[chunk_index - 1] if chunk_index - 1 < len(origin_chunks) else ""
		translate_chunk = translate_chunks[chunk_index - 1] if chunk_index - 1 < len(translate_chunks) else ""

		self.sys_prompt = self._build_system_prompt(reading_cfg)
		self.ai_config = self._build_ai_config(reading_cfg)

		origin_prompt = self._build_origin_prompt(reading_cfg, origin_chunk, chunk_index)
		origin_resp = self.Call_Ai.call_ai(self.ai_config, self.sys_prompt, origin_prompt)
		origin_record = self.Record.recording(origin_resp, f"reading:origin:{chunk_index}", chunk_index, chunk_index, "reading")

		translate_prompt = self._build_translation_prompt(reading_cfg, translate_chunk, origin_record, chunk_index)
		translate_resp = self.Call_Ai.call_ai(self.ai_config, self.sys_prompt, translate_prompt)
		translate_record = self.Record.recording(translate_resp, f"reading:translate:{chunk_index}", chunk_index, chunk_index, "reading")

		merged_record = self._merge_reading_records(origin_record, translate_record)
		merged_record["title"] = f"reading:double:{os.path.basename(origin_path)}:{chunk_index}"

		self.Record.update_record(merged_record)
		self._update_pnt_from_record(merged_record)
		self._mark_record_written(merged_record)

		return merged_record

	def _reading_from_translatefile(self, reading_cfg: dict):
		data = self.TranslateFile.read_translatefile()
		chapters = data.get("chapters", [])
		pending = [c for c in chapters if c.get("state") == "HT_PNTing"]
		if not pending:
			print("No HT_PNTing entries in TranslateFile.json.")
			return None

		current_group = self._select_translatefile_group(pending, reading_cfg)
		start_id = current_group[0].get("id")
		end_id = current_group[-1].get("id")
		pairs = [(c.get("original-text", ""), c.get("translation-text", "")) for c in current_group]

		self.sys_prompt = self._build_system_prompt(reading_cfg)
		self.user_prompt = self._build_user_prompt(reading_cfg, pairs, int(start_id))
		self.ai_config = self._build_ai_config(reading_cfg)

		self.response = self.Call_Ai.call_ai(self.ai_config, self.sys_prompt, self.user_prompt)

		title = f"reading:TranslateFile:{start_id}-{end_id}"
		new_record = self.Record.recording(self.response, title, start_id, end_id, "reading")

		self.Record.update_record(new_record)
		self._update_pnt_from_record(new_record)
		self._mark_record_written(new_record)

		for chapter in chapters:
			cid = chapter.get("id")
			if isinstance(cid, int) and start_id <= cid <= end_id and chapter.get("state") == "HT_PNTing":
				chapter["state"] = "HT_PNTed"
		self.TranslateFile.write_translatefile(data)

		return new_record

	def preview_translatefile_reading(self):
		"""
		Preview prompts and AI config for TranslateFile-based reading without calling AI.
		"""
		self.Config.data = self.Config.read_config()
		reading_cfg = self.Config.data.get("reading_setting", {})
		if not reading_cfg.get("generate_TranslateFile", False):
			raise ValueError("generate_TranslateFile is false; TranslateFile preview is disabled.")
		if not self._is_done_flag(reading_cfg.get("gTF_done")):
			raise ValueError("gTF_done is not true; TranslateFile preview is disabled.")

		data = self.TranslateFile.read_translatefile()
		chapters = data.get("chapters", [])
		pending = [c for c in chapters if c.get("state") == "HT_PNTing"]
		if not pending:
			return {
				"message": "No HT_PNTing entries in TranslateFile.json.",
				"sys_prompt": [],
				"user_prompt": [],
				"ai_config": {}
			}

		current_group = self._select_translatefile_group(pending, reading_cfg)
		start_id = current_group[0].get("id")
		end_id = current_group[-1].get("id")
		pairs = [(c.get("original-text", ""), c.get("translation-text", "")) for c in current_group]

		sys_prompt = self._build_system_prompt(reading_cfg)
		user_prompt = self._build_user_prompt(reading_cfg, pairs, int(start_id))
		ai_config = self._build_ai_config(reading_cfg)

		return {
			"message": "Preview only; AI not called.",
			"title": f"reading:TranslateFile:{start_id}-{end_id}",
			"start_id": start_id,
			"end_id": end_id,
			"pair_count": len(pairs),
			"sys_prompt": sys_prompt,
			"user_prompt": user_prompt,
			"ai_config": ai_config
		}

	def _select_translatefile_group(self, pending: List[dict], reading_cfg: dict) -> List[dict]:
		use_chars = bool(reading_cfg.get("use_chars_count_for_pairing", False))
		if not use_chars:
			group_size = int(reading_cfg.get("Number of pairs per group", 60))
			return pending[:group_size]

		max_chars = self._get_context_char_limit(reading_cfg)
		selected = []
		char_count = 0
		for item in pending:
			original = item.get("original-text", "")
			translated = item.get("translation-text", "")
			pair_len = len(original) + len(translated)
			if selected and char_count + pair_len > max_chars:
				break
			selected.append(item)
			char_count += pair_len

		if not selected and pending:
			return [pending[0]]
		return selected

	def _load_lines(self, file_path: str, reading_cfg: dict) -> List[str]:
		skip_empty = bool(reading_cfg.get("skip_empty_lines", False))
		with open(file_path, "r", encoding="utf-8") as f:
			lines = [line.rstrip("\n") for line in f]
		if skip_empty:
			lines = [line for line in lines if line.strip()]
		return lines

	def _load_text(self, file_path: str, reading_cfg: dict) -> str:
		lines = self._load_lines(file_path, reading_cfg)
		return "\n".join(lines)

	def _select_line_chunk(self, lines: List[str], reading_cfg: dict):
		start_idx = self._find_next_start_index()
		if start_idx is None or start_idx > len(lines):
			return None, None, []
		max_chars = self._get_context_char_limit(reading_cfg)
		chunk_lines = []
		char_count = 0
		end_idx = start_idx - 1
		for i in range(start_idx - 1, len(lines)):
			line = lines[i]
			line_len = len(line)
			if chunk_lines and char_count + line_len > max_chars:
				break
			chunk_lines.append(line)
			char_count += line_len
			end_idx = i + 1
		return start_idx, end_idx, chunk_lines

	def _get_context_char_limit(self, reading_cfg: dict) -> int:
		return int(reading_cfg.get("max_chars_per_chunk", 12000))

	def _split_double_by_ratio(self, origin_text: str, translate_text: str, max_chars: int) -> Tuple[List[str], List[str]]:
		max_len = max(len(origin_text), len(translate_text))
		if max_len <= max_chars:
			return [origin_text], [translate_text]
		groups = max(1, int((max_len + max_chars - 1) / max_chars))
		return self._split_text_to_groups(origin_text, groups), self._split_text_to_groups(translate_text, groups)

	def _split_text_to_groups(self, text: str, groups: int) -> List[str]:
		if groups <= 1:
			return [text]
		chunk_len = max(1, int(len(text) / groups))
		chunks = []
		for i in range(groups):
			start = i * chunk_len
			end = len(text) if i == groups - 1 else (i + 1) * chunk_len
			chunks.append(text[start:end])
		return chunks

	def _build_pairless_prompt(self, reading_cfg: dict, lines: List[str], start_idx: int) -> List[str]:
		prompt_lines: List[str] = []
		prompt_lines.append(reading_cfg.get("pairless_prompt", ""))
		prompt_lines.append("\n## 本次需要解析的文本：")
		for offset, line in enumerate(lines):
			prompt_lines.append(f"{start_idx + offset}. {line}")

		if reading_cfg.get("include_existing_terms", True):
			prompt_lines.append("\n## 已确定的人物/专有名词翻译：\n")
			name_list = self._get_existing_name_list()
			if name_list:
				prompt_lines.extend([f"- {name}" for name in name_list])

		prompt_lines.append(f"\n#请严格按照以下格式输出:\n{reading_cfg.get('pairless_output_structure', reading_cfg.get('Output structure', ''))}")
		prompt_lines.append(f"\n#其他注意点:\n{reading_cfg.get('pairless_checklist', reading_cfg.get('Checklist', ''))}")

		final_prompt = "\n".join([line.strip() for line in prompt_lines if line and line.strip()])
		return [final_prompt]

	def _build_origin_prompt(self, reading_cfg: dict, origin_text: str, chunk_index: int) -> List[str]:
		prompt_lines: List[str] = []
		prompt_lines.append(reading_cfg.get("origin_prompt", ""))
		prompt_lines.append(f"\n## 原文片段（分段 {chunk_index}）：")
		prompt_lines.append(origin_text)
		prompt_lines.append(f"\n#请严格按照以下格式输出:\n{reading_cfg.get('origin_output_structure', reading_cfg.get('Output structure', ''))}")
		prompt_lines.append(f"\n#其他注意点:\n{reading_cfg.get('origin_checklist', reading_cfg.get('Checklist', ''))}")
		final_prompt = "\n".join([line.strip() for line in prompt_lines if line and line.strip()])
		return [final_prompt]

	def _build_translation_prompt(self, reading_cfg: dict, translate_text: str, origin_record: dict, chunk_index: int) -> List[str]:
		prompt_lines: List[str] = []
		prompt_lines.append(reading_cfg.get("translation_prompt", ""))
		prompt_lines.append(f"\n## 译文片段（分段 {chunk_index}）：")
		prompt_lines.append(translate_text)

		prompt_lines.append("\n## 待补全的名词表：")
		for item in origin_record.get("New Character", []):
			prompt_lines.append(f"- name:{item.get('name','')} translation: describe:")
		for item in origin_record.get("New proper noun", []):
			prompt_lines.append(f"- name:{item.get('name','')} translation: describe:")

		prompt_lines.append(f"\n#请严格按照以下格式输出:\n{reading_cfg.get('translation_output_structure', reading_cfg.get('Output structure', ''))}")
		prompt_lines.append(f"\n#其他注意点:\n{reading_cfg.get('translation_checklist', reading_cfg.get('Checklist', ''))}")
		final_prompt = "\n".join([line.strip() for line in prompt_lines if line and line.strip()])
		return [final_prompt]

	def _merge_reading_records(self, origin_record: dict, translate_record: dict) -> dict:
		merged = origin_record

		def _merge_list(target_key: str, source_list: list):
			name_map = {item.get("name"): item for item in merged.get(target_key, [])}
			for item in source_list:
				name = item.get("name")
				if not name:
					continue
				if name in name_map:
					if item.get("translation"):
						name_map[name]["translation"] = item.get("translation")
					if item.get("describe"):
						name_map[name]["describe"] = item.get("describe")
				else:
					name_map[name] = item
			merged[target_key] = list(name_map.values())

		_merge_list("New Character", translate_record.get("New Character", []))
		_merge_list("New proper noun", translate_record.get("New proper noun", []))
		_merge_list("Character changing", translate_record.get("Character changing", []))

		return merged

	def _is_done_flag(self, value) -> bool:
		if isinstance(value, bool):
			return value
		if isinstance(value, str):
			return value.strip().lower() in {"done", "true", "yes", "1"}
		return False

	def _update_pnt_from_record(self, rec: dict):
		data = self.PNT.read_pnt()
		table = data.get("translation_table", [])

		def find_entry(name: str):
			for entry in table:
				if entry.get("name") == name or entry.get("translation") == name:
					return entry
			return None

		title = rec.get("title", "")

		for key in ["New Character", "New proper noun"]:
			for item in rec.get(key, []):
				entry = find_entry(item.get("name"))
				describe = item.get("describe", "")
				clean_describe = re.sub(r"<<.*?>>", "", describe, flags=re.S).strip()
				if entry:
					if item.get("translation") and not entry.get("translation"):
						entry["translation"] = item.get("translation")
					entry["describe"] = clean_describe
					appearances = entry.get("appearances", [])
					if title and title not in appearances:
						appearances.append(title)
					entry["appearances"] = appearances
				else:
					new_entry = {
						"name": item.get("name"),
						"type": "Character" if key == "New Character" else "Proper noun",
						"translation": item.get("translation"),
						"describe": clean_describe,
						"appearances": [title] if title else []
					}
					table.append(new_entry)

		for item in rec.get("Character changing", []):
			entry = find_entry(item.get("name"))
			if entry and not entry.get("locked", False):
				describe = item.get("describe", "")
				clean_describe = re.sub(r"<<.*?>>", "", describe, flags=re.S).strip()
				entry["describe"] = clean_describe

		data["translation_table"] = table
		self.PNT.write_pnt(data)

	def _mark_record_written(self, new_record: dict):
		records = self.Record.read_record()
		target_ts = new_record.get("timestamp")
		if not target_ts:
			return
		for rec in records.get("record", []):
			if rec.get("timestamp") == target_ts:
				rec["status"] = "written"
				break
		self.Record.write_record(records)
  




def test_preview_translatefile_reading(project_name: str):
	"""
	Convenience test helper for TranslateFile-based reading preview.
	"""
	reader = Reading(project_name)
	return reader.preview_translatefile_reading()

if __name__ == "__main__":
    #test
	print(test_preview_translatefile_reading("test超时空辉耀姬"))
	reader = Reading("test超时空辉耀姬")
	result = reader.reading()
	print(result)
	runner = Reading("test超时空辉耀姬")
	result = runner.reading()
	print(result)


