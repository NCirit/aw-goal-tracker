# Goal tracker is for keeping track of your working hours and your goals

Goal tracker is a desktop widget that allows you set daily, monthly, or etc. goals with custom filters. It depends on activity watch as it gets the date from it. Every goal you create has some activity watch filters to that basically specify how you measure the progress of your goal.

## Requirements
- Python3
- [Activity Watch](https://activitywatch.net/downloads/) needs to be installed as the app gets the data from it. 

## Installation

```
pip install git+ssh://github.com/NCirit/aw-goal-tracker.git
```



## Usage:

`pythonw` starts the app in the background with the following command.

```
pythonw -m goaltracker
```

## UI previews

![progress ui](images/progressui.png)
![config menu](images/configmenu.png)
![goal edit](images/goaleditor.png)
![filter configuration](images/filterconfig.png)