import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from .app_model import AppModel
from .consts import READONLY


# Inspired by tkinter.simpledialog.Dialog
class CfgDialog(tk.Toplevel):
    """Class to open dialogs.

    This class is intended as a base class for custom settings dialogs.
    """

    def __init__(self, parent, model: AppModel, title: Optional[str] = None,
                 process_cb: Optional[Callable[[bool], None]] = None):
        """Initialize a dialog.

        Args:
            parent: A parent window (the application window).
            model (AppModel): A container with application data.
            title (str): The dialog title.
            process_cb (Callable[[bool], None]):
                A callback function invoked on OK and Apply button click.
                The argument is True for Apply and False for OK button.
        """

        super().__init__(parent)

        self.parent = parent
        self.model = model
        self._process_cb = process_cb
        self._process_cb_apply = False
        # UI controls to be enabled or disabled during update via 'enable' function
        self.ui_widgets = []

        self.withdraw()  # Remain invisible until 'show_modal' call
        # If the parent is not viewable, don't make the child transient,
        # or else it would be opened withdrawn.
        if parent is not None and parent.winfo_viewable():
            self.transient(parent)

        if title:
            self.title(title)

        _setup_dialog(self)

        body_box = ttk.Frame(self)
        self.initial_focus = self.body(body_box)
        if not self.initial_focus:
            self.initial_focus = self
        body_box.pack(anchor=tk.NW, fill=tk.X, expand=True, padx=5, pady=5)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(anchor=tk.S, fill=tk.X, padx=0, pady=0)

        button_box = ttk.Frame(self)
        self.buttonbox(button_box)
        button_box.pack(anchor=tk.S, fill=tk.X, padx=5, pady=5)

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        # Set min. size
        self.update()  # Geometry is '1x1+0+0' here, update it first
        self.minsize(self.winfo_width(), self.winfo_height())

        # Set default size (enlarges to min. size if necessary)
        if parent is None:
            self.geometry('450x50')
        else:
            self.geometry(f'450x50'
                          f'+{parent.winfo_rootx() + 50}'
                          f'+{parent.winfo_rooty() + 50}')

    def destroy(self):
        """Destroy the window."""
        self.initial_focus = None
        self.ui_widgets = []
        super().destroy()

    # pylint: disable=unused-argument
    def body(self, master) -> tk.BaseWidget:
        """Create dialog body.

        Return widget that should have initial focus.
        This method should be overridden, and is called
        by the __init__ method.
        """

        return self  # Override

    def buttonbox(self, master) -> None:
        """Add standard button box.

        Override if you don't want the standard buttons.

        """

        btn_ok = ttk.Button(master, text='OK', compound=tk.LEFT,
                            image=self.model.icons.ok,
                            command=self.ok, default=tk.ACTIVE)
        btn_ok.pack(side=tk.RIGHT, padx=5, pady=5)
        self.ui_widgets.append(btn_ok)

        btn_apply = ttk.Button(master, text='Apply', compound=tk.LEFT,
                               image=self.model.icons.start,
                               command=self.apply)
        btn_apply.pack(side=tk.RIGHT, padx=(5, 0), pady=5)
        self.ui_widgets.append(btn_apply)

        btn_cancel = ttk.Button(master, text='Close', compound=tk.LEFT,
                                image=self.model.icons.cancel,
                                command=self.cancel)
        btn_cancel.pack(side=tk.RIGHT, padx=(5, 0), pady=5)
        # Close/Cancel button is not disabled, allows closing dialog during update
        # self.ui_widgets.append(btn_cancel)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

    def show_modal(self) -> None:
        self.deiconify()  # Become visible now
        self.enable(True)
        self.initial_focus.focus_set()

        # Wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)

    def ok(self, _event=None) -> None:
        if not self.validate():
            self.initial_focus.focus_set()  # Put focus back
            return

        self.withdraw()
        self.update_idletasks()

        try:
            self.process()
        finally:
            self.cancel()

    def apply(self, _event=None) -> None:
        self._process_cb_apply = True
        try:
            if not self.validate():
                self.initial_focus.focus_set()  # Put focus back
            else:
                self.process()
        finally:
            self._process_cb_apply = False

    def cancel(self, _event=None) -> None:
        if self.parent is not None:
            self.parent.focus_set()  # Put focus back to the parent window
        self.destroy()

    def validate(self) -> bool:
        """Validate the data.

        This method is called automatically to validate the data before the
        dialog is destroyed. By default, it always validates OK.
        """

        return True  # Override

    def process(self) -> None:
        """Process the data.

        This method is called automatically to process the data
        on Apply and OK button click.
        By default, it invokes process callback only.
        """

        if self._process_cb is not None:
            self._process_cb(self._process_cb_apply)

        # Override

    def enable(self, active: bool, change_cursor: bool = True) -> None:
        if change_cursor:
            self.winfo_toplevel().configure(cursor='' if active else 'watch')

        for w in self.ui_widgets:
            if active:
                state = tk.NORMAL
                if isinstance(w, ttk.Combobox):
                    state = READONLY
            else:
                state = tk.DISABLED
            w.configure(state=state)

    @staticmethod
    def is_float(num) -> bool:
        try:
            float(num)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_int(num) -> bool:
        try:
            int(num)
            return True
        except ValueError:
            return False

    @staticmethod
    def clamp(n, min_n, max_n):
        return min(max(n, min_n), max_n)


# noinspection PyProtectedMember
# pylint: disable=protected-access
def _setup_dialog(w) -> None:
    if w._windowingsystem == "aqua":
        w.tk.call("::tk::unsupported::MacWindowStyle", "style",
                  w, "moveableModal", "")
    elif w._windowingsystem == "x11":
        w.wm_attributes("-type", "dialog")
