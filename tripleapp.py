import cgi
import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template

import datetime

class Family(db.Model):
    name = db.StringProperty()
    member_num = db.IntegerProperty()
    created_at = db.DateTimeProperty(auto_now_add = True)
    
class FamilyMember(db.Model):
    user = db.StringProperty()
    nickname = db.StringProperty()
    email = db.EmailProperty()
    birthday = db.DateProperty()
    gender = db.IntegerProperty()
    created_at = db.DateTimeProperty(auto_now_add = True)
    
class Connection(db.Model):
    user = db.StringProperty()
    family = db.ReferenceProperty()

class Greeting(db.Model):
    family = db.ReferenceProperty()
    author = db.UserProperty()
    content = db.StringProperty(multiline = True)
    date = db.DateTimeProperty(auto_now_add = True)

class CurrentStatus(db.Model):
    user = db.StringProperty()
    content = db.StringProperty()
    updated_at = db.DateTimeProperty(auto_now = True)

class HistoricalStatus(db.Model):
    user = db.StringProperty()
    content = db.StringProperty()
    created_at = db.DateTimeProperty(auto_now_add = True)

class StatusEntry():
    user = ''
    user_id = ''
    title = ''
    content = ''
    updated_at = ''

class Communication(db.Model):
    author = db.UserProperty()
    receiver = db.UserProperty()
    content = db.StringProperty(multiline = True)
    date = db.DateTimeProperty(auto_now_add = True)

