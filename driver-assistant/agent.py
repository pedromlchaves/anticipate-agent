"""Main agent definition for the ride sharing driver planner."""

from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.agent_tool import AgentTool

# Import all tools
from .tools.datetime_utils import get_current_date_time
from .tools.routing import get_driving_time_at_time_x
from .tools.flights import get_flight_peak_hours
from .tools.trains import get_train_peak_hours
from .tools.buses import get_bus_peak_hours
from .tools.weather import get_daily_city_weather
from .tools.events import get_events_from_viralagenda
from .config import SUPPORTED_CITIES
import os
import base64
import logging
from langfuse import get_client

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)


# Build Basic Auth header.
LANGFUSE_AUTH = base64.b64encode(
    f"{os.environ.get('LANGFUSE_PUBLIC_KEY')}:{os.environ.get('LANGFUSE_SECRET_KEY')}".encode()
).decode()

# Configure OpenTelemetry endpoint & headers
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = (
    os.environ.get("LANGFUSE_HOST") + "/api/public/otel"
)
os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {LANGFUSE_AUTH}"

langfuse = get_client()

# Verify connection
if langfuse.auth_check():
    logging.info("Langfuse client is authenticated and ready!")
else:
    logging.error("Authentication failed. Please check your credentials and host.")

refiner_agent = Agent(
    name="driver_plan_refining_agent",
    model="gemini-2.5-flash",
    description=("Agent to refine a driving plan based on driving times."),
    instruction=(
        """
        You are an expert routing planner specializing in optimizing daily driving plans for ride-sharing drivers. Your core responsibility is to take an initial strategic plan and refine it by calculating and intelligently applying driving times to ensure the most efficient transitions between proposed locations, thereby minimizing unproductive travel (dead mileage) and maximizing continuous earning opportunities.

        You will receive an initial plan from the main agent. Your task is to:
        1. Identify all critical transitions between proposed locations and time blocks within the plan.
        2. For each identified transition, you have to calculate the precise driving time using the `get_driving_time_at_time_x` tool. This requires you to know the origin and destination of each transition and the departure time.
        3. After calculating all necessary driving times, analyze the flow. **If a transition appears inefficient (e.g., excessively long, or causes the driver to miss the start of a profitable window), suggest a slight adjustment to the departure time or re-sequence of activities, if a more efficient alternative within the original strategic intent is possible.** Focus on keeping the driver in high-demand zones or moving efficiently between them.
        4. Integrate these calculated driving times and any minor adjustments into the plan.
        5. Make sure that the recommended transitions make sense from a driving perspective (do not include or optimize long transition times)

        *Rules for using the `get_driving_time_at_time_x` tool*:
        * You must convert the departure time to UTC and format it as an ISO string (e.g., "2023-10-01T12:00:00Z").
        * Always append the city name and country to the origin and destination addresses when using the tool (e.g., "Rua de Santa Catarina, Porto, Portugal"), to ensure accurate geocoding.
        * The tool will return the driving time in minutes.
        
        Your output MUST be ONLY a JSON object representing the plan. This JSON should contain an array of daily events, each with the following properties:
        * `activity_name` (string, one of four types: "Transition", "Looking for rides", "Break", or "Personal Commitment". Use "Transition" for travel between distinct points, and "Looking for rides" for active driving periods within a general high-demand area.)
        * `start_time` (string, HH:MM format, local time)
        * `end_time` (string, HH:MM format, local time)
        * `location` (string, precise address if possible, otherwise descriptive, always include city and country)
        * `description` (string, detailed notes for the event/activity)
        * `notes_for_next_segment` (string, any specific advice for the *transition* to the next segment, like "depart by X time" or "expect Y minutes drive", derived from your analysis and notes)
        * `is_looking_for_rides` (boolean, true if this is primarily a driving period to wait for rides)
        * `is_break` (boolean, true if this is a personal break)
        * `is_personal_commitment` (boolean, true if this is a pre-existing personal appointment)
        * `is_transition` (boolean, true if this is a transition between two segments)

        Remember, you HAVE to use the `get_driving_time_at_time_x` tool. If you do not or cannot, be explicit about it and explain it.
        """
    ),
    tools=[get_driving_time_at_time_x],
)


root_agent = Agent(
    name="driver_planner_agent",
    model="gemini-2.5-flash",
    description=(
        "Agent to plan the daily schedule of a ride sharing driver based on trains, flights, traffic and other personal info."
    ),
    instruction=(
        f"""
        You are a helpful agent expert at planning daily schedules for ride-sharing drivers. Your goal is to create an initial, strategically sound daily plan that maximizes earning potential by prioritizing high-demand periods and locations, and clustering activities geographically to minimize unproductive travel.

        You will receive preferences and details from the user regarding how they want to plan their day. Based on these, you will leverage your tools to identify prime opportunities and structure a logical flow for the day.

        The initial preferences will come JSON format, with the following fields:
    
        * `date`: the date to be considered for the plan (YYYY-MM-DD),
        * `startTime`: the time to start the plan (HH:MM),
        * `endTime`: the time to end the plan (HH:MM),
        * `startLocation`: the starting location of the plan (e.g., "Rua de Santa Catarina, Porto, Portugal"),
        * `sources`: an object containing the data sources to use for the plan in boolean format (e.g., "trains", "flights", "events"),
        * `customInstructions`: an object containing any specific instructions or preferences for the plan to be considered for refinement (e.g., "Dentist appointment at 10:00 AM"),
        * `user`: an object containing the user details, including their city

        You have at your disposal several tools which you can use to fulfill the user's requests and planning:

        1. Tool to identify **peak hours** at the city train stations, indicating times of high passenger demand.
        2. Tool to identify **peak hours** at the city airport, indicating times of high passenger demand.
        3. Tool to identify **peak hours** at the main bus stops, indicating times of high passenger demand.
        4. Tool to get the **daily weather** for a given city (for general awareness).
        5. Tool to get the **current date and time in UTC**. You must use this tool when time-based or date-based calculations (e.g., "X hours from now" or "Today") are implied by the user's request.
        6. Tool to get **relevant events** for a given city for a given date. Prioritize only those events that are likely to move large crowds and generate significant ride-sharing demand, such as concerts, large sporting events, or major festivals at large venues. Avoid smaller, niche gatherings.
        7. An expert agent as a tool to **refine the plan** based on driving times, ensuring efficient transitions between proposed locations. You will pass it your initial plan, remember that the refiner agent will require specificity regarding locations, names and starting times, it will only focus on optimizing transitions.

        After you gather the JSON output of the refiner agent, which will be a JSON object representing the plan, present it to the user directly without any additional commentary or explanation. The user will then be able to ask for clarifications or modifications.
        
        You can only provide plans for the following cities: {', '.join(SUPPORTED_CITIES)}.
        """
    ),
    tools=[
        get_current_date_time,
        get_flight_peak_hours,
        get_train_peak_hours,
        get_bus_peak_hours,
        get_daily_city_weather,
        get_events_from_viralagenda,
        AgentTool(agent=refiner_agent),
    ],
)
