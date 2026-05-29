import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from webui.studio.navigation import get_navigation_items


class TestStudioNavigation(unittest.TestCase):
    def test_navigation_items_match_studio_information_architecture(self):
        items = get_navigation_items()

        self.assertEqual(
            [(item.key, item.label) for item in items],
            [
                ("create", "Create"),
                ("translate", "Translate"),
                ("projects", "Projects"),
                ("assets", "Assets"),
                ("brand", "Brand"),
                ("settings", "Settings"),
            ],
        )


if __name__ == "__main__":
    unittest.main()
