"""
合并原文文本和人工翻译的文本，并将其最终储存到 TranslateFile.json 中。
支持：
- 逐行对齐或 strict_alignment: true 的直接合并
- 需要 AI 匹配的模糊对齐（按比例切块）
"""

from __future__ import annotations

import glob
import json
import os
from typing import Dict, List, Tuple

from Project import Project
from Config import Config
from TranslateFile import TranslateFile
from ai import Call_Ai
from format import LightNovelRobotJpFormat
from epub_dispose import EpubDispose


class Merger(Project):
	def __init__(self, project_name: str, sse_callback=None):
		super().__init__(project_name)
		self.project_name = project_name
		self.sse_callback = sse_callback
		self.Config = Config(self.config_path)
		self.TranslateFile = TranslateFile(self.translate_file_path)
		self.Call_Ai = Call_Ai(sse_callback=sse_callback)

	def merge(self):
		self.Config.data = self.Config.read_config()
		reading_cfg = self.Config.data.get("reading_setting", {})
		gtf_cfg = reading_cfg.get("gTF_setting", {})

		origin_path, translate_path = self._resolve_double_file_paths(reading_cfg)

		origin_json_path = os.path.join(self.project_path, "_origin_tmp_TranslateFile.json")
		translate_json_path = os.path.join(self.project_path, "_translate_tmp_TranslateFile.json")

		origin_data = self._build_translatefile(origin_path, origin_json_path)
		translate_data = self._build_translatefile(translate_path, translate_json_path)

		strict_alignment = bool(reading_cfg.get("line_pair_mode", True)) or bool(gtf_cfg.get("strict_alignment", False))
		if strict_alignment:
			merged = self._merge_by_index(origin_data, translate_data)
			self._write_translatefile(merged)
			return merged

		merged = self._merge_by_ai(origin_data, translate_data, reading_cfg, gtf_cfg)
		self._write_translatefile(merged)
		return merged

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

	def _build_translatefile(self, file_path: str, destination_path: str) -> dict:
		ext = os.path.splitext(file_path)[1].lower()
		if ext == ".epub":
			disposer = EpubDispose(self.project_path)
			disposer.epub_format(epub_file_path=file_path, destination_file=destination_path, state="HT_PNTing")
		else:
			formatter = LightNovelRobotJpFormat(self.project_path)
			formatter.lnrj_format(original_file=file_path, destination_file=destination_path)
		with open(destination_path, "r", encoding="utf-8") as f:
			return json.load(f)

	def _merge_by_index(self, origin_data: dict, translate_data: dict) -> dict:
		origin_chapters = origin_data.get("chapters", [])
		translate_chapters = translate_data.get("chapters", [])
		min_len = min(len(origin_chapters), len(translate_chapters))

		for i in range(min_len):
			origin_chapters[i]["translation-text"] = translate_chapters[i].get("original-text", "")
			origin_chapters[i]["state"] = "HT_PNTing"

		for i in range(min_len, len(origin_chapters)):
			origin_chapters[i]["translation-text"] = ""
			origin_chapters[i]["state"] = "HT_PNTing"

		origin_data["chapters"] = origin_chapters
		return origin_data

	def _merge_by_ai(self, origin_data: dict, translate_data: dict, reading_cfg: dict, gtf_cfg: dict) -> dict:
		origin_chapters = origin_data.get("chapters", [])
		translate_chapters = translate_data.get("chapters", [])
		origin_map = {c.get("id"): c for c in origin_chapters if isinstance(c.get("id"), int)}
		translate_map = {c.get("id"): c for c in translate_chapters if isinstance(c.get("id"), int)}

		origin_ids = [c.get("id") for c in origin_chapters if isinstance(c.get("id"), int)]
		translate_ids = [c.get("id") for c in translate_chapters if isinstance(c.get("id"), int)]

		origin_idx = 0
		translate_idx = 0
		max_chars = int(reading_cfg.get("max_chars_per_chunk", 12000))
		translation_ratio = float(gtf_cfg.get("translation_ratio", 1.2))

		final_map: Dict[int, str] = {}

		while origin_idx < len(origin_ids):
			origin_slice_ids = self._slice_ids_by_chars(origin_ids, origin_map, origin_idx, max_chars)
			translate_slice_ids = self._slice_ids_by_chars(translate_ids, translate_map, translate_idx, int(max_chars * translation_ratio))
			if not origin_slice_ids:
				break

			prompt = self._build_match_prompt(origin_slice_ids, translate_slice_ids, origin_map, translate_map, gtf_cfg)
			ai_cfg = self._build_ai_config(reading_cfg)
			response = self.Call_Ai.call_ai(ai_cfg, gtf_cfg.get("base_prompt", "").splitlines(), [prompt])
			match_data = self._parse_match_response(response.get("content", ""))

			self._apply_match_result(match_data, origin_map, translate_map, final_map)
			origin_idx, translate_idx = self._advance_indices(match_data, origin_ids, translate_ids, origin_slice_ids, translate_slice_ids)

		for cid, chapter in origin_map.items():
			chapter["translation-text"] = final_map.get(cid, "")
			chapter["state"] = "HT_PNTing"
		origin_data["chapters"] = list(origin_map.values())
		origin_data["chapters"].sort(key=lambda x: x.get("id", 0))
		return origin_data

	def _slice_ids_by_chars(self, ids: List[int], data_map: Dict[int, dict], start_idx: int, max_chars: int) -> List[int]:
		result = []
		char_count = 0
		for i in range(start_idx, len(ids)):
			cid = ids[i]
			text = str(data_map[cid].get("original-text", ""))
			if result and char_count + len(text) > max_chars:
				break
			result.append(cid)
			char_count += len(text)
		return result

	def _build_match_prompt(self, origin_ids: List[int], translate_ids: List[int], origin_map: Dict[int, dict], translate_map: Dict[int, dict], gtf_cfg: dict) -> str:
		lines = []
		lines.append("# 原文片段")
		for cid in origin_ids:
			lines.append(f"id:{cid} {origin_map[cid].get('original-text','')}")
		lines.append("\n# 译文片段")
		for cid in translate_ids:
			lines.append(f"id:{cid} {translate_map[cid].get('original-text','')}")
		lines.append("\n#请严格按照以下格式输出:")
		lines.append(gtf_cfg.get("Output structure", ""))
		return "\n".join(lines)

	def _parse_match_response(self, content: str) -> dict:
		try:
			return json.loads(content)
		except Exception:
			pass

		def _extract_json_from_text(s: str):
			candidates = []
			for opening, closing in (("{", "}"), ("[", "]")):
				start = 0
				while True:
					idx = s.find(opening, start)
					if idx == -1:
						break
					in_string = False
					escape = False
					depth = 0
					for j in range(idx, len(s)):
						ch = s[j]
						if ch == "\\" and in_string:
							escape = not escape
							continue
						if ch == '"' and not escape:
							in_string = not in_string
						if in_string:
							escape = False
							continue
						if ch == opening:
							depth += 1
						elif ch == closing:
							depth -= 1
							if depth == 0:
								candidates.append(s[idx:j + 1])
								break
						escape = False
					start = idx + 1
			return candidates

		for cand in _extract_json_from_text(content):
			try:
				return json.loads(cand)
			except Exception:
				continue
		return {"matching chains": [], "others": []}

	def _apply_match_result(self, match_data: dict, origin_map: Dict[int, dict], translate_map: Dict[int, dict], final_map: Dict[int, str]):
		chains = match_data.get("matching chains") or match_data.get("matching_chains") or []
		for chain in chains:
			try:
				origin_start = int(chain.get("origin_start_id"))
				translation_start = int(chain.get("translation_start_id"))
				length = int(chain.get("length"))
			except Exception:
				continue
			for i in range(length):
				orig_id = origin_start + i
				trans_id = translation_start + i
				if orig_id in origin_map and trans_id in translate_map:
					final_map[orig_id] = translate_map[trans_id].get("original-text", "")

		others = match_data.get("others", [])
		for item in others:
			try:
				orig_id = int(item.get("id"))
			except Exception:
				continue
			translation = item.get("translation", "")
			if orig_id in origin_map and translation:
				final_map[orig_id] = translation

	def _advance_indices(self, match_data: dict, origin_ids: List[int], translate_ids: List[int], origin_slice_ids: List[int], translate_slice_ids: List[int]) -> Tuple[int, int]:
		max_origin_id = None
		max_trans_id = None
		chains = match_data.get("matching chains") or match_data.get("matching_chains") or []
		for chain in chains:
			try:
				origin_start = int(chain.get("origin_start_id"))
				translation_start = int(chain.get("translation_start_id"))
				length = int(chain.get("length"))
			except Exception:
				continue
			origin_end = origin_start + length - 1
			trans_end = translation_start + length - 1
			max_origin_id = origin_end if max_origin_id is None else max(max_origin_id, origin_end)
			max_trans_id = trans_end if max_trans_id is None else max(max_trans_id, trans_end)

		if max_origin_id is None:
			origin_next = origin_ids.index(origin_slice_ids[-1]) + 1
			if translate_slice_ids:
				translate_next = translate_ids.index(translate_slice_ids[-1]) + 1
			else:
				translate_next = 0
			return origin_next, translate_next

		origin_idx = self._index_after_id(origin_ids, max_origin_id)
		trans_idx = self._index_after_id(translate_ids, max_trans_id) if max_trans_id is not None else 0
		return origin_idx, trans_idx

	def _index_after_id(self, ids: List[int], target_id: int) -> int:
		for i, cid in enumerate(ids):
			if cid == target_id:
				return i + 1
		return len(ids)

	def _build_ai_config(self, reading_cfg: dict) -> dict:
		ai_cfg = reading_cfg.get("ai_config", {}).copy()
		key_value = ai_cfg.get("key", "")
		if isinstance(key_value, str) and key_value.startswith("${") and key_value.endswith("}"):
			env_key = key_value[2:-1]
			ai_cfg["key"] = os.environ.get(env_key, "")

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

	def _write_translatefile(self, data: dict):
		with open(self.translate_file_path, "w", encoding="utf-8") as f:
			json.dump(data, f, ensure_ascii=False, indent=2)