import json
from datetime import datetime, timezone, timedelta
import calendar

class GoalTypes:
    CUSTOM = "custom"
    DAILY = "daily"
    MONTHLY = "monthly"
    YEARLY = "yearly"

class Goal:
    def __init__(self, goal_id = None, name = "", target = 1, current_progress = 0, 
            goal_type = GoalTypes.DAILY, active = True, begin_date : datetime = None, end_date : datetime = None, dict_values : dict = None):
        self.name = name
        self.target = target
        self.current_progress = current_progress
        self.goal_type = goal_type
        self.goal_id = goal_id

        self.begin_date = begin_date
        self.end_date = end_date
        self.active = active

        if not dict_values is None:
            self.from_dict(dict_values)
    
    def get_date_range(self):
        begin_date, end_date = None, None
        if self.goal_type == GoalTypes.CUSTOM:
            begin_date, end_date = self.begin_date, self.end_date
        elif self.goal_type == GoalTypes.DAILY:
            begin_date = datetime.now(timezone(timedelta(hours=3)))
            begin_date = begin_date.replace(hour=0, minute=0, second=0, microsecond=0)

            end_date = datetime.now(timezone(timedelta(hours=3)))
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=0)
        elif self.goal_type == GoalTypes.MONTHLY:
            begin_date = datetime.now(timezone(timedelta(hours=3)))
            begin_date = begin_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            end_date = datetime.now(timezone(timedelta(hours=3)))
            end_date = end_date.replace(day = calendar.monthrange(end_date.year, end_date.month)[1], hour=23, minute=59, second=59, microsecond=0)
        elif self.goal_type == GoalTypes.YEARLY:
            begin_date = datetime.now(timezone(timedelta(hours=3)))
            begin_date = begin_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

            end_date = datetime.now(timezone(timedelta(hours=3)))
            end_date = end_date.replace(month=12, day = calendar.monthrange(end_date.year, end_date.month)[1],hour=23, minute=59, second=59, microsecond=0)
        else:
            raise Exception("Unkown goal type: {}".format(self.goal_type))

        return begin_date, end_date

    def from_dict(self, dict_values : dict):
        self.name = dict_values["name"]
        self.target = dict_values["target"]
        self.current_progress = dict_values["current_progress"]
        self.goal_type = dict_values["goal_type"]
        self.goal_id = dict_values["goal_id"]
        self.begin_date = dict_values["begin_date"]
        self.end_date = dict_values["end_date"]
        self.active = dict_values["active"]

    def to_dict(self):
        return {
            "name" : self.name,
            "target" : self.target,
            "current_progress" : self.current_progress,
            "goal_id": self.goal_id,
            "goal_type" : self.goal_type,
            "begin_date" : self.begin_date,
            "end_date" : self.end_date,
            "active": self.active
        }