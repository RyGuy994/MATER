from flask import Blueprint, request, jsonify, Response, current_app
from icalendar import Calendar
from utils.jwt.jwt_utils import retrieve_username_jwt
from models.service import Service

calendar_blueprint = Blueprint("calendar", __name__, template_folder="../templates")

@calendar_blueprint.route("/calendar/api/events")  # Normal endpoint for all events
def api_events():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    if not user_id:
        return jsonify({"error": "Invalid or missing JWT token."}), 401  # Unauthorized

    # Fetch all services for the user
    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter(Service.user_id == user_id)
        .all()
    )
    calendar_events = [service.to_calendar_event() for service in services]
    return jsonify(calendar_events)

@calendar_blueprint.route("/calendar/api/events/completed")  # Endpoint for completed events
def api_events_completed():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    if not user_id:
        return jsonify({"error": "Invalid or missing JWT token."}), 401  # Unauthorized

    # Fetch completed services (where service_status is 'Complete')
    complete_services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter(
            Service.service_status == "Complete",  # Adjusted to check service_status
            Service.user_id == user_id,
        )
        .all()
    )
    calendar_events_completed = [
        service.to_calendar_event() for service in complete_services
    ]
    return jsonify(calendar_events_completed)

@calendar_blueprint.route("/calendar/api/events/incomplete")  # Endpoint for incomplete events
def api_events_incomplete():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    if not user_id:
        return jsonify({"error": "Invalid or missing JWT token."}), 401  # Unauthorized

    # Fetch incomplete services (where service_status is not 'Complete')
    incomplete_services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter(
            Service.service_status != "Complete",  # Adjusted to check service_status
            Service.user_id == user_id,
        )
        .all()
    )
    calendar_events_incomplete = [
        service.to_calendar_event() for service in incomplete_services
    ]
    return jsonify(calendar_events_incomplete)

@calendar_blueprint.route("/calendar/ical/events")  # iCal events
def ical_events():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    if not user_id:
        return jsonify({"error": "Invalid or missing JWT token."}), 401  # Unauthorized

    # Fetch all services for the user
    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter(Service.user_id == user_id)
        .all()
    )
    cal = Calendar()  # Create iCalendar object
    for service in services:
        cal_event = service.to_icalendar_event()
        cal.add_component(cal_event)
    
    response = Response(
        cal.to_ical(), content_type="text/calendar; charset=utf-8"
    )
    response.headers["Content-Disposition"] = "attachment; filename=events.ics"
    return response

@calendar_blueprint.route("/calendar/ical/subscribe")
def ical_subscribe():
    base_url = request.url_root
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    if not user_id:
        return jsonify({"error": "Invalid or missing JWT token."}), 401  # Unauthorized

    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .filter(Service.user_id == user_id)
        .all()
    )
    cal = Calendar()
    for service in services:
        cal_event = service.to_icalendar_event()
        cal.add_component(cal_event)
    
    cal.add("method", "PUBLISH")
    cal.add("X-WR-CALNAME", request.args.get("calendar_name", "User Calendar"))
    
    response = Response(cal.to_ical(), content_type="text/calendar")
    response.headers["Content-Disposition"] = "inline; filename=calendar.ics"
    return response
