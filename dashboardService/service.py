import tornado.wsgi
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import Application
from tornado.platform.asyncio import asyncio
from dashboardService.handlers.dashboardRequestHandler import DashboardRequestHandler


define('port', default=8086, help='Port to listen on')

# def main():
"""Construct and serve the tornado application."""
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

app = Application([
    ('/api/.*', DashboardRequestHandler)
])

application = tornado.wsgi.WSGIAdapter(app)

http_server = HTTPServer(app)
http_server.listen(options.port)
print('Dashboard service listening on http://localhost:%i' % options.port)
IOLoop.current().start()

# if __name__ == '__main__':
#     main()