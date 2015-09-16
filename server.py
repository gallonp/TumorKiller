import webapp2
import jinja2
import os

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Homepage(webapp2.RequestHandler):
    def get(self):
	template = JINJA_ENVIRONMENT.get_template('index.html')
	self.response.write(template.render())

app = webapp2.WSGIApplication([
    ('/', Homepage),
], debug=True)

def main():
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1', port='8080')

if __name__ == '__main__':
    main()
