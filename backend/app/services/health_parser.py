import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class ParsedHealthLog:
    log_type: str
    structured_data: dict[str, Any]


class HealthLogParser:
    def parse(self, text: str) -> ParsedHealthLog:
        sexual_health = self._parse_nocturnal_emission(text)
        if "睡" in text or "起来" in text:
            data: dict[str, Any] = {"description": text}
            waking = re.search(r"起来了?([一二两三四五六七八九\d]+)次", text)
            if waking:
                values = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5}
                data["night_wakings"] = values.get(waking.group(1), int(waking.group(1)) if waking.group(1).isdigit() else None)
            if "十二点" in text:
                data["sleep_time"] = "00:00左右"
            if sexual_health:
                data.update(sexual_health)
            return ParsedHealthLog("sleep", data)
        if any(x in text for x in ("头晕", "疼", "不舒服", "不得劲", "麻", "恶心", "喘")):
            symptom = next((x for x in ("头晕", "胸部不适", "疼痛", "麻", "恶心", "喘") if x in text), "身体不适")
            if "不得劲" in text:
                symptom = "胸部不适" if "胸" in text else "身体不适"
            duration = re.search(r"(最近)?([一二两三四五六七八九十\d]+)(天|周|个月)", text)
            return ParsedHealthLog("symptom", {"symptom": symptom, "duration": duration.group(0) if duration else None, "description": text})
        if any(x in text for x in ("吃了", "早餐", "午餐", "晚餐")):
            return ParsedHealthLog("food", {"description": text})
        if any(x in text for x in ("走了", "运动", "锻炼")):
            return ParsedHealthLog("exercise", {"description": text})
        if any(x in text for x in ("心情", "开心", "难过", "烦")):
            return ParsedHealthLog("mood", {"description": text})
        if sexual_health:
            return ParsedHealthLog("symptom", {"description": text, **sexual_health})
        return ParsedHealthLog("other", {"description": text})

    @staticmethod
    def _parse_nocturnal_emission(text: str) -> dict[str, Any] | None:
        """统一识别用户对睡眠中遗精的常见口语表达，但保留原文。"""
        if "遗精" in text or "梦遗" in text:
            return {"sexual_health": "睡眠中遗精", "normalized_symptoms": ["睡眠中遗精"]}
        nocturnal_context = any(x in text for x in ("睡觉", "睡着", "半夜", "夜里", "夜间", "晚上", "凌晨", "醒来", "醒了", "早上起来", "没意识", "无意识"))
        ejaculation_term = "射精" in text or "射了" in text
        if nocturnal_context and ejaculation_term:
            return {"sexual_health": "睡眠中遗精", "normalized_symptoms": ["睡眠中遗精"]}
        return None

    @staticmethod
    def dumps(data: dict[str, Any]) -> str:
        return json.dumps(data, ensure_ascii=False)


class MeasurementParser:
    def parse(self, text: str) -> dict[str, Any] | None:
        pressure = re.search(r"血压[^\d]*(\d{2,3})\s*[/／,，]\s*(\d{2,3})", text)
        if pressure:
            return {"type": "blood_pressure", "value": float(pressure.group(1)), "value2": float(pressure.group(2)), "unit": "mmHg", "measurement_context": "unknown"}
        glucose = re.search(r"血糖[^\d]*(\d+(?:\.\d+)?)", text)
        if glucose:
            context = "fasting" if "空腹" in text else "post_meal" if any(x in text for x in ("饭后", "餐后")) else "unknown"
            return {"type": "blood_glucose", "value": float(glucose.group(1)), "value2": None, "unit": "mmol/L", "measurement_context": context}
        temp = re.search(r"体温[^\d]*(\d+(?:\.\d+)?)", text)
        if temp:
            return {"type": "temperature", "value": float(temp.group(1)), "value2": None, "unit": "℃", "measurement_context": "unknown"}
        weight = re.search(r"体重[^\d]*(\d+(?:\.\d+)?)", text)
        if weight:
            return {"type": "weight", "value": float(weight.group(1)), "value2": None, "unit": "kg", "measurement_context": "unknown"}
        return None
