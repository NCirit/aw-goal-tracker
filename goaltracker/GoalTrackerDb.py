import sqlite3
import os, json
from goaltracker.Goal import Goal

class GoalTrackerDb:
    def __init__(self, force_init = False):
        self.con = self.init_db(force_init=force_init)

    def add_goal(self, goal : Goal):
        cur = self.con.cursor()
        inserted_goal = cur.execute(
            "INSERT INTO Goal (name, target, last_progress, type, active, begin_date, end_date, creation_date)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, unixepoch())",
            (goal.name, goal.target, goal.current_progress, goal.goal_type, goal.active, goal.begin_date, goal.end_date)
        )
        self.con.commit()

        return inserted_goal.lastrowid

    def get_goal_filter(self, goal_id : int):
        cur = self.con.cursor()
        goal_filter = cur.execute(
            "select filter from ActivityWatchFilter "
            "where goal_id = (?)",
            (goal_id, )
        )
        return goal_filter.fetchall()

    def get_goal(self, goal_id : int):
        cur = self.con.cursor()
        goal = cur.execute(
            "select * from Goal "
            "where id = (?)",
            (goal_id, )
        )
        return goal.fetchall()

    def deactivate_goal(self, goal_id : int):
        registered_goal = self.get_goal(goal_id)

        cur = self.con.cursor()
        if len(registered_goal) > 0:
            cur.execute(
                "UPDATE Goal "
                "SET active = 0 "
                "WHERE id = (?)",
                (goal_id, )
            )
            self.con.commit()
    
    def update_goal_progress(self, goal_id : int, current_progress):
        cur = self.con.cursor()
        cur.execute(
                "UPDATE Goal "
                "SET last_progress = (?) "
                "WHERE id = (?)",
                (current_progress, goal_id)
            )
        self.con.commit()

    def update_goal(self, goal : Goal):
        registered_goal = self.get_goal(goal.goal_id)

        cur = self.con.cursor()
        if len(registered_goal) > 0:
            cur.execute(
                "UPDATE Goal "
                "SET name = (?), target = (?), last_progress = (?), type = (?), active = (?), begin_date = (?), end_date = (?) "
                "WHERE id = (?)",
                (goal.name, goal.target, goal.current_progress, goal.goal_type, goal.active,
                goal.begin_date, goal.end_date, goal.goal_id)
            )
            self.con.commit()
        else:
            return self.add_goal(goal)
        return goal.goal_id

    def update_goal_filter(self, goal_id : int, activity_watch_filter : dict):
        cur = self.con.cursor()

        goal_filter = self.get_goal_filter(goal_id)

        if len(goal_filter) > 0:
            cur.execute(
                "UPDATE ActivityWatchFilter "
                "SET filter = (?) "
                "where goal_id = (?)",
                (json.dumps(activity_watch_filter), goal_id)
            )
        else:
            cur.execute(
                "INSERT INTO ActivityWatchFilter(goal_id, filter) "
                "VALUES(?, ?)",
                (goal_id, json.dumps(activity_watch_filter))
            )
        self.con.commit()

    def get_goals(self):
        cur = self.con.cursor()
        goals = cur.execute(
            "select * from Goal "
            "where active = 1"
        )
        return goals.fetchall()
    
    def get_goal_types(self):
        cur = self.con.cursor()
        goalType = cur.execute("select * from GoalType")
        return goalType.fetchall()

    def init_db(self, force_init = False):

        user_home = os.path.expanduser("~")
        db_file_name = "goaltracker.db"
        app_folder = os.path.join(user_home, ".goaltracker")
        if not os.path.exists(app_folder):
            os.makedirs(app_folder, exist_ok=True)
        
        db_path = os.path.join(app_folder, db_file_name)

        # If already exist, just return it
        if not force_init and os.path.exists(db_path):
            return sqlite3.connect(db_path)
        
        if os.path.exists(db_path):
            os.remove(db_path)

        # Create db and initialize
        con = sqlite3.connect(db_path)

        cur = con.cursor()
        
        cur.execute(
            "CREATE TABLE GoalType("
            "type PRIMARY KEY NOT NULL"
            ")"
        )

        cur.execute("INSERT INTO GoalType(type) VALUES ('daily')")
        cur.execute("INSERT INTO GoalType(type) VALUES ('monthly')")
        cur.execute("INSERT INTO GoalType(type) VALUES ('yearly')")
        cur.execute("INSERT INTO GoalType(type) VALUES ('custom')")

        goalType = cur.execute("select * from GoalType")
        print("Registered goal types:", goalType.fetchall())

        cur.execute(
            "CREATE TABLE Goal("
                "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
                "name VARCHAR NOT NULL,"
                "target REAL NOT NULL,"
                "last_progress REAL NOT NULL,"
                "type NOT NULL DEFAULT ('daily') REFERENCES GoalType(goal_type),"
                "active INTEGER NOT NULL DEFAULT (1),"
                "begin_date INTEGER,"
                "end_date INTEGER,"
                "creation_date INTEGER NOT NULL DEFAULT (unixepoch())"
            ")"
        )

        # cur.execute(
        #     "CREATE TABLE GoalProgress("
        #         "id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,"
        #         "goal_id INTEGER NOT NULL,"
        #         "progress REAL NOT NULL DEFAULT (0),"
        #         "begin_date INTEGER NOT NULL,"
        #         "end_date INTEGER NOT NULL,"
        #         "FOREIGN KEY(goal_id) REFERENCES Goal(id)"
        #     ")"
        # )

        cur.execute(
            "CREATE TABLE ActivityWatchFilter("
                "goal_id INTEGER PRIMARY KEY NOT NULL,"
                "filter VARCHAR NOT NULL,"
                "FOREIGN KEY(goal_id) REFERENCES Goal(id)"
            ")"
        )

        con.commit()
        return con

def main():
    tracker = GoalTrackerDb("testdb", True)
    goal_id = tracker.add_goal(Goal(name = "work", target = 120, current_progress=1))
    
    print(goal_id)
    print(tracker.get_goals())
    tracker.update_goal_filter(goal_id=goal_id, activity_watch_filter={"test":1})
    print(tracker.get_goal_filter(goal_id))
    pass

if __name__ == "__main__":
    main()