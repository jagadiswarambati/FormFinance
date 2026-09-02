from pathlib import Path
from typing import Any

from formwise_worker.ocr.providers import OcrLayoutToken, OcrResult


class PaddleOCRProvider:
    name = "paddleocr"
    enabled = True

    def extract(self, document_path: Path) -> OcrResult:
        from paddleocr import PPStructureV3

        pipeline = PPStructureV3()
        text_parts: list[str] = []
        scores: list[float] = []
        tokens: list[OcrLayoutToken] = []
        for page, result in enumerate(pipeline.predict(input=str(document_path)), start=1):
            value = result.json if not callable(result.json) else result.json()
            self._collect(value, text_parts, scores, tokens, page)
        return OcrResult(text="\n".join(part for part in text_parts if part).strip(), confidence=sum(scores) / len(scores) if scores else None, layout_tokens=tuple(tokens))

    def _collect(self, value: Any, text_parts: list[str], scores: list[float], tokens: list[OcrLayoutToken], page: int, region_type: str = "text", table_id: str | None = None) -> None:
        if isinstance(value, dict):
            texts = value.get("rec_texts", value.get("texts"))
            boxes = value.get("rec_boxes", value.get("boxes"))
            confidences = value.get("rec_scores", value.get("scores"))
            current_region = str(value.get("label", value.get("type", region_type))).lower()
            current_table = str(value.get("table_id")) if value.get("table_id") is not None else table_id
            if isinstance(texts, list):
                for index, text in enumerate(texts):
                    if not isinstance(text, str):
                        continue
                    text_parts.append(text)
                    confidence = float(confidences[index]) if isinstance(confidences, list) and index < len(confidences) and isinstance(confidences[index], (int, float)) else None
                    if confidence is not None:
                        scores.append(confidence)
                    box = boxes[index] if isinstance(boxes, list) and index < len(boxes) else None
                    normalized = self._box(box)
                    if normalized is not None:
                        tokens.append(OcrLayoutToken(text=text, page=page, x=normalized[0], y=normalized[1], width=normalized[2], height=normalized[3], confidence=confidence, reading_order=len(tokens), region_type=current_region, table_id=current_table, widget_id=str(value.get("widget_id")) if value.get("widget_id") is not None else None))
            for key, nested in value.items():
                if key not in {"rec_texts", "texts", "rec_scores", "scores", "rec_boxes", "boxes"}:
                    self._collect(nested, text_parts, scores, tokens, page, current_region, current_table)
        elif isinstance(value, list):
            for nested in value:
                self._collect(nested, text_parts, scores, tokens, page, region_type, table_id)

    @staticmethod
    def _box(value: Any) -> tuple[float, float, float, float] | None:
        if not isinstance(value, list) or not value:
            return None
        points = value if isinstance(value[0], list) else [value]
        coordinates = [(float(point[0]), float(point[1])) for point in points if isinstance(point, list) and len(point) >= 2 and isinstance(point[0], (int, float)) and isinstance(point[1], (int, float))]
        if not coordinates:
            return None
        xs, ys = [point[0] for point in coordinates], [point[1] for point in coordinates]
        return min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)