class MainPage(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            user = users.get_current_user()
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Log out'
            has_family = Connection.gql('WHERE user = :user_id', user_id = user.user_id()).get()
            if has_family is not None:
                selfuser = FamilyMember.gql('WHERE user = :user_id', user_id = user.user_id()).get()
                connection = Connection.gql('WHERE user = :user_id', user_id = user.user_id()).get()
                selfstatus = CurrentStatus.gql('WHERE user = :user_id', user_id = user.user_id()).get()
                family = connection.family
                connections = Connection.gql('WHERE family = :family', family = family)
                member_status = []
                for connection in connections:
                    member = FamilyMember.gql('WHERE user = :user_id', user_id = connection.user).get()
                    currentstatus = CurrentStatus.gql('WHERE user = :user_id', user_id = member.user).get()
                    entry = StatusEntry()
                    entry.user = member.nickname
                    entry.user_id = member.user
                    entry.content = currentstatus.content
                    entry.updated_at = currentstatus.updated_at
                    member_status.append(entry)
                template_values = {
                    'selfuser': selfuser,
                    'user_id': user.user_id(),
                    'url': url,
                    'url_linktext': url_linktext,
                    'selfstatus': selfstatus,
                    'family': family,
                    'member_status': member_status
                }
                path = os.path.join(os.path.dirname(__file__), 'index.html')
            else:
                template_values = {
                    'user': user,
                    'url': url,
                    'url_linktext': url_linktext
                }
                path = os.path.join(os.path.dirname(__file__), 'demo_index.html')
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Log in'
            template_values = {
                'url': url,
                'url_linktext': url_linktext
            }
            path = os.path.join(os.path.dirname(__file__), 'demo_index.html')

        self.response.out.write(template.render(path, template_values))

class UpdateStatus(webapp.RequestHandler):
    def post(self):
        if users.get_current_user():
            user = users.get_current_user()
            currentstatus = CurrentStatus.gql('WHERE user = :user_id', user_id = user.user_id()).get()
            currentstatus.content = self.request.get('status')
            currentstatus.put()
            print 'saved'
        else:
            self.redirect('/')

class FamilyWall(webapp.RequestHandler):
    def get(self, slash, familyname):
        if familyname is not None and familyname != '':
            if users.get_current_user():
                has_family = Connection.gql('WHERE user = :user_id', user_id = user.user_id()).get()
                if has_family is not None:
                    user = users.get_current_user().nickname()
                    url = users.create_logout_url(self.request.uri)
                    url_linktext = 'Log out'
                    family = Family.gql('WHERE name = :familyname', familyname = familyname).get()
                    greetings = Greeting.gql('WHERE family = :family', family = family)
                    template_values = {
                        'user': user,
                        'url': url,
                        'url_linktext': url_linktext,
                        'familyname': familyname,
                        'greetings': greetings
                    }
                    path = os.path.join(os.path.dirname(__file__), 'familywall.html')
                    self.response.out.write(template.render(path, template_values))
                else:
                    self.redirect('/familywall')
            else:
                self.redirect('/familywall')
        else:
            if users.get_current_user():
                user = users.get_current_user().nickname()
                url = users.create_logout_url(self.request.uri)
                url_linktext = 'Log out'
            else:
                user = 'anonymous'
                url = users.create_login_url(self.request.uri)
                url_linktext = 'Log in'

            template_values = {
                'user': user,
                'url': url,
                'url_linktext': url_linktext
            }

            path = os.path.join(os.path.dirname(__file__), 'demo_familywall.html')
            self.response.out.write(template.render(path, template_values))

class Guestbook(webapp.RequestHandler):
    def post(self, familyname):
        greeting = Greeting()

        if users.get_current_user():
            greeting.author = users.get_current_user()

        family = Family.gql('WHERE name = :familyname', familyname = familyname).get()
        greeting.family = family
        greeting.content = self.request.get('content')
        greeting.put()
        self.redirect('/familywall/%s' % familyname)

class JoinFamily(webapp.RequestHandler):
    def get(self, familyname):
        if users.get_current_user():
            user = users.get_current_user()
            has_family = Connection.gql('WHERE user = :user_id', user_id = user.user_id()).get()
            if has_family is None:
                family = Family.gql('WHERE name = :familyname', familyname = familyname).get()
                connections = Connection.gql('WHERE family = :family', family = family)
                members = []
                for connection in connections:
                    member = FamilyMember.gql('WHERE user = :user_id', user_id = connection.user).get()
                    members.append(member)
                template_values = {
                    'user': user,
                    'familyname': familyname,
                    'member': member
                }

                path = os.path.join(os.path.dirname(__file__), 'joinfamily.html')
                self.response.out.write(template.render(path, template_values))
            else:
                self.redirect('/')
        else:
            url = users.create_login_url(self.request.uri)
            self.redirect(url)

class SaveJoining(webapp.RequestHandler):
    def post(self, familyname):
        if users.get_current_user():
            user = users.get_current_user()
            has_family = Connection.gql('WHERE user = :user_id', user_id = user.user_id()).get()
            if has_family is None:
                family = Family.gql('WHERE name = :familyname', familyname = familyname).get()

                familymember = FamilyMember()
                familymember.user = user.user_id()
                familymember.nickname = self.request.get('nickname')
                familymember.email = self.request.get('email')
                birthday = self.request.get('birthday')
                birthday = birthday.split('-')
                familymember.birthday = datetime.date(int(birthday[0]), int(birthday[1]), int(birthday[2]))
                familymember.gender = int(self.request.get('gender'))
                familymember.put()

                connection = Connection()
                connection.user = users.get_current_user().user_id()
                connection.family = family
                connection.put()

                historicalstatus = HistoricalStatus()
                historicalstatus.user = user.user_id()
                historicalstatus.content = self.request.get('status')
                historicalstatus.put()

                currentstatus = CurrentStatus()
                currentstatus.user = user.user_id()
                currentstatus.content = self.request.get('status')
                currentstatus.put()

        self.redirect('/')
        
class Register(webapp.RequestHandler):
    def get(self):
        if users.get_current_user():
            user = users.get_current_user()
            has_family = Connection.gql('WHERE user = :user_id', user_id = user.user_id()).get()
            if has_family is None:
                template_values = {
                    'user': user
                }

                path = os.path.join(os.path.dirname(__file__), 'registration.html')
                self.response.out.write(template.render(path, template_values))
            else:
                self.redirect('/')
        else:
            url = users.create_login_url(self.request.uri)
            self.redirect(url)

class SaveRegistration(webapp.RequestHandler):
    def post(self):
        if users.get_current_user():
            user = users.get_current_user()
            has_family = Connection.gql('WHERE user = :user_id', user_id = user.user_id()).get()
            if has_family is None:
                family = Family()
                family.name = self.request.get('familyname')
                family.member_num = 1
                family.put()

                familymember = FamilyMember()
                familymember.user = user.user_id()
                familymember.nickname = self.request.get('nickname')
                familymember.email = self.request.get('email')
                birthday = self.request.get('birthday')
                birthday = birthday.split('-')
                familymember.birthday = datetime.date(int(birthday[0]), int(birthday[1]), int(birthday[2]))
                familymember.gender = int(self.request.get('gender'))
                familymember.put()

                connection = Connection()
                connection.user = users.get_current_user().user_id()
                connection.family = family
                connection.put()

                historicalstatus = HistoricalStatus()
                historicalstatus.user = user.user_id()
                historicalstatus.content = self.request.get('status')
                historicalstatus.put()

                currentstatus = CurrentStatus()
                currentstatus.user = user.user_id()
                currentstatus.content = self.request.get('status')
                currentstatus.put()

        self.redirect('/')

class Message(webapp.RequestHandler):
    def get(self):
        r = self.request.get('r')
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
            'r': r,
        }
        #if users.get_current_user():
            #path = os.path.join(os.path.dirname(__file__), 'message.html')
        #else:
        path = os.path.join(os.path.dirname(__file__), 'demo_message.html')
        self.response.out.write(template.render(path, template_values))

class Msg(webapp.RequestHandler):
    def post(self):
        communication = Communication()

        if users.get_current_user():
            communication.author = users.get_current_user()

        communication.content = self.request.get('content')
        communication.put()
        self.redirect('/message')

application = webapp.WSGIApplication([('/', MainPage),
                                      ('/update_status', UpdateStatus),
                                      ('/familywall(/?)(.*)', FamilyWall),
                                      ('/sign/(.*)', Guestbook),
                                      ('/join/(.*)', JoinFamily),
                                      ('/save_joining/(.*)', SaveJoining),
                                      ('/register', Register),
                                      ('/save_registration', SaveRegistration),
                                      ('/message', Message),
                                      ('/signmsg', Msg)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
