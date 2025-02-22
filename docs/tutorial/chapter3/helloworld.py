from pyramid.config import Configurator
from pyramid.view import view_config

from baseplate import Baseplate
# from baseplate.frameworks.pyramid import BaseplateConfigurator
from baseplate.frameworks.pyramid import includeme as baseplate_includeme


@view_config(route_name="hello_world", renderer="json")
def hello_world(request):
    return {"Hello": "World"}


def make_wsgi_app(app_config):
    baseplate = Baseplate(app_config)
    baseplate.configure_observers()

    configurator = Configurator(settings=app_config)
    # configurator.include(BaseplateConfigurator(baseplate).includeme)
    configurator.include(baseplate_includeme)
    configurator.baseplate = baseplate
    configurator.add_route("hello_world", "/", request_method="GET")
    configurator.scan()
    return configurator.make_wsgi_app()
