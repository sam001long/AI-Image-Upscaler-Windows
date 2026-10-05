from __future__ import annotations

from pathlib import Path

from PIL import Image


class OpenPoseExtractor:
    def __init__(self) -> None:
        self.detector = None

    def _load_detector(self):
        if self.detector is not None:
            return self.detector

        try:
            from controlnet_aux import OpenposeDetector
        except ImportError as exc:
            raise RuntimeError(
                "尚未安裝 OpenPose 元件。請重新執行 setup.bat 安裝 controlnet-aux。"
            ) from exc

        # The detector weights are downloaded once, then reused from the
        # Hugging Face cache for later local runs.
        self.detector = OpenposeDetector.from_pretrained("lllyasviel/Annotators")
        return self.detector

    def extract(self, image: Image.Image, include_hands: bool = True, include_face: bool = True) -> Image.Image:
        detector = self._load_detector()
        result = detector(
            image.convert("RGB"),
            hand_and_face=bool(include_hands or include_face),
        )
        if not isinstance(result, Image.Image):
            result = Image.fromarray(result)
        return result.convert("RGB")


def load_pose_image(path: str | Path) -> Image.Image:
    return Image.open(path).convert("RGB")
