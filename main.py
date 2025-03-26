from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserQuery(BaseModel):
    query: str

@app.post("/query/")
def user_query(user_query: UserQuery):
    return """{
  "type": "chart",
  "chartType": "line",
  "title": "Pod CPU Usage",
  "crossAxis": {
    "label": "Time",
    "unit": "date"
  },
  "dependentAxis": {
    "label": "CPU Usage",
    "type": "cores"
  },
  "data": [
    {
      "x": "2016-06-03T01:00:00",
      "y": 2.4
    },
    {
      "x": "2016-06-03T02:00:00",
      "y": 3.1
    },
    {
      "x": "2016-06-03T03:00:00",
      "y": 5.7
    },
    {
      "x": "2016-06-04T01:00:00",
      "y": 2.1
    },
    {
      "x": "2016-06-04T05:00:00",
      "y": 2.6
    },
    {
      "x": "2016-06-04T06:00:00",
      "y": 3.3
    }
  ]
}"""