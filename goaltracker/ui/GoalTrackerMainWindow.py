import json
from datetime import datetime

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QWidget, QVBoxLayout, \
    QHBoxLayout

from goaltracker.ui.CircularProgress import CircularProgress
from goaltracker.ui.FilterConfiguration import FilterConfiguration
from goaltracker.GoalTrackerDb import GoalTrackerDb
from goaltracker.Goal import Goal

class GoalTrackerMainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Enable window transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        self.goal_tracker_db = GoalTrackerDb()

        root_layout = QHBoxLayout(self)

        self.vbox = QVBoxLayout()
        root_layout.addLayout(self.vbox)

        goals = self.goal_tracker_db.get_goals()

        self.goal_widgets = []

        if len(goals) > 0:
            for agoal in goals:
                goal_id, goal_name, goal_target,\
                goal_current_progress, goal_type, \
                goal_active, begin_date,\
                end_date, creation_date = agoal
                
                # Convert unix timestamp to python datetime
                if begin_date:
                    begin_date = datetime.fromtimestamp(begin_date)
                
                if end_date:
                    end_date = datetime.fromtimestamp(end_date)

                goal = Goal(goal_id=goal_id, current_progress=goal_current_progress, name = goal_name, target = goal_target,
                    goal_type=goal_type, begin_date=begin_date, end_date=end_date)
                
                goal_filter = self.goal_tracker_db.get_goal_filter(goal_id)
                filter = None
                if len(goal_filter) > 0:
                    filter = json.loads(goal_filter[0][0])

                self.create_and_register_goal_widget(goal=goal, filter=filter)
        else:
            self.add_place_holder_goal()

        self.setWindowTitle("Goal Tracker")

        self.is_dragging = False
        self.drag_position = QPoint()
    
    
    def create_and_register_goal_widget(self, goal : Goal, filter : dict = None):
        goal_widget = CircularProgress(goal=goal, filter = filter)
        goal_widget.signal_goal_edited.connect(self.on_goal_update)
        goal_widget.signal_goal_progressed.connect(self.on_goal_progress)
        goal_widget.signal_filter_update.connect(self.on_filter_update)
        goal_widget.signal_remove.connect(self.on_progress_delete)
        self.vbox.addWidget(goal_widget)
        self.goal_widgets.append(goal_widget)

    def on_goal_update(self, goal : Goal):
        self.goal_tracker_db.update_goal(goal)
    
    def on_goal_progress(self, goal : Goal):
        self.goal_tracker_db.update_goal_progress(goal.goal_id, goal.current_progress)

    def on_filter_update(self, goal_id : int, filterConfig : FilterConfiguration):
        self.goal_tracker_db.update_goal_filter(goal_id, filterConfig.to_dict())

    def on_progress_delete(self, widget : CircularProgress):
        widget.goal.active = 0
        self.goal_tracker_db.deactivate_goal(widget.goal.goal_id)
        self.vbox.removeWidget(widget)
        self.goal_widgets.remove(widget)

        if len(self.goal_widgets) == 0:
            self.add_place_holder_goal()

    def add_place_holder_goal(self):
        goal = Goal(name = "New Goal", target=100, current_progress=75)
        goal.goal_id = self.goal_tracker_db.add_goal(goal)
        self.create_and_register_goal_widget(goal=goal)

    def mouseDoubleClickEvent(self, event):
        self.add_place_holder_goal()
    
    def mousePressEvent(self, event):
        # Check if the ALT key is pressed and the left mouse button is clicked
        if event.button() == Qt.LeftButton and event.modifiers() == Qt.AltModifier:
            self.is_dragging = True
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        # Move the window if dragging
        if self.is_dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        # Stop dragging when the mouse button is released
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            event.accept()
    
    def wheelEvent(self, event):
        # Check if the Ctrl key is pressed
        if event.modifiers() == Qt.ControlModifier:
            # Get the angle delta of the wheel event
            delta = event.angleDelta().y()

            # Determine the resize factor (you can adjust this value)
            resize_factor = 1.05 if delta > 0 else 0.95

            # Calculate new width and height
            new_width = int(self.width() * resize_factor)
            new_height = int(self.height() * resize_factor)

            # Resize the window
            self.resize(new_width, new_height)