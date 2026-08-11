from abc import ABC, abstractmethod
from pathlib import Path


class DocumentParserProvider(ABC):
    @abstractmethod
    def parse(self, path: Path) -> dict: ...


class MockDocumentParser(DocumentParserProvider):
    def parse(self, path: Path) -> dict:
        return {"raw_extracted_text": None, "ai_summary": "文件已保存，V0.1 请由家属人工补充摘要。"}


class VisionLLMDocumentParser(DocumentParserProvider):
    def parse(self, path: Path) -> dict:
        raise NotImplementedError("V0.2 接入经审核的 OCR / 多模态模型")

