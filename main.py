#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import re
from string import letters

import webapp2
import jinja2



from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)


class BaseHandler(webapp2.RequestHandler):
    
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    

class Rot13(BaseHandler):

    def get(self):
        self.render('rot13-form.html')

    def post(self):
        rot13=''
        text =self.request.get('text')
        if text:
            rot13 = text.encode('rot13')
            self.render('rot13-form.html', text = rot13)



USER_RE = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
def valid_username(username):
    return username and USER_RE.match(username)


PASS_RE =re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and USER_RE.match(password)

EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
def valid_email(email):
    return not email or EMAIL_RE.match(email)


class Signup(BaseHandler):
    def get(self):
        self.render('signup-form.html')

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username, email = email)

        if not valid_username(username):
            params['error_username']= "That is not valid username."
            have_error =True
        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True
        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            self.redirect('/unit2/welcome?username=' + username)

class Welcome(BaseHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html', username = username)
        else:
            self.redirect('/unit2/signup')


class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
    

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


            
            
def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)


class Post(db.Model):
    subject =db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    lastmodified = db.DateTimeProperty(auto_now = True)
    
    def render(self):
        self._render_text = self.content.replace('\n', '<br>')
        return render_str("post.html", p = self)

class BlogFront(BaseHandler):
    def get(self):
        posts = db.GqlQuery("SELECT *FROM Post ORDER BY created DESC")
        self.render("front.html", posts = posts)


class PostPage(BaseHandler):
    def get(self, post_id):
        key = db.Key.from_path('Post', int(post_id), parent = blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return
        self.render("permalink.html", post = post)

class NewPost(BaseHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject, content = content)
            p.put()

            self.redirect('/blog/''%s' % str(p.key().id()))

        else:
            error = "Please need both subject and content,please!"

            self.render("newpost.html", subject=subject, content=content, error=error)


class MainPage(BaseHandler):
    def get(self):
        self.write('Udacity Page')
 

app = webapp2.WSGIApplication([('/', MainPage),
                               ('/unit2/rot13', Rot13),
                               ('/unit2/signup', Signup),
                               ('/unit2/welcome', Welcome),
                               ('/blog?', BlogFront),
                               ('/blog/([0-9])', PostPage),
                              ('/blog/newpost', NewPost),],
                              debug=True)
