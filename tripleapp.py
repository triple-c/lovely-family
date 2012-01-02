import cgi
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

from datetime import datetime

class Family(db.Model):
    name = db.StringProperty()
    member_num = db.IntegerProperty()
    created_at = db.DateTimeProperty(auto_now_add = True)
    
class FamilyMember(db.Model):
    user = db.UserProperty()
    nickname = db.StringProperty()
    gender = db.IntegerProperty()
    birthday = db.DateProperty()
    email = db.EmailProperty()
    created_at = db.DateTimeProperty(auto_now_add = True)
    
class Connection(db.Model):
    user = db.StringProperty()
    family_key = db.ReferenceProperty()

class Greeting(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)

class Communication(db.Model):
    author = db.UserProperty()
    receiver = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        members_query = Greeting.all()
        members = members_query.fetch(10)
        user = users.get_current_user()
        #q = db.GqlQuery("SELECT * FROM Connection WHERE user = %s", user.user_id())
        #family = q.name
        template_values = {
            'members':members,
            #'family':family
        }
        #if users.get_current_user():
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        #else:
         #   path = os.path.join(os.path.dirname(__file__), 'demo_index.html')
        self.response.out.write(template.render(path, template_values))

class FamilyWall(webapp.RequestHandler):
    def get(self):
        greetings_query = Greeting.all().order('-date')
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Log out'
            user = users.get_current_user().nickname()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Log in'
            user = 'anonymous'

        template_values = {
            'greetings': greetings,
            'url': url,
            'url_linktext': url_linktext,
            'user': user
        }
        #if users.get_current_user():
            #path = os.path.join(os.path.dirname(__file__), 'familywall.html')
        #else:
        path = os.path.join(os.path.dirname(__file__), 'demo_familywall.html')
        self.response.out.write(template.render(path, template_values))

class Guestbook(webapp.RequestHandler):
    def post(self):
        greeting = Greeting()

        if users.get_current_user():
            greeting.author = users.get_current_user()

        greeting.content = self.request.get('content')
        greeting.put()
        self.redirect('/familywall')
        
class Registration(webapp.RequestHandler):
    def get(self):
        template_values = {
        }

        path = os.path.join(os.path.dirname(__file__), 'registration.html')
        self.response.out.write(template.render(path, template_values))

class SaveRegistration(webapp.RequestHandler):
    def post(self):
        family=Family()
        familymember=FamilyMember()
        family.name=self.request.get('familyname')
        family.member_num=1
        family.put()

        if users.get_current_user():
            familymember.user = users.get_current_user()

        familymember.gender = int(self.request.get('gender'))
        d = datetime.strptime(self.request.get('birthday'),'%Y-%m-%d').date()
        familymember.birthday=d
        familymember.nickname=self.request.get('nickname')
        familymember.put()
        connection=Connection()
        connection.user=users.get_current_user().user_id()
        connection.family_key=family.key()
        connection.put()
        self.redirect('/')

class Message(webapp.RequestHandler):
    def get(self):
        r=self.request.get('r')
        greetings_query = Greeting.all().order('-date')
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Log out'
            user = users.get_current_user().nickname()
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Log in'
            user = 'anonymous'

        template_values = {
            'greetings': greetings,
            'url': url,
            'url_linktext': url_linktext,
            'user': user,
            'r':r,
        }
        #if users.get_current_user():
            #path = os.path.join(os.path.dirname(__file__), 'message.html')
        #else:
        path = os.path.join(os.path.dirname(__file__), 'demo_message.html')
        self.response.out.write(template.render(path, template_values))

class MSG(webapp.RequestHandler):
    def post(self):
        communication = Communication()

        if users.get_current_user():
            communication.author = users.get_current_user()

        communication.content = self.request.get('content')
        communication.put()
        self.redirect('/message')

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/registration',Registration),
                                      ('/familywall', FamilyWall),
                                      ('/sign', Guestbook),
                                      ('/message',Message),
                                      ('/signmsg',MSG)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
