from flask import Blueprint, request, render_template, jsonify, Response, current_app
from icalendar import Calendar

from blueprints.utilities import retrieve_username_jwt
from models.service import Service

calendar_blueprint = Blueprint("calendar", __name__, template_folder="../templates")


@calendar_blueprint.route("/calendar")
def calendar():
    print(request.cookies)
    return render_template(
        "calendar.html", loggedIn=True
    )  # Assuming the user is logged in


@calendar_blueprint.route("/calendar/api/events")  # Normal endpoint for all events
def api_events():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .query.filter(Service.user_id == user_id)
        .all()
    )
    calendar_events = [service.to_calendar_event() for service in services]
    return jsonify(calendar_events)


@calendar_blueprint.route(
    "/calendar/api/events/completed"
)  # Endpoint for completed events
def api_events_completed():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    complete_services = (
        current_app.config["current_db"]
        .session.query(Service)
        .query.filter(
            Service.service_complete
            == True,  # set service_completed to true for completed services
            Service.user_id == user_id,
        )
        .all()
    )
    calendar_events_completed = [
        service.to_calendar_event() for service in complete_services
    ]
    return jsonify(calendar_events_completed)


@calendar_blueprint.route(
    "/calendar/api/events/incomplete"
)  # Endpoint for incomplete events
def api_events_incomplete():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    incomplete_services = (
        current_app.config["current_db"]
        .session.query(Service)
        .query.filter(
            Service.service_complete
            == False,  # set service_completed to false for incompleted services
            Service.user_id == user_id,
        )
        .all()
    )
    calendar_events_incomplete = [
        service.to_calendar_event() for service in incomplete_services
    ]
    return jsonify(calendar_events_incomplete)


@calendar_blueprint.route("/calendar/ical/events")  # ical events
def ical_events():
    user_id = retrieve_username_jwt(request.cookies.get("access_token"))
    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .query.filter_by(user_id=user_id)
        .all()
    )  # query all services
    cal = Calendar()  # set calendar
    for service in services:  # for services in Class services
        cal_event = service.to_icalendar_event()  # change to event
        cal.add_component(cal_event)  # add event
    response = Response(
        cal.to_ical(), content_type="text/calendar; charset=utf-8"
    )  # set text
    response.headers[
        "Content-Disposition"
    ] = "attachment; filename=events.ics"  # set as attachment
    return response  # send response


@calendar_blueprint.route("/calendar/ical/subscribe")
def ical_subscribe():
    base_url = request.url_root  # Retrieve the base URL of your application
    cal = Calendar()  # Generate iCalendar data for subscription
    user_id = retrieve_username_jwt()
    services = (
        current_app.config["current_db"]
        .session.query(Service)
        .query.filter_by(user_id=user_id)
        .all()
    )  # get services
    for service in services:  # for services in Class services
        cal_event = service.to_icalendar_event()  # change to event
        cal.add_component(cal_event)  # add event
    ical_url = (
        base_url + "calendar/ical/events"
    )  # Generate the full iCalendar URL for subscription
    cal.add("method", "PUBLISH")  # Add the iCalendar URL to the response
    cal.add("X-WR-CALNAME", request.args.get("calendar_name"))  # Calendar Name
    response = Response(cal.to_ical(), content_type="text/calendar")  # set text
    response.headers[
        "Content-Disposition"
    ] = "inline; filename=calendar.ics"  # set as attachment
    return response  # send response
