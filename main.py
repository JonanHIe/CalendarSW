import httplib
import json
import logging
import os
import urllib

import jinja2
import webapp2
from webapp2_extras import sessions

import httplib2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

cliente_id="364280739195-pg4r0km6r1guvuvp8d8ts7f0i2jnchoh.apps.googleusercontent.com"
cliente_secret="lKkSc2V6pGN7E3bz2hUtAa8x"
redirect_uri="http://sistemaswebgae.appspot.com/callback_uri"



class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()
config = {}
config['webapp2_extras.sessions'] = {'secret_key': 'my-super-secret-key'}


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('<a href="/LoginAndAuthorize">Login ant Authorize with Calendar</a>')


class LoginAndAuthorize(BaseHandler):
    def get(self):
        servidor = 'accounts.google.com'
        conn = httplib.HTTPSConnection(servidor)
        conn.connect()
        metodo = 'GET'
        params = {'client_id': cliente_id,
                  'redirect_uri': redirect_uri,
                  'response_type': 'code',
                  'scope': 'https://www.googleapis.com/auth/calendar',
                  'approval_prompt': 'auto',
                  'access_type': 'offline'}
        params_coded = urllib.urlencode(params)
        uri = '/o/oauth2/v2/auth' + '?' + params_coded
        self.redirect('https://' + servidor + uri)

        logging.debug(params)


class OAuthHandler(BaseHandler):
    def get(self):
        servidor = 'accounts.google.com'
        metodo = 'POST'
        uri = '/o/oauth2/token'
        auth_code = self.request.get('code')
        params = {'code': auth_code,
                  'client_id': cliente_id,
                  'client_secret': cliente_secret,
                  'redirect_uri': redirect_uri,
                  'grant_type': 'authorization_code'}
        params_encoded = urllib.urlencode(params)
        cabeceras = {'Host': servidor,
                     'User-Agent': 'Python bezeroa',
                     'Content-Type': 'application/x-www-form-urlencoded',
                     'Content-Length': str(len(params_encoded))}
        http = httplib2.Http()
        respuesta, cuerpo = http.request('https://' + servidor + uri, method=metodo, headers=cabeceras,
                                         body=params_encoded)

        json_cuerpo = json.loads(cuerpo)

        access_token = json_cuerpo['access_token']
        self.session['access_token'] = access_token
        logging.debug(access_token)

        self.redirect('/CalendarLista')


class CalendarLista(BaseHandler):
    def get(self):
        access_token = self.session.get('access_token')
        logging.debug(access_token)

        servidor = 'www.googleapis.com'
        metodo = 'GET'
        uri = '/calendar/v3/users/me/calendarList'
        cabeceras = {'Host': servidor,
                     'Authorization': 'Bearer ' + access_token
                    }
        http = httplib2.Http()
        respuesta, cuerpo = http.request('https://' + servidor + uri, method=metodo, headers=cabeceras)

        logging.debug(respuesta)
        logging.debug(cuerpo)
        json_cuerpo=json.loads(cuerpo)

        self.response.write('<html><head>')
        self.response.write('<title>Calendarios</title>')
        self.response.write('</head>')

        self.response.write('<h1>Mis Calendarios de Google son</h1>')
        for each in json_cuerpo['items']:
            self.response.write('   '+ each['summary']+ ' su ID es:' + each ['id']+'</br>')
            self.response.write('</body></html>')



app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorize),
    ('/callback_uri', OAuthHandler),
    ('/CalendarLista', CalendarLista)], config=config, debug=True)
