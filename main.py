
import os

from uuid import uuid4

from fastapi import FastAPI

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.client_tool import client_tool
from llama_stack_client.lib.agents.event_logger import EventLogger
from llama_stack_client.types.agent_create_params import AgentConfig
from llama_stack_client.types.toolgroup_register_params import McpEndpoint

from prometheus_api_client import PrometheusConnect
from prometheus_api_client.utils import parse_datetime

from pydantic import BaseModel

from termcolor import colored

# i don't know a better way to do this than a global
charts_and_graphs = []

# pydantic objects
class UserQuery(BaseModel):
    query: str

class ChartAxis(BaseModel):
    label: str
    unit_or_type: str

class ChartDataPoint(BaseModel):
    x: str
    y: str

class MetricChart(BaseModel):
    type: str = "chart"
    chartType: str = "line"
    title: str
    crossAxis: ChartAxis
    dependentAxis: ChartAxis
    data: list[ChartDataPoint]

# define tools
@client_tool
def get_prometheus_metrics():
    """Get the list of all of the prometheus metrics available

    :returns: a plaintext list of the kind object in the namespace
    """
    output = prom.all_metrics()
    return str(output)

@client_tool
def prometheus_query(query: str):
    """Execute a custom instantaneous prometheus query
    
:param query: the promql query to execute
:returns: the prometheus output data
"""

    print(f"prometheus_query: {query}")

    output = prom.custom_query(query=query)

    ## add this data to the charts and graphs output
    #global charts_and_graphs

    #new_chart = MetricChart(type="chart", chartType="line", 
    #                        title="My Chart", 
    #                        crossAxis=ChartAxis(label="Time", unit_or_type="date"),
    #                        dependentAxis=ChartAxis(label="stuff", unit_or_type="thingy"),
    #                        data=[ChartDataPoint(x="1",y="2")])
    #charts_and_graphs.append(new_chart)
    return str(output)

@client_tool
def prometheus_range_query(query: str, minutes_ago: int = 5):
    """Perform a ranged Prometheus query using default step size.

:param query: PromQL expression.
:param minutes_ago: How many minutes back to query from now.
:returns: Range query result.
"""

    print(f"prometheus range query: {query} | time: {minutes_ago}")

    end_time = parse_datetime("now")
    start_time = parse_datetime(f"{minutes_ago}m")

    result = prom.custom_query_range(
        query=query,
        start_time=start_time,
        end_time=end_time,
        step=15
    )

    if type(result) is list and len(result) > 0:
        # add this data to the charts and graphs output
        global charts_and_graphs

        for indiv in result:
          # build the list of data points
          data_points = []
          for dp in indiv['values']:
              data_points.append(ChartDataPoint(x = str(dp[0]), y = str(dp[1])))

          new_chart = MetricChart(type="chart", chartType="line", 
                                  title=query, 
                                  crossAxis=ChartAxis(label="Time", unit_or_type="date"),
                                  dependentAxis=ChartAxis(label="stuff", unit_or_type="thingy"),
                                  data=data_points)
          charts_and_graphs.append(new_chart)

    return result

# set up the prometheus client
prom = PrometheusConnect(url=os.environ['PROMETHEUS_URL'], disable_ssl=True, headers={"Authorization": f"bearer {os.environ['PROMETHEUS_TOKEN']}"})

client = LlamaStackClient(
    base_url=f"http://{os.environ['LLAMA_HOST']}:{os.environ['LLAMA_PORT']}",
)

available_shields = [shield.identifier for shield in client.shields.list()]
if not available_shields:
    print(colored("No available shields. Disabling safety.", "yellow"))
else:
    print(f"Available shields found: {available_shields}")

available_models = [
    model.identifier for model in client.models.list() if model.model_type == "llm"
]

# the model decision logic is basic
if not available_models:
    print(colored("No available models. Exiting.", "red"))
else:
    selected_model = available_models[0]
    print(f"Using model: {selected_model}")

#mcp_ep : McpEndpoint = { 'uri' : "http://localhost:8989/sse" }
#client.toolgroups.register(
#    toolgroup_id="mcp::grafana",
#    provider_id="model-context-protocol",
#    mcp_endpoint=mcp_ep,
#)

client_tools = [get_prometheus_metrics, prometheus_query, prometheus_range_query]

agent_config = AgentConfig(
    model=selected_model,
    instructions="You are a helpful assistant.",
    sampling_params={
        "strategy": {"type": "top_p", "temperature": 1.0, "top_p": 0.9},
    },
    toolgroups=(
        [
        ]
    ),
    client_tools=[
        client_tool.get_tool_definition() for client_tool in client_tools
    ],
    tool_choice="auto",
    input_shields=[], #available_shields if available_shields else [],
    output_shields=[], #available_shields if available_shields else [],
    enable_session_persistence=False,
)
agent = Agent(client, agent_config, client_tools)

app = FastAPI()

@app.post("/fixed/")
def ignore_query(user_query: UserQuery):
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

@app.post("/query/")
def user_query(user_query: UserQuery):
    session_id = agent.create_session(str(uuid4()))

    # re-initialize the charts and graphs to be the empty set
    global charts_and_graphs
    charts_and_graphs = []

    response = agent.create_turn(
        messages=[
            {
                "role": "user",
                "content": user_query.query,
            }
        ],
        session_id=session_id,
        stream=False
    )

    llm_responses = response.output_message.content

    final_response = {
        "llm_responses" : llm_responses,
        "charts_and_graphs" : charts_and_graphs
    }

    return(final_response)
