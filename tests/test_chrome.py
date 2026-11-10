import gc
import os
import time
import tkinter as tk
import unittest
from types import SimpleNamespace
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

    def test_alt_alone_toggles_cues_and_chords_leave_them_hidden(self):
        window = self.window()
        entry = tk.Entry(window)
        entry.pack()
        menu = tk.Menu(window, tearoff=False)
        bar = chrome.MenuBar(window, window, (("Bibliothèques", menu),))
        bar.pack(fill="x")
        window.update()
        entry.focus_force()
        window.update()
        button = bar.buttons["Bibliothèques"]

        def tap_alt(key, state=0):
            event = SimpleNamespace(keysym=key, state=state)
            bar.key_press(event)
            bar.key_release(event)
            window.update()

        self.assertEqual(-1, button.cget("underline"))
        tap_alt("Alt_L")
        self.assertEqual(0, button.cget("underline"))
        self.assertEqual(button, window.focus_get())
        tap_alt("Alt_L")
        self.assertEqual(-1, button.cget("underline"))
        self.assertEqual(entry, window.focus_get())
        tap_alt("Alt_R", state=chrome.CONTROL)
        self.assertEqual(-1, button.cget("underline"))

        entry.bind("<KeyPress-z>", lambda _event: "break")
        alt = SimpleNamespace(keysym="Alt_L", state=0)
        bar.key_press(alt)
        entry.event_generate("<KeyPress-z>")
        self.assertFalse(bar.alt_alone)
        bar.key_release(alt)
        self.assertEqual(-1, button.cget("underline"))
        tap_alt("Alt_L")
        button.event_generate("<Escape>")
        window.update()
        self.assertEqual(-1, button.cget("underline"))
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

    def test_hover_switches_top_menu_with_submenu_open_and_restores_focus(self):
        window = self.window()
        entry = tk.Entry(window)
        entry.pack()
        first = NightMenu(window, tearoff=False)
        second = NightMenu(window, tearoff=False)
        child = NightMenu(first, tearoff=False)
        child.add_command(label="Témoin")
        first.add_cascade(label="Sous-menu", menu=child)
        second.add_command(label="Autre")
        bar = chrome.MenuBar(window, window, (("Catalogue", first), ("Bibliothèques", second)))
        bar.pack(fill="x")
        window.update()
        entry.focus_force()
        window.update()
        bar.buttons["Catalogue"].invoke()
        first.popup.levels[0].step(1)
        first.popup.open_child(first.popup.levels[0], keyboard=True)
        window.update()
        previous = first.popup
        target = bar.buttons["Bibliothèques"]
        x = target.winfo_rootx() + target.winfo_width() // 2
        y = target.winfo_rooty() + target.winfo_height() // 2

        target.state(["disabled"])
        with (patch.object(window, "winfo_pointerxy", return_value=(x, y)) as pointer,
              patch.object(bar, "winfo_containing", return_value=target)):
            time.sleep(.05)
            window.update()
            self.assertIs(first.popup, previous)
            target.state(["!disabled"])
            pointer.return_value = x + 1, y
            time.sleep(.05)
            window.update()
        self.assertTrue(previous.closed)
        self.assertFalse(previous.levels)
        self.assertIsNotNone(second.popup)
        self.assertTrue(target.instate(["selected"]))
        second.popup.close()
        window.update()
        self.assertEqual(entry, window.focus_get())
