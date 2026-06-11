import re


class TextChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 70) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        clean_text = self._normalize_text(text)
        if not clean_text:
            return []
        if len(clean_text) <= self.chunk_size:
            return [clean_text]

        chunks: list[str] = []
        start = 0
        while start < len(clean_text):
            end = min(start + self.chunk_size, len(clean_text))
            if end < len(clean_text):
                end = self._best_break(clean_text, start, end)
            chunk = clean_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(clean_text):
                break
            start = max(end - self.chunk_overlap, start + 1)
        return chunks

    def _best_break(self, text: str, start: int, proposed_end: int) -> int:
        min_end = start + max(1, self.chunk_size // 2)
        window = text[min_end:proposed_end]
        for separator in ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]:
            index = window.rfind(separator)
            if index != -1:
                return min_end + index + len(separator)
        return proposed_end

    def _normalize_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
