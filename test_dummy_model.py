import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

from model.dummy_model import analyze_mri


class DummyModelRandomImageTest(unittest.TestCase):
    def test_random_noise_is_not_marked_as_tumor_when_model_is_unavailable(self):
        rng = np.random.default_rng(0)
        image = rng.integers(0, 255, (256, 256, 3), dtype=np.uint8)
        image_path = Path("test_random_noise.png")
        Image.fromarray(image).save(image_path)

        try:
            with patch("model.dummy_model.load_model", return_value=(None, None)):
                result = analyze_mri(str(image_path))
            self.assertFalse(result["present"], msg=f"Random image was mislabeled: {result}")
            self.assertEqual(result["type"], "No Tumor")
        finally:
            image_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
