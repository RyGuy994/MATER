from flask import Blueprint, request, render_template, jsonify, Response
from icalendar import Calendar

from models.service import Service
calendar_blueprint = Blueprint('calendar', __name__, template_folder='../templates')

@calendar_blueprint.route('/calendar')
def calendar():
    return render_template('calendar.html')

@calendar_blueprint.route('/api/events') # Normal endpoint for all events
def api_events():
    services = Service.query.all()
    calendar_events = [service.to_calendar_event() for service in services]
    return jsonify(calendar_events)

@calendar_blueprint.route('/api/events/completed') # Endpoint for completed events
def api_events_completed():
    complete_services = Service.query.filter_by(service_complete=True).all()
    calendar_events_completed = [service.to_calendar_event() for service in complete_services]
    return jsonify(calendar_events_completed)

@calendar_blueprint.route('/api/events/incomplete') # Endpoint for incomplete events
def api_events_incomplete():
    incomplete_services = Service.query.filter_by(service_complete=False).all()
    calendar_events_incomplete = [service.to_calendar_event() for service in incomplete_services]
    return jsonify(calendar_events_incomplete)

@calendar_blueprint.route('/ical/events') # ical events
def ical_events():
    services = Service.query.all() # query all services
    cal = Calendar() # set calendar
    for service in services: #for services in Class services
        cal_event = service.to_icalendar_event() # change to event
        cal.add_component(cal_event) # add event
    response = Response(cal.to_ical(), content_type='text/calendar; charset=utf-8') # set text
    response.headers['Content-Disposition'] = 'attachment; filename=events.ics' # set as attachment
    return response # send response

@calendar_blueprint.route('/ical/subscribe')
def ical_subscribe():
    base_url = request.url_root # Retrieve the base URL of your application
    cal = Calendar() # Generate iCalendar data for subscription
    services = Service.query.all() # get services
    for service in services: # for services in Class services
        cal_event = service.to_icalendar_event() # change to event
        cal.add_component(cal_event) # add event
    ical_url = base_url + 'ical/events' # Generate the full iCalendar URL for subscription
    cal.add('method', 'PUBLISH') # Add the iCalendar URL to the response
    cal.add('X-WR-CALNAME', 'MATER')  # Calendar Name **ADDADD Maybe let user set this**
    response = Response(cal.to_ical(), content_type='text/calendar') # set text
    response.headers['Content-Disposition'] = 'inline; filename=calendar.ics' # set as attachment
    return response # send response