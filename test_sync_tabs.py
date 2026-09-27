"""Run with: python3 test_sync_tabs.py"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock


def test_sync_both_directions():
    glyphs_app = ModuleType("GlyphsApp")
    glyphs_app.Glyphs = SimpleNamespace()
    for name in ("VIEW_MENU", "UPDATEINTERFACE", "ONSTATE", "OFFSTATE", "NSMenuItem"):
        setattr(glyphs_app, name, name)
    plugins = ModuleType("GlyphsApp.plugins")
    plugins.GeneralPlugin = object
    objc = ModuleType("objc")
    objc.python_method = lambda method: method
    sys.modules.update({"GlyphsApp": glyphs_app, "GlyphsApp.plugins": plugins, "objc": objc})

    path = Path(__file__).parent / "SyncTabs.glyphsPlugin/Contents/Resources/plugin.py"
    spec = importlib.util.spec_from_file_location("sync_tabs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    source_tab = MagicMock()
    source_tab.text = "/A/B"
    source_tab.textCursor = 2
    target_tab = MagicMock()
    target_tab.text = "/A"
    target_tab.textCursor = 1
    target_font = MagicMock()
    target_font.currentTab = target_tab
    target_font.parent.windowForSheet.return_value.reallyVisible.return_value = True
    source_font = MagicMock()
    source_font.currentTab = source_tab
    glyphs_app.Glyphs.font = source_font
    glyphs_app.Glyphs.removeCallback = MagicMock()

    plugin = module.SyncTabs()
    plugin.menuItem = MagicMock()
    plugin.syncEditViews_(SimpleNamespace(object=lambda: target_tab))
    assert target_tab.text == "/A"
    for fonts in ([target_font, source_font], [source_font, target_font]):
        glyphs_app.Glyphs.fonts = fonts
        for event_object in (source_tab, source_font):
            target_tab.text = "/A"
            plugin.syncEditViews_(SimpleNamespace(object=lambda: event_object))
            assert target_tab.text == "/A/B"


if __name__ == "__main__":
    test_sync_both_directions()
    print("Sync Tabs callback check passed")
