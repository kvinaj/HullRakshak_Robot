import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from hullrakshak.calibration import (
    Surface,
    derive_line_calibration,
    load_line_calibration,
    save_line_calibration,
)
from hullrakshak.sensors.line import LineSensorReadings


class CalibrationTests(unittest.TestCase):
    def test_classifies_recorded_light_and_dark_clusters(self) -> None:
        calibration = load_line_calibration()

        light = calibration.classify(
            LineSensorReadings(left=154, middle=180, right=84)
        )
        dark = calibration.classify(
            LineSensorReadings(left=906, middle=904, right=915)
        )

        self.assertEqual(
            (light.left, light.middle, light.right),
            (Surface.LIGHT, Surface.LIGHT, Surface.LIGHT),
        )
        self.assertEqual(
            (dark.left, dark.middle, dark.right),
            (Surface.DARK, Surface.DARK, Surface.DARK),
        )

    def test_threshold_is_independent_for_each_sensor(self) -> None:
        calibration = load_line_calibration()
        classified = calibration.classify(
            LineSensorReadings(left=529, middle=542, right=500)
        )

        self.assertEqual(classified.left, Surface.LIGHT)
        self.assertEqual(classified.middle, Surface.DARK)
        self.assertEqual(classified.right, Surface.DARK)

    def test_derives_median_thresholds_and_round_trips_toml(self) -> None:
        light = [
            LineSensorReadings(140, 160, 60),
            LineSensorReadings(144, 165, 62),
            LineSensorReadings(148, 170, 64),
        ]
        dark = [
            LineSensorReadings(900, 910, 890),
            LineSensorReadings(914, 923, 897),
            LineSensorReadings(920, 930, 905),
        ]
        calibration = derive_line_calibration(light, dark)
        self.assertEqual(calibration.left.threshold, 529)

        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "calibration.toml"
            save_line_calibration(calibration, path, source="unit test")
            loaded = load_line_calibration(path)

        self.assertEqual(loaded, calibration)

    def test_rejects_poor_surface_separation(self) -> None:
        light = [LineSensorReadings(100, 100, 100)]
        dark = [LineSensorReadings(120, 120, 120)]
        with self.assertRaises(ValueError):
            derive_line_calibration(light, dark)


if __name__ == "__main__":
    unittest.main()
