from common import *

def get_attendee(full_name, email, zip_code):
    words = full_name.split()
    for i in range(1, len(words)):
        first, last = " ".join(words[:i]), " ".join(words[i:])
        attendee = Attendee.objects.filter(first_name__iexact=first, last_name__iexact=last,
                                           email__iexact=email, zip_code=zip_code)
        if attendee:
            return attendee[0]
    raise ValueError("attendee not found")

@all_renderable(SIGNUPS)
class Root:
    def index(self, message = ""):
        return {
            "message": message,
            "attendee": Attendee.objects.get(id = cherrypy.session["staffer_id"])
        }
    
    def fire_safety(self, message = "", fire_safety_cert = None):
        attendee = Attendee.objects.get(id = cherrypy.session["staffer_id"])
        if fire_safety_cert is not None:
            if not re.match(r"^\d{5}\.\d{10}$", fire_safety_cert):
                message = "That is not a valid certification number"
            else:
                attendee.fire_safety_cert = fire_safety_cert
                attendee.save()
                raise HTTPRedirect("index?message={}", "Your fire safety certification has been received")
        
        return {
            "message": message,
            "attendee": attendee,
            "fire_safety_cert": fire_safety_cert or ""
        }
    
    def hotel_requests(self, message = "", decline = None, **params):
        attendee = Attendee.objects.get(id = cherrypy.session["staffer_id"])
        requests = get_model(HotelRequests, params, checkgroups = ["nights"], restricted = True)
        if "attendee_id" in params:
            if decline or not requests.nights:
                requests.nights = ""
                requests.save()
                raise HTTPRedirect("index?message={}", "We've recorded that you've declined hotel room space")
            else:
                requests.save()
                nondefault = set(map(int, requests.nights.split(","))) - {THURSDAY, FRIDAY, SATURDAY}
                if nondefault:
                    days = " / ".join(dict(NIGHTS_OPTS)[day] for day in sorted(nondefault))
                    message = "Your hotel room request has been submitted.  We'll let you know whether your offer to help on {} is accepted, and who your roommates will be, in the first week of December.".format(days)
                else:
                    message = "You've accepted hotel room space for Thursday / Friday / Saturday.  We'll let you know your roommates in the first week of December."
                raise HTTPRedirect("index?message={}", message)
        else:
            requests = attendee.hotel_requests or requests
        
        return {
            "message":  message,
            "requests": requests,
            "attendee": attendee
        }
    
    def schedule(self, message = ""):
        return {
            "message":  message,
            "attendee": Attendee.objects.get(id = cherrypy.session["staffer_id"])
        }
    
    def possible(self, message = ""):
        return {
            "message":  message,
            "attendee": Attendee.objects.get(id = cherrypy.session["staffer_id"])
        }
    
    def sign_up(self, job_id):
        message = assign(cherrypy.session["staffer_id"], job_id) or "Signup successful"
        raise HTTPRedirect("possible?message={}", message)
    
    def drop(self, shift_id):
        Shift.objects.filter(id=shift_id, attendee = cherrypy.session["staffer_id"]).delete()
        raise HTTPRedirect("schedule?message={}", "Shift dropped")
    
    @unrestricted
    def login(self, message="", full_name="", email="", zip_code=""):
        if full_name or email or zip_code:
            try:
                attendee = get_attendee(full_name, email, zip_code)
                if not attendee.staffing:
                    message = "You are not signed up as a volunteer!  Email {} if you are interested in volunteering.".format(STAFF_EMAIL)
                elif not attendee.assigned:
                    message = "You have not been assigned to any departmemts; an admin must assign you to a department before you can log in"
            except:
                message = "No attendee matches that name and email address and zip code"
            
            if not message:
                cherrypy.session["staffer_id"] = attendee.id
                raise HTTPRedirect("index")
        
        return {
            "message":   message,
            "full_name": full_name,
            "email":     email,
            "zip_code":  zip_code
        }
