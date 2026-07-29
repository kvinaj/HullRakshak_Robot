import unittest

from hullrakshak.calibration import Surface, load_line_calibration
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


if __name__ == "__main__":
    unittest.main()
