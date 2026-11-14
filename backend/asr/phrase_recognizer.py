from typing import Dict, Any, Optional, List
import numpy as np

from backend.config import settings
from backend.asr.audio_io import load_wav_bytes
from backend.asr.resample import resample_audio
from backend.asr.vad import trim_silence
from backend.asr.mfcc import extract_mfcc
from backend.asr.dtw import dtw_distance
from backend.asr.templates import TemplateManager, AudioTemplate

class PhraseRecognizer:
    def __init__(self, template_manager: Optional[TemplateManager] = None):
        if template_manager is None:
            self.template_manager = TemplateManager(settings.templates_dir)
            self.template_manager.load_all_templates()
            self._expand_speed_variants()
        else:
            self.template_manager = template_manager

        self.rejection_threshold = settings.dtw_rejection_threshold

    def _expand_speed_variants(self) -> None:
        """
        Add speed/pitch-perturbed copies of every source recording as extra
        templates.

        Real users speak at different rates and pitches than the synthetic
        reference speakers. DTW absorbs time misalignment, but a rate mismatch
        also shifts the spectrum itself, which pushed real utterances just
        above the rejection threshold (the classic "same output every time"
        bug: every recording was rejected with the fallback reply). The
        variants restore an accept region that covers real speech while the
        ambiguity gate keeps wrong-phrase accepts out.
        """
        rates = getattr(settings, "speed_variants", ())
        if not rates:
            return
        added = 0
        for wav_path in sorted(settings.recordings_dir.glob("*.wav")):
            # File name format: INTENT__phrase_with_underscores__speaker.wav
            parts = wav_path.stem.split("__")
            if len(parts) < 3:
                continue
            intent, phrase, speaker = parts[0], parts[1].replace("_", " "), parts[2]
            try:
                raw, sr = load_wav_bytes(wav_path.read_bytes())
            except Exception:
                continue
            if raw.size < settings.sample_rate // 4:
                continue
            for rate in rates:
                # Naive resample: scales playback rate AND pitch together,
                # which is exactly how a different voice differs from the
                # reference speaker.
                n = int(len(raw) / rate)
                stretched = np.interp(
                    np.linspace(0.0, len(raw) - 1, n), np.arange(len(raw)), raw
                ).astype(np.float32)
                audio_16k = resample_audio(stretched, sr, settings.sample_rate)
                trimmed, has_speech, _ = trim_silence(
                    audio_16k,
                    sample_rate=settings.sample_rate,
                    energy_threshold_multiplier=2.5,
                )
                if not has_speech or len(trimmed) < settings.sample_rate // 4:
                    continue
                features = extract_mfcc(
                    trimmed,
                    sample_rate=settings.sample_rate,
                    include_deltas=True,
                    apply_cmvn=True,
                )
                self.template_manager.add_template(
                    phrase, intent, f"{speaker}_r{int(round(rate * 100))}", features
                )
                added += 1
        if added:
            print(
                f"ASR templates: +{added} speed/pitch variants "
                f"(total {len(self.template_manager.templates)})"
            )
        
    def recognize_features(self, query_features: np.ndarray) -> Dict[str, Any]:
        """
        Matches query MFCC features against stored templates using DTW.
        """
        templates = self.template_manager.get_templates()
        if not templates:
            return {
                "success": False,
                "error": "no_templates_loaded",
                "recognized_text": None,
                "intent": None,
                "confidence": 0.0,
                "best_distance": float('inf'),
                "candidates": []
            }
            
        candidate_scores: List[Dict[str, Any]] = []
        n_q = query_features.shape[0]
        
        for tmpl in templates:
            n_t = tmpl.features.shape[0]
            # Duration ratio check: human speech variation is within 2.2x
            if n_q > 0 and n_t > 0:
                ratio = max(n_q, n_t) / min(n_q, n_t)
                if ratio > 2.2:
                    continue

            dist, _ = dtw_distance(query_features, tmpl.features, window_ratio=0.3, metric="euclidean")
            candidate_scores.append({
                "phrase": tmpl.phrase,
                "intent": tmpl.intent,
                "speaker_id": tmpl.speaker_id,
                "distance": dist
            })
            
        if not candidate_scores:
            return {
                "success": False,
                "rejected": True,
                "reason": "duration_mismatch",
                "recognized_text": None,
                "intent": None,
                "confidence": 0.0,
                "best_distance": float('inf'),
                "candidates": []
            }

        # Sort by lowest DTW distance
        candidate_scores.sort(key=lambda x: x["distance"])
        best = candidate_scores[0]
        second = candidate_scores[1] if len(candidate_scores) > 1 else None
        
        best_dist = best["distance"]
        
        # Check rejection threshold
        if best_dist > self.rejection_threshold:
            return {
                "success": False,
                "rejected": True,
                "reason": f"distance_above_threshold ({best_dist:.2f} > {self.rejection_threshold})",
                "recognized_text": None,
                "intent": None,
                "confidence": 0.0,
                "best_distance": best_dist,
                "candidates": candidate_scores[:3]
            }

        # Margin ratio: how much closer best is compared to second
        if second is not None and second["distance"] > 0:
            margin = (second["distance"] - best_dist) / max(1e-5, second["distance"])
        else:
            margin = 0.5

        # Ambiguity gate: when the runner-up is a DIFFERENT phrase and nearly
        # as close as the winner, the utterance is ambiguous -- reject rather
        # than guess, so a wrong command is never accepted.
        if (
            second is not None
            and second["intent"] != best["intent"]
            and margin < settings.dtw_margin_ratio
        ):
            return {
                "success": False,
                "rejected": True,
                "reason": f"ambiguous_match (margin {margin:.3f} < {settings.dtw_margin_ratio})",
                "recognized_text": None,
                "intent": None,
                "confidence": 0.0,
                "best_distance": best_dist,
                "candidates": candidate_scores[:3]
            }
            
        # Absolute distance factor: 1.0 at dist=0, 0.0 at rejection_threshold
        dist_factor = max(0.0, 1.0 - (best_dist / self.rejection_threshold))
        confidence = float(np.clip(0.6 * dist_factor + 0.4 * margin, 0.1, 0.99))
        
        return {
            "success": True,
            "rejected": False,
            "recognized_text": best["phrase"],
            "intent": best["intent"],
            "confidence": round(confidence, 3),
            "best_distance": round(best_dist, 2),
            "candidates": candidate_scores[:3]
        }
        
    def recognize_wav_bytes(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Complete pipeline: raw WAV bytes -> float array -> resample -> VAD -> MFCC -> DTW match.
        """
        try:
            raw_audio, orig_sr = load_wav_bytes(audio_bytes)
        except Exception as e:
            return {"success": False, "error": f"invalid_audio_format: {str(e)}"}
            
        # 1. Resample to 16kHz
        audio_16k = resample_audio(raw_audio, orig_sr, target_sr=settings.sample_rate)
        
        # 2. Check duration
        duration = len(audio_16k) / settings.sample_rate
        if duration < settings.min_audio_duration_sec:
            return {"success": False, "rejected": True, "reason": "audio_too_short", "duration": duration}
        if duration > settings.max_audio_duration_sec:
            return {"success": False, "rejected": True, "reason": "audio_too_long", "duration": duration}
            
        # 3. Voice Activity Detection (silence trimming)
        trimmed_audio, has_speech, vad_metrics = trim_silence(
            audio_16k,
            sample_rate=settings.sample_rate,
            energy_threshold_multiplier=2.5
        )
        if not has_speech:
            return {"success": False, "rejected": True, "reason": "no_speech_detected", "vad": vad_metrics}
            
        # 4. MFCC Feature Extraction
        features = extract_mfcc(
            trimmed_audio,
            sample_rate=settings.sample_rate,
            include_deltas=True,
            apply_cmvn=True
        )
        
        # 5. DTW Recognition
        result = self.recognize_features(features)
        result["vad_metrics"] = vad_metrics
        return result

