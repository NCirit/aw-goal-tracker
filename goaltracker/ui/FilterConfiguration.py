import sys, json
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeView, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QCheckBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class AwFilterTreeView(QTreeView):
    def __init__(self, parent : QWidget = None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        # Check if the clicked position is on a valid index
        index = self.indexAt(event.pos())
        if not index.isValid():
            # If clicked on an empty area, clear the selection
            self.clearSelection()

        # Call the base class implementation
        super().mousePressEvent(event)


class FilterConfiguration(QWidget):
    signal_close_window = pyqtSignal()

    def __init__(self, parent : QWidget = None, data : dict = None, filter_afk: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Goal aw filter configuration")
        self.setGeometry(200, 100, 600, 400)
        self.setWindowFlags(Qt.Tool)

        layout = QVBoxLayout(self)

        # Tree view setup
        self.tree_view = AwFilterTreeView(self)
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Category", "Ignore Case", "Regex Filter"])

        self.filter_afk = filter_afk

        # Populate the tree with data
        if not data is None:
            self.from_dict(data)

        # Set the model to the tree view
        self.tree_view.setModel(self.model)

        layout.addWidget(self.tree_view)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        
        btnAdd = QPushButton("Add")
        btnDelete = QPushButton("Delete")

        btnAdd.setMinimumSize(50, 30)
        btnAdd.setMaximumSize(100, 50)
        btnDelete.setMinimumSize(50, 30)
        btnDelete.setMaximumSize(100, 50)

        self.chkBoxFilterAfk = QCheckBox("Filter Afk")

        if self.filter_afk:
            self.chkBoxFilterAfk.setCheckState(Qt.Checked)

        self.chkBoxFilterAfk.stateChanged.connect(self.on_filter_afk_checkbox_change)

        hbox.addWidget(self.chkBoxFilterAfk)
        hbox.addWidget(QLabel())
        hbox.addWidget(btnAdd)
        hbox.addWidget(btnDelete)

        btnAdd.clicked.connect(self.on_add_clicked)
        btnDelete.clicked.connect(self.on_delete_clicked)

        self.model.dataChanged.connect(self.on_data_changed)

    def closeEvent(self, event):
        self.signal_close_window.emit()
        super().closeEvent(event)

    def on_data_changed(self, top_left, bottom_right, roles):
        self.save_settings()
    
    def on_delete_clicked(self):
        self.delete_selected()

    def on_add_clicked(self):
        indexes = self.tree_view.selectedIndexes()

        if len(indexes) < 1:
            item = self.model
        else:
            index = indexes[0]
            item = self.model.itemFromIndex(index)

        # Get the item that was double-clicked
        
        # Create new items for the new row
        new_child = QStandardItem("New Item")
        new_child_desc = QStandardItem("New Description")
        new_child_checkbox = self.create_checkbox_item()

        # Add the new row as a child of the double-clicked item
        item.appendRow([new_child, new_child_checkbox, new_child_desc])
        self.save_settings()

    def on_filter_afk_checkbox_change(self, state):
        self.filter_afk = state == Qt.Checked

    def save_settings(self):
        with open("temp.txt", "w")  as fl:
            json.dump(self.to_dict(), fl, indent=4)

    def from_dict(self, data : dict):
        
        if "sub_categories" not in data.keys():
            return

        category_stack = []
        category_stack.append([None, data["sub_categories"]])
        parent = None
        while len(category_stack) > 0:
            parent, sub_categories = category_stack.pop(0)

            for category_info in sub_categories:
                category = QStandardItem(category_info["category"])
                ignore_case = self.create_checkbox_item(category_info["ignore_case"])
                filter_regex = QStandardItem(category_info["filter"])
                if parent is None:
                    parent = self.model
                
                parent.appendRow([category, ignore_case, filter_regex])
                if len(category_info["sub_categories"]) > 0:
                    category_stack.append([category, category_info["sub_categories"]])
        return
        
    def create_checkbox_item(self, checked : bool = False):
        # Create a checkable item
        checkbox_item = QStandardItem()
        checkbox_item.setCheckable(True)
        checkbox_item.setCheckState(Qt.Checked if checked else Qt.Unchecked)
        return checkbox_item
    
    def delete_selected(self):
        selected_indexes = self.tree_view.selectedIndexes()

        if selected_indexes:
            # Get the top-level index of the selected item
            selected_row = selected_indexes[0].row()
            parent_index = selected_indexes[0].parent()

            # Remove the selected row
            if parent_index.isValid():
                parent_item = self.model.itemFromIndex(parent_index)
                parent_item.removeRow(selected_row)
            else:
                self.model.removeRow(selected_row)
            self.save_settings()

    def keyPressEvent(self, event):
        # Check if the Delete key is pressed
        if event.key() == Qt.Key_Delete:
            # Get the selected indexes
            self.delete_selected()

        # Call the base class event handler
        super().keyPressEvent(event)

    def get_filter_categories(self) -> list:
        result = []
        categories_stack = [[None, self.model]]
        while len(categories_stack) > 0:
            parent_path, category = categories_stack.pop(0)
            if parent_path is None:
                parent_path = []
                get_child = self.model.item
            else:
                get_child = category.child

            for i in range(category.rowCount()):
                path = []
                path.extend(parent_path)
                path.append(get_child(i, 0).text())
                result.append(tuple(path))
                categories_stack.append([path, get_child(i)])
        return result

    def to_aw_filter(self) -> list:
        categories_stack = [[None, self.model]]
        result = []
        while len(categories_stack) > 0:
            parent_path, category = categories_stack.pop(0)
            if parent_path is None:
                parent_path = []
                get_child = self.model.item
            else:
                get_child = category.child

            for i in range(category.rowCount()):
                path = []
                path.extend(parent_path)
                path.append(get_child(i, 0).text())
                temp_dict = {
                    "type" : "regex",
                    "ignore_case" : get_child(i, 1).checkState() == Qt.Checked,
                    "regex" : get_child(i, 2).text(),
                }
                result.append([path, temp_dict])
                categories_stack.append([path, get_child(i)])
        return result
    
    def to_dict(self):
        categories_stack = [[None, self.model]]
        result = {"sub_categories" : []}
        while len(categories_stack) > 0:
            parent_dict, category = categories_stack.pop(0)
            if parent_dict is None:
                parent_dict = result
                get_child = self.model.item
            else:
                get_child = category.child

            for i in range(category.rowCount()):
                temp_dict = {
                    "category" : get_child(i, 0).text(),
                    "ignore_case" : get_child(i, 1).checkState() == Qt.Checked,
                    "filter" : get_child(i, 2).text(),
                    "sub_categories" : []
                }
                parent_dict["sub_categories"].append(temp_dict)
                categories_stack.append([temp_dict, get_child(i)])
        return result

if __name__ == "__main__":
    example_tree = {
    "sub_categories" :[
        {
            "category" : "Work",
            "filter" : "filter" ,
            "ignore_case" : True,
            "sub_categories" : [
                {
                "category" : "test",
                "filter" : "filter" ,
                "ignore_case" : True,
                "sub_categories" : [
                    
                ]
            },
            {
                "category" : "test3",
                "filter" : "filter" ,
                "ignore_case" : False,
                "sub_categories" : [
                    
                ]
            }
            ]
        },
        {
                "category" : "test123",
                "filter" : "filter" ,
                "ignore_case" : True,
                "sub_categories" : [
                    
                ]
        }
    ]
    }
    app = QApplication(sys.argv)
    window = QMainWindow()

    # Layout setup
    #window.setLayout(layout)

    treeview = FilterConfiguration(window, example_tree)
    window.setCentralWidget(treeview)

    print(json.dumps(treeview.to_aw_filter()))
    window.show()
    sys.exit(app.exec_())