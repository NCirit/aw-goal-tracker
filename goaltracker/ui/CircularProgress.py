import sys
from datetime import datetime

from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QTimer, QThread, QThreadPool
from PyQt5.QtGui import QPainter, QColor, QFont, QPen
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, \
    QLabel, QMenu, QAction, QLineEdit, QPushButton, \
    QDoubleSpinBox, QComboBox,QDateTimeEdit, QSizePolicy, \
    QGridLayout

from goaltracker.ui.FilterConfiguration import FilterConfiguration
from goaltracker.Goal import Goal, GoalTypes
from goaltracker.awfetcher import fetch_hours

class GoalEditor(QWidget):
    signal_goal_edited = pyqtSignal(Goal)

    def __init__(self, goal : Goal):
        super().__init__()

        self.setWindowTitle("Goal Editor")
        self.setWindowFlags(Qt.Tool)

        self.goal = goal
        
        grid = QGridLayout(self)

        LABEL_COL = 0
        WIDGET_COL = 1
        current_row = 0
        self.le_name = QLineEdit(self.goal.name)
        self.le_name.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        grid.addWidget(QLabel("Name: "), current_row, LABEL_COL)
        grid.addWidget(self.le_name, current_row, WIDGET_COL)
        current_row += 1

        self.dsp_goal = QDoubleSpinBox()
        self.dsp_goal.setRange(1, 1e6)
        self.dsp_goal.setValue(self.goal.target)
        self.dsp_goal.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        grid.addWidget(QLabel("Goal: "), current_row, LABEL_COL)
        grid.addWidget(self.dsp_goal, current_row, WIDGET_COL)
        current_row += 1

        self.combo_goal_type = QComboBox()
        self.combo_goal_type.addItem(GoalTypes.DAILY)
        self.combo_goal_type.addItem(GoalTypes.MONTHLY)
        self.combo_goal_type.addItem(GoalTypes.YEARLY)
        self.combo_goal_type.addItem(GoalTypes.CUSTOM)
        self.combo_goal_type.setCurrentIndex(self.combo_goal_type.findText(goal.goal_type))
        self.combo_goal_type.currentIndexChanged.connect(self.goal_type_selected)
        self.combo_goal_type.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed))
        grid.addWidget(QLabel("Goal type: "), current_row, LABEL_COL)
        grid.addWidget(self.combo_goal_type, current_row, WIDGET_COL)
        current_row += 1

        self.dte_begin_date = QDateTimeEdit()
        if not self.goal.begin_date is None:
            self.dte_begin_date.setDateTime(self.goal.begin_date)
        else:
            self.dte_begin_date.setDateTime(datetime.now())
        self.dte_begin_date.setDisabled(True)
        grid.addWidget(QLabel("Begin date: "), current_row, LABEL_COL)
        grid.addWidget(self.dte_begin_date, current_row, WIDGET_COL)
        current_row += 1
        
        self.dte_end_date = QDateTimeEdit()
        if not self.goal.end_date is None:
            self.dte_end_date.setDateTime(self.goal.end_date)
        else:
            self.dte_end_date.setDateTime(datetime.now())
        self.dte_end_date.setDisabled(True)
        grid.addWidget(QLabel("End date: "), current_row, LABEL_COL)
        grid.addWidget(self.dte_end_date, current_row, WIDGET_COL)
        current_row += 1

        self.btn_done = QPushButton("Done")
        self.btn_done.clicked.connect(self.update_goal)
        self.btn_done.setMinimumSize(50, 30)
        self.btn_done.setMaximumSize(100, 50)
        grid.addWidget(self.btn_done, current_row, LABEL_COL, 1, 2)

    def goal_type_selected(self):
        goal_type = self.combo_goal_type.currentText()
        disable_date_pickers = goal_type != GoalTypes.CUSTOM
        self.dte_begin_date.setDisabled(disable_date_pickers)
        self.dte_end_date.setDisabled(disable_date_pickers)

    def update_goal(self):
        self.goal.name = self.le_name.text()
        self.goal.target = self.dsp_goal.value()
        self.goal.goal_type = self.combo_goal_type.currentText()
        if self.goal.goal_type == GoalTypes.CUSTOM:
            self.goal.begin_date = self.dte_begin_date.dateTime().toPyDateTime()
            self.goal.end_date = self.dte_end_date.dateTime().toPyDateTime()
        self.signal_goal_edited.emit(self.goal)
        self.hide()

