import sys
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor

from app import App
from config import *
from myLogger import *

class ServerTop(Resource):
	def __init__(self, serverId=0):
		Resource.__init__(self)
		self.logger = loggerInit('appServer' + str(serverId))
		self.app = App(serverId)
		self.serverShorten = ServerShorten(self.app, self.logger)
		self.serverRedirect = ServerRedirect(self.app, self.logger)
		self.formHtml = open(APP_TOP_DIR + 'views/base.html', 'r').read()

	def render_GET(self, request):
		# Return the form to introduce a URL
		self.logger.info('Received ServerTop request, retruning base form')
		return self.formHtml

	def getChild(self, path, request):
		if path == '':
			return self
		elif path == '_shorten':
			return self.serverShorten
		else:
			self.serverRedirect.setPath(path)
			return self.serverRedirect

class ServerShorten(Resource):
	isLeaf = True
	def __init__(self, app, logger):
		Resource.__init__(self)
		self.app = app
		self.shortUrlHtml = open(APP_TOP_DIR + 'views/shortUrl.html', 'r').read()
		self.errorHtml = open(APP_TOP_DIR + 'views/error.html', 'r').read()
		self.logger = logger
		
	def render_POST(self, request):
		# Security check for form input
		if not request.args['url'] or not request.args['url'][0] or len(request.args['url'][0]) > MAX_REQ_LENGTH:
			 return self.errorHtml % 'Not valid URL'
			 
		self.logger.info('Received ServerShorten request for URL ' + request.args['url'][0])
		# Generate a code for the given URL and stores the mapping
		url = APP_URL + self.app.get_short_url(request.args['url'][0])
		# Return the short URL
		return self.shortUrlHtml % (url, url)
		
class ServerRedirect(Resource):
	isLeaf = True
	def __init__(self, app, logger):
		Resource.__init__(self)
		self.app = app
		self.redirectHtml = open(APP_TOP_DIR + 'views/redirect.html', 'r').read()
		self.notFoundHtml = open(APP_TOP_DIR + 'views/notFound.html', 'r').read()
		self.errorHtml = open(APP_TOP_DIR + 'views/error.html', 'r').read()
		self.logger = logger
	
	def setPath(self, path):
		self.path = path
	
	def render_GET(self, request):
		# Security check for path
		if not self.path or len(self.path) > MAX_REQ_LENGTH:
			 return self.errorHtml % 'Not valid URL'
		self.logger.info('Received ServerRedirect request for short URL ' + self.path)
		# Check if it is an unvalid request detected by the loadBalancer
		if self.path == '_error':
			self.logger.info('Error request detected by the load balancer')
			return self.notFoundHtml % 'Invalid'
		# Fetch original URL from URL code
		longUrl = self.app.get_long_url(self.path)
		if longUrl:
			# Return original URL
			self.logger.info('Resolved short URL ' + self.path + ' as long URL ' + longUrl)
			return self.redirectHtml % longUrl
		else:
			# URL Code not found
			self.logger.info('Short URL ' + self.path + ' can not be resolved')
			return self.notFoundHtml % (APP_URL + self.path)


if __name__ == "__main__":
	serverId = int(sys.argv[1])	
	root = ServerTop(serverId)
	factory = Site(root)
	reactor.listenTCP(SERVERS[serverId][PORT], factory)
	reactor.run()

