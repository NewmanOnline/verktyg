# -*- coding: utf-8 -*-
"""
    werkzeug_dispatch.views
    ~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2014 by Ben Mather.
    :license: BSD, see LICENSE for more details.
"""
import json

from werkzeug import Response
from werkzeug_dispatch.bindings import Binding, BindingFactory


class View(BindingFactory):
    """ Wraps a function or callable so that it can be bound to a name in a
    dispatcher.
    """
    def __init__(self, name, action, *, methods={'GET'}, content_type=None):
        self._name = name
        self._methods = methods
        self._content_type = content_type
        self._action = action

    def __call__(self, env, req, *args, **kwargs):
        return self._action(env, req, *args, **kwargs)

    def get_bindings(self):
        for method in self._methods:
            yield Binding(self._name, self,
                          method=method,
                          content_type=self._content_type)


class TemplateView(View):
    """ Like `View` but if the value returned from the action is not an
    instance of `Response` it is rendered using the named template.

    :param name:
    :param action: called with environment, request and params to generate
                   response.  See `View`.
    :param template: either a string naming the template to be retrieved from
                     the environment or a callable applied to the result to
                     create an http `Response` object
    """
    def __init__(self, name, action, *,
                 methods={'GET'}, template=None,
                 content_type=None):
        super(TemplateView, self).__init__(
            name, action,
            methods=methods,
            content_type=content_type)
        self._template = template

    def __call__(self, env, req, *args, **kwargs):
        res = self._action(env, req, *args, **kwargs)
        if isinstance(res, Response):
            return res
        return Response(env.get_renderer(self._template)(res))


def expose(dispatcher, name, *args, **kwargs):
    def decorator(f):
        dispatcher.add(TemplateView(name, f, *args, **kwargs))
        return f
    return decorator


def expose_html(*args, **kwargs):
    if 'content_type' not in kwargs:
        kwargs['content_type'] = 'text/html'
    return expose(*args, **kwargs)


class JsonView(View):
    def __init__(self, name, action, *, methods={'GET'}):
        super(JsonView, self).__init__(name, action, methods=methods,
                                       content_type='text/json')

    def __call__(self, env, req, *args, **kwargs):
        res = super(JsonView, self).__call__(env, req, *args, **kwargs)
        if isinstance(res, Response):
            return res
        return Response(json.dumps(res), content_type='text/json')


def expose_json(dispatcher, name, *args, **kwargs):
    def decorator(f):
        dispatcher.add(JsonView(name, f, *args, **kwargs))
        return f
    return decorator


class ClassView(BindingFactory):
    def get_bindings(self):
        for method in {'GET', 'HEAD', 'POST', 'PUT', 'DELETE'}:  # TODO
            if hasattr(self, method):
                yield Binding(self.name, getattr(self, method),
                              method=method)