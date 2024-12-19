from goaltracker.ui.GoalTrackerMainWindow import GoalTrackerMainWindow
import sys
from PyQt5.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)

    root_widget = GoalTrackerMainWindow()
    root_widget.show()

    #root_widget.resize(300, 300)

    app.aboutToQuit.connect(root_widget.save_window_geometry)
    # Update progress value for demonstration
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()