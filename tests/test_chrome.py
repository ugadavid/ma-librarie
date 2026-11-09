import gc
import os
import tkinter as tk
import unittest
from unittest.mock import patch

from catalogue import chrome
from catalogue.night_menu import NightMenu


@unittest.skipUnless(os.name == "nt", "La recette utilise la fenêtre Windows.")
class ChromeTests(unittest.TestCase):
    def window(self):
        gc.collect()
        window = tk.Tk()
        self.addCleanup(window.destroy)
        return window

    def test_dwm_reverts_caption_if_text_color_is_rejected(self):
        window = self.window()
        window.update()
        with patch.object(chrome.ctypes.windll.dwmapi, "DwmSetWindowAttribute",
                          side_effect=(0, -1, 0)) as apply:
            self.assertFalse(chrome.tint_title(window))
        self.assertEqual([35, 36, 35], [call.args[1] for call in apply.call_args_list])
        self.assertEqual(chrome.DWMWA_COLOR_DEFAULT, apply.call_args.args[2]._obj.value)

    def test_menu_mnemonic_and_focus_return(self):
        window = self.window()
        entry = tk.Entry(window)
        entry.pack()
        catalogue = tk.Menu(window, tearoff=False)
        libraries = tk.Menu(window, tearoff=False)
        bar = chrome.MenuBar(window, window, (("Catalogue", catalogue), ("Bibliothèques", libraries)))
        bar.pack(fill="x")
        window.update()
        entry.focus_force()
        window.update()
        button = bar.buttons["Bibliothèques"]

        def while_posted(*_coordinates, on_close, **_options):
            self.assertTrue(button.instate(["selected"]))
            on_close()

        with patch.object(libraries, "tk_popup", side_effect=while_posted) as popup:
            entry.event_generate("<Alt-KeyPress-b>")
            popup.assert_called_once()
            self.assertEqual(entry, window.focus_get())
            self.assertFalse(button.instate(["selected"]))
            popup.reset_mock()
            entry.event_generate("<F10>")
            window.update()
            first = bar.buttons["Catalogue"]
            self.assertEqual(first, window.focus_get())
            first.event_generate("<Right>")
            window.update()
            self.assertEqual(button, window.focus_get())
            button.event_generate("<Return>")
            popup.assert_called_once()
            window.update()
            self.assertEqual(entry, window.focus_get())

    def test_themed_submenu_is_invoked_and_focus_is_restored(self):
        window = self.window()
        entry = tk.Entry(window)
        entry.pack()
        menu = NightMenu(window, tearoff=False)
        child = NightMenu(menu, tearoff=False)
        seen = []
        child.add_command(label="Témoin", command=lambda: seen.append("action"))
        menu.add_command(label="Indisponible", state="disabled")
        menu.add_cascade(label="Sous-menu", menu=child)
        window.update()
        entry.focus_force()
        window.update()
        menu.tk_popup(entry.winfo_rootx(), entry.winfo_rooty() + 30, keyboard=True)
        window.update()
        popup = menu.popup
        self.assertEqual(1, popup.levels[0].active)
        popup.levels[0].canvas.event_generate("<Right>")
        window.update()
        self.assertEqual(2, len(popup.levels))
        popup.levels[1].canvas.event_generate("<Return>")
        window.update()
        self.assertEqual(["action"], seen)
        self.assertIsNone(menu.popup)
        self.assertEqual(entry, window.focus_get())
