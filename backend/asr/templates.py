import os
from pathlib import Path
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class AudioTemplate:
    phrase: str
    intent: str
    speaker_id: str
    features: np.ndarray  # (frames, features)

class TemplateManager:
    def __init__(self, templates_dir: Path):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.templates: List[AudioTemplate] = []
        
    def add_template(self, phrase: str, intent: str, speaker_id: str, features: np.ndarray) -> None:
        template = AudioTemplate(
            phrase=phrase.strip().lower(),
            intent=intent,
            speaker_id=speaker_id,
            features=features
        )
        self.templates.append(template)
        
    def save_template_file(self, template: AudioTemplate, filename: Optional[str] = None) -> Path:
        if filename is None:
            clean_phrase = "".join(c if c.isalnum() else "_" for c in template.phrase)
            filename = f"{template.intent}__{clean_phrase}__{template.speaker_id}.npz"
        filepath = self.templates_dir / filename
        np.savez_compressed(
            filepath,
            features=template.features,
            phrase=template.phrase,
            intent=template.intent,
            speaker_id=template.speaker_id
        )
        return filepath
        
    def load_all_templates(self) -> int:
        self.templates.clear()
        count = 0
        for npz_path in self.templates_dir.glob("*.npz"):
            try:
                data = np.load(npz_path)
                template = AudioTemplate(
                    phrase=str(data["phrase"]),
                    intent=str(data["intent"]),
                    speaker_id=str(data["speaker_id"]),
                    features=data["features"].astype(np.float32)
                )
                self.templates.append(template)
                count += 1
            except Exception as e:
                print(f"Warning: Failed to load template from {npz_path}: {e}")
        return count
        
    def get_templates(self) -> List[AudioTemplate]:
        return self.templates