class CircularProgress(QWidget):
    signal_remove = pyqtSignal(QWidget)

    signal_goal_edited = pyqtSignal(Goal)
    signal_goal_progressed = pyqtSignal(Goal)
    signal_filter_update = pyqtSignal(int, FilterConfiguration)

    def __init__(self, goal : Goal = None, filter : dict = None , dict_values = None, max_width=300, max_height=300, parent = None):
        super().__init__(parent)
        self.goal = goal

        self.filterConfig = FilterConfiguration(data=filter, parent=self)

        # If a dict is given try loading goal and filter from it
        if not dict_values is None:
            self.from_dict(dict_values)
    
        self.goal_editor = GoalEditor(self.goal)

        vbox = QVBoxLayout(self)
        self.lbl_progress = QLabel("{:.1f}%".format(self.goal.current_progress / self.goal.target * 100))
        self.lbl_progress.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl_progress)

        self.lbl_progress_count = QLabel("{:.1f}/{:.1f}".format(self.goal.current_progress, self.goal.target))
        self.lbl_progress_count.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl_progress_count)

        self.lbl_name = QLabel(self.goal.name)
        self.lbl_name.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.lbl_name)

        vbox.setAlignment(Qt.AlignCenter)

        self.max_width = max_width
        self.max_height = max_height
        self.line_width_ratio = 0.05  # Line thickness as a ratio of the widget size
        self.bg_color = QColor(200, 200, 200)  # Background color (gray)
        self.progress_color = QColor(0, 150, 0)  # Progress color (blue)
        self.text_color = QColor(50, 50, 50)  # Color for the text in the center
        self.resize(self.max_width, self.max_height)  # Set the initial size of the widget

        self.setMinimumSize(self.max_width // 2, self.max_height // 2)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.on_refresh)
        self.refresh_timer.setInterval(60 * 1000) # 1 minute intervals
        self.refresh_timer.start()

        self.setContextMenuPolicy(3)  # Qt.CustomContextMenu
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.goal_editor.signal_goal_edited.connect(self.on_goal_edited)
        self.filterConfig.signal_close_window.connect(self.on_filter_window_close)

        self.fetch_thread_pool = QThreadPool(self)

    def on_refresh(self):
        def fetch_data():
            if self.filterConfig.model.rowCount() < 1:
                return
            begin_date, end_date = self.goal.get_date_range()
            hours = fetch_hours(self.filterConfig.to_aw_filter(), begin_date, end_date)
            if not hours is None:
                self.on_goal_progress(hours)
        self.fetch_thread_pool.start(fetch_data)

        
    def on_filter_window_close(self):
        self.signal_filter_update.emit(self.goal.goal_id, self.filterConfig)

    def from_dict(self, dict_values):
        self.goal.from_dict(dict_values["goal"])
        self.filterConfig.from_dict(dict_values["aw-filters"])

    def to_dict(self):
        return {
            "goal" : self.goal.to_dict(),
            "aw-filters": self.filterConfig.to_dict()
        }

    def on_goal_edited(self):
        self.lbl_name.setText(self.goal.name)
        self.signal_goal_edited.emit(self.goal)

    def edit_values_pop_up(self):
        if not self.goal_editor.isActiveWindow():
            self.goal_editor.show()

    def show_context_menu(self, position):
        # Create a QMenu object
        menu = QMenu(self)

        # Add some actions to the menu
        action1 = QAction("Edit goal", self)
        action2 = QAction("Configure aw filters", self)
        action3 = QAction("Delete", self)
        action4 = QAction("Quit", self)

        # Connect actions to methods
        action1.triggered.connect(self.edit_goal_action)
        action2.triggered.connect(self.configure_aw_filter_action)
        action3.triggered.connect(self.delete_action)
        action4.triggered.connect(QApplication.instance().quit)

        # Add the actions to the menu
        menu.addAction(action1)
        menu.addAction(action2)
        menu.addAction(action3)
        menu.addAction(action4)

        # Display the menu at the cursor position
        menu.exec_(self.mapToGlobal(position))

    def edit_goal_action(self):
        self.edit_values_pop_up()
    
    def configure_aw_filter_action(self):
        self.filterConfig.show()
    
    def delete_action(self):
        self.signal_remove.emit(self)

    def on_goal_progress(self, current_progress):
        self.goal.current_progress = current_progress
        self.lbl_progress.setText("{:.1f}%".format(self.goal.current_progress / self.goal.target * 100))
        self.lbl_progress_count.setText("{:.1f}/{:.1f}".format(self.goal.current_progress, self.goal.target))
        self.repaint()  # Redraw the widget whenever the value changes
        self.signal_goal_progressed.emit(self.goal)

    def paintEvent(self, event):
        # Painter setup
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Determine size and position based on the current widget size
        size = min(self.width(), self.height())  # Choose the smaller dimension
        line_width = int(size * self.line_width_ratio)
        left = (self.width() - size) // 2 + line_width
        top = (self.height() - size) // 2 + line_width

        horizontal_pad = (self.width() - size + 2 * line_width) // 2
        vertical_pad = (self.height() - size + 2 * line_width) // 2
        self.setContentsMargins(horizontal_pad, vertical_pad,
                                horizontal_pad, vertical_pad)

        rect = QRectF(left, top,
                      size - 2 * line_width,
                      size - 2 * line_width)

        # Draw background circle
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.bg_color)
        painter.drawEllipse(rect)

        # Draw progress arc
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(QColor(self.progress_color).darker(), line_width, Qt.SolidLine))
        arc_length = int(360 * (self.goal.current_progress / self.goal.target))  # Angle corresponding to the progress
        painter.drawArc(rect, -90 * 16, -arc_length * 16)


        font_size = int(size * 0.1)  # Set font size relative to the widget size
        self.lbl_progress.setFont(QFont("Arial", font_size, QFont.Weight.Bold))

        font_size = int(size * 0.05)  # Set font size relative to the widget size
        self.lbl_progress_count.setFont(QFont("Arial", font_size, QFont.Weight.DemiBold))

        font_size = int(size * 0.05)  # Set font size relative to the widget size
        self.lbl_name.setFont(QFont("Arial", font_size, QFont.Weight.DemiBold))

        # Finish painting
        painter.end()

        super().paintEvent(event)

    def resizeEvent(self, event):
        # Restrict the widget size to the maximum width and height
        new_width = min(self.width(), self.max_width)
        new_height = min(self.height(), self.max_height)
        self.resize(new_width, new_height)
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    root_widget = CircularProgress()
    root_widget.show()

    root_widget.resize(300, 300)

    # Update progress value for demonstration

    sys.exit(app.exec_())
