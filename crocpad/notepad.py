"""The main module for Crocpad++.

Contains the application class MainWindow which should only be instantiated once.
"""

import random
from pathlib import Path

from PyQt5.QtCore import QEvent, QObject, Qt
from PyQt5.QtGui import QFont, QFontDatabase, QIcon
from PyQt5.QtMultimedia import QSound
from PyQt5.QtWidgets import (QAction, QApplication, QDesktopWidget, QFileDialog,
                             QFontDialog, QMainWindow, QMessageBox,
                             QPlainTextEdit, QStatusBar, QVBoxLayout, QWidget)

import crocpad.stylesheets
from crocpad.configuration import app_config, save_config
from crocpad.eula_dialog import EulaDialog
from crocpad.eula_quiz_dialog import EulaQuizDialog
from crocpad.insert_emoji_dialog import EmojiPicker
from crocpad.troubleshooter import Troubleshooter


class MainWindow(QMainWindow):
    """Main application class for Crocpad++."""

    def __init__(self, app: QApplication, *args, **kwargs):
        """Set up the single instance of the application."""
        super(MainWindow, self).__init__(*args, **kwargs)
        self.app = app

        # Set up the QTextEdit editor configuration
        self.text_window = QPlainTextEdit()  # the actual editor pane
        self.text_window.setTabStopWidth(800)  # Set the tabstop to a nice pretty 800 pixels
        fixed_font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixed_font.setPointSize(24)
        self.text_window.setFont(QFont('Comic Sans MS', 30))
        self.text_window.installEventFilter(self)
        click_sound = str(Path('crocpad') / Path('sounds') / Path('click.wav'))
        self.sound = QSound(click_sound)
        enter_sound = str(Path('crocpad') / Path('sounds') / Path('scream.wav'))
        self.enter_sound = QSound(enter_sound)
        backspace_sound = str(Path('crocpad') / Path('sounds') / Path('wrong.wav'))
        self.backspace_sound = QSound(backspace_sound)

        # Main window layout. Most of the dialogs in Crocpad++ are converted to .py from
        # Qt Designer .ui files in the ui/ directory, but the main app window is built here.
        layout = QVBoxLayout()
        layout.addWidget(self.text_window)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Update title and centre window
        self.filename = "** Untitled **"
        self.setGeometry(50, 50, 800, 600)
        rectangle = self.frameGeometry()
        center_point = QDesktopWidget().availableGeometry().center()
        rectangle.moveCenter(center_point)
        self.move(rectangle.topLeft())
        window_icon = str(Path('crocpad') / Path('crocpad.ico'))
        self.setWindowIcon(QIcon(window_icon))
        self.create_menus()
        styles = {'light': crocpad.stylesheets.light,
                  'dark': crocpad.stylesheets.dark,
                  'hotdogstand': crocpad.stylesheets.hotdogstand,
                  'quitedark': crocpad.stylesheets.quitedark}
        self.app.setStyleSheet(styles[app_config['Editor']['visualmode']])
        self.show()

        # Post-startup tasks
        if app_config['License']['eulaaccepted'] != 'yes':
            self.do_eula()
        self.show_tip()  # tip of the day
        if app_config['Editor']['linewrap'] == 'off':
            self.text_window.setLineWrapMode(0)
            self.wrap_action.setChecked(False)

    def create_menus(self):
        """Build the menu structure for the main window."""
        main_menu = self.menuBar()
        help_menu = main_menu.addMenu('H&elp')
        view_menu = main_menu.addMenu('Vi&ew')
        file_menu = main_menu.addMenu('R&ecent Files')
        edit_menu = main_menu.addMenu('&Edit')
        search_menu = main_menu.addMenu('S&earch')
        tools_menu = main_menu.addMenu('Sp&ecial Tools')

        # Help menu
        action_tip = QAction("Tip of th&e Day", self)
        action_tip.triggered.connect(self.show_tip)
        help_menu.addAction(action_tip)

        # View menu
        theme_menu = view_menu.addMenu("Th&emes")
        action_light_theme = QAction("Light mod&e", self)
        action_light_theme.triggered.connect(self.set_light_theme)
        theme_menu.addAction(action_light_theme)
        action_dark_theme = QAction("Dark mod&e", self)
        action_dark_theme.triggered.connect(self.set_dark_theme)
        theme_menu.addAction(action_dark_theme)
        accessibility_menu = view_menu.addMenu("Acc&essibility")
        action_hotdogstand_theme = QAction("High visibility th&eme", self)
        action_hotdogstand_theme.triggered.connect(self.set_hotdogstand_theme)
        accessibility_menu.addAction(action_hotdogstand_theme)
        action_quitedark_theme = QAction("Th&eme for blind users", self)
        action_quitedark_theme.triggered.connect(self.set_quitedark_theme)
        accessibility_menu.addAction(action_quitedark_theme)

        # Special Tools menu
        font_menu = QAction("Chang&e font", self)
        font_menu.triggered.connect(self.change_font)
        tools_menu.addAction(font_menu)
        self.wrap_action = QAction("Lin&e wrap", self)  # class attribute so we can toggle it
        self.wrap_action.setCheckable(True)
        self.wrap_action.setChecked(True)
        self.wrap_action.triggered.connect(self.toggle_wrap)
        tools_menu.addAction(self.wrap_action)
        self.sound_action = QAction("Sound &effects", self)
        self.sound_action.setCheckable(True)
        self.sound_action.setChecked(True if app_config['Sound']['sounds'] == 'on' else False)
        self.sound_action.triggered.connect(self.toggle_sound)
        tools_menu.addAction(self.sound_action)

        # Edit menu
        action_insert_symbol = QAction("Ins&ert symbol", self)
        action_insert_symbol.triggered.connect(self.insert_emoji)
        edit_menu.addAction(action_insert_symbol)
        action_open_settings = QAction("Op&en settings file", self)
        action_open_settings.triggered.connect(self.open_settings)
        edit_menu.addAction(action_open_settings)

        # Search menu
        action_open = QAction("S&earch for file to open", self)
        action_open.triggered.connect(self.open_file)
        search_menu.addAction(action_open)
        action_save = QAction("S&earch for file to save", self)
        action_save.triggered.connect(self.save_file)
        search_menu.addAction(action_save)
        action_new = QAction("S&earch for a new file", self)
        action_new.triggered.connect(self.new_file)
        search_menu.addAction(action_new)

        # SubMenu Test
        testmenu = []
        for i in range(0, 200):
            testmenu.append(file_menu.addMenu(f'{i}'))

    def do_eula(self):
        """Display the End-User License Agreement and prompt the user to accept."""
        eula_file = Path('crocpad') / Path('EULA.txt')
        with open(eula_file, 'r', encoding='utf8') as f:
            eula = f.read()
        eula_dialog = EulaDialog(eula)
        eula_quiz_dialog = EulaQuizDialog()
        # run the EULA quiz, to make sure they read and understand
        while not eula_quiz_dialog.quiz_correct():
            eula_dialog.exec_()  # exec_ makes dialog modal (user cannot access main window)
            eula_quiz_dialog.exec_()

    def show_tip(self):
        """Randomly choose one tip of the day and display it."""
        tips_file = Path('crocpad') / Path('tips.txt')
        with open(tips_file, 'r', encoding='utf8') as f:
            tips = f.readlines()
        tip = random.choice(tips)
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Tip of the Day")
        dlg.setText(tip.strip())
        dlg.setIcon(QMessageBox.Information)
        dlg.show()

    def change_font(self):
        """Prompt the user for a font to change to."""
        # Do the users REEEEEALY need to change font :D
        font, ok = QFontDialog.getFont()
        if ok:
            print(font.toString())

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        """Override the eventFilter method of QObject to intercept keystrokes."""
        if event.type() == QEvent.KeyPress:
            if app_config['Sound']['sounds'] == 'on':
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    self.sound.stop()
                    self.enter_sound.play()
                if event.key() == Qt.Key_Backspace:
                    self.sound.stop()
                    self.backspace_sound.play()
                else:
                    self.sound.play()
            if event.key() == Qt.Key_Space:  # prank user with instant disappearing dialog
                if random.random() > 0.8:
                    dlg = QMessageBox(self)
                    dlg.setWindowTitle("Are you sure?")
                    dlg.setText("_" * 100)
                    dlg.show()
                    dlg.close()
            if random.random() > 0.95:
                troubleshooter = Troubleshooter()  # pester the user with a troubleshooter
                troubleshooter.exec()
        return False  # imitate overridden method

    @property
    def filename(self):
        """Return the name of the current file being edited."""
        return self._filename

    @filename.setter
    def filename(self, name: str):
        """Update the title of the main window when filename changes."""
        self._filename = name
        self.setWindowTitle(f"Crocpad++ - {self.filename}")

    def toggle_wrap(self):
        """Toggle the line wrap flag in the text editor."""
        self.text_window.setLineWrapMode(not self.text_window.lineWrapMode())
        if self.text_window.lineWrapMode():
            app_config['Editor']['linewrap'] = 'on'
        else:
            app_config['Editor']['linewrap'] = 'off'
        save_config(app_config)

    def toggle_sound(self):
        """Toggle the sound effects flag."""
        if app_config['Sound']['sounds'] == 'off':
            app_config['Sound']['sounds'] = 'on'
        else:
            app_config['Sound']['sounds'] = 'off'
        save_config(app_config)

    def open_file(self):
        """Ask the user for a filename to open, and load it into the text editor.

        Called by the Open File menu action."""
        filename = QFileDialog.getOpenFileName()[0]
        if filename != '':
            with open(filename, 'r', encoding='utf-8') as file:
                self.text_window.setPlainText(file.read())
            self.filename = filename

    def save_file(self):
        """Ask the user for a filename to save to, and write out the text editor.

        Called by the Save File menu action."""
        filename = QFileDialog.getSaveFileName()[0]
        if filename != '':
            text = self.text_window.document().toPlainText()
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(text)
            self.filename = filename

    def new_file(self):
        """Clear the text editor and insert a helpful message.

        Called by the New File menu action."""
        self.filename = "** Untitled **"
        self.text_window.document().clear()
        self.text_window.insertPlainText("""To remove this message, please make sure you have entered
your full credit card details, made payable to:
Crocpad++ Inc
PO BOX 477362213321233
Cheshire Cheese
Snekland
Australia""")

    def open_settings(self):
        settings_file = Path('crocpad') / Path('notepad.ini')
        with open(settings_file, 'r', encoding='utf-8') as file:
            self.text_window.setPlainText(file.read())
        self.filename = settings_file

    def set_light_theme(self):
        """Set the text view to the light theme."""
        self.app.setStyleSheet(crocpad.stylesheets.light)
        app_config['Editor']['visualmode'] = 'light'
        save_config(app_config)

    def set_dark_theme(self):
        """Set the text view to the dark theme."""
        self.app.setStyleSheet(crocpad.stylesheets.dark)
        app_config['Editor']['visualmode'] = 'dark'
        save_config(app_config)

    def set_hotdogstand_theme(self):
        """Set the text view to the High Contrast theme."""
        self.app.setStyleSheet(crocpad.stylesheets.hotdogstand)
        app_config['Editor']['visualmode'] = 'hotdogstand'
        save_config(app_config)

    def set_quitedark_theme(self):
        """Set the text view to the Quite Dark theme for the legally blind."""
        self.app.setStyleSheet(crocpad.stylesheets.quitedark)
        app_config['Editor']['visualmode'] = 'quitedark'
        save_config(app_config)

    def insert_emoji(self):
        """Open a modal EmojiPicker dialog which can insert arbitrary symbols at the cursor."""
        picker = EmojiPicker(self.text_window.textCursor())
        picker.exec_()
