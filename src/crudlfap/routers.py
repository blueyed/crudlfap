"""
CRUDLFA+ router for Django 2.0.

Note that you can also use non-database backed models, by inheriting from
models.Model and setting their Meta.managed attribute to False. Then, you can
use CRUDLFA+ views and routers.
"""
import re

from django.apps import apps


crudlfap = apps.get_app_config('crudlfap')  # pylint: disable=invalid-name


class Router(object):
    """Base router for CRUDLFA+."""

    views = crudlfap.get_default_views()

    def generate_view_slug(self, view):
        """
        Generate a slug from a view class.

        Strip model name and 'View' suffix from view class name, will be added
        by router, YourModelCreateView gets the 'create' slug.
        """
        name = view.__name__.replace(self.model.__name__, '')
        name = name.replace('View', '')
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

    def generate_views(self, *views):
        """
        Generate views for this router, core of the automation in CRUDLFA+.

        This method considers each view in given args or self.views and returns
        a list of usable views.

        Each arg may be a view class or a dict of attributes with a `_cls` key
        for the actual view class.

        It will copy the view class and bind the router on it in the list this
        returns.

        For example, this would cause two view classes to be returned, if
        self.model is ``Artist``, then ``CreateView`` will be used as parent to
        create ``ArtistCreateView`` and ``DetailView`` will be used to create
        ``ArtistDetailView``, also setting the attribute
        ``extra_stuff='bar'``::

            Router(Artist).generate_views(
                [CreateView, dict(_cls=DetailView, extra_stuff='bar')]
            )
        """
        result = []
        for arg in views or self.views:
            view = arg

            if isinstance(arg, dict):
                view = arg.pop('_cls')

            slug = getattr(view, 'slug', None)
            if not view.slug:
                slug = self.generate_view_slug(view)

            url_pattern = getattr(view, 'url_pattern', None)
            if url_pattern:
                url_pattern = url_pattern.format(slug=slug)

            attrs = dict(
                router=self,
                model=self.model,
                slug=slug,
            )

            view_name = view.__name__
            if self.model.__name__ not in view_name:
                view_name = self.model.__name__ + view_name

            view_class = type(view_name, (view,), attrs)
            result.append(view_class)
        return result

    def __init__(self, model, prefix=None, *views):
        """Create a Router for a Model."""
        self.model = model

        # pylint: disable=protected-access
        self.model_name = model._meta.model_name
        self.model_verbose_name = model._meta.verbose_name
        self.model_verbose_name_plural = model._meta.verbose_name_plural

        self.prefix = prefix or ''
        self.views = self.generate_views(*views)

    def __getitem__(self, slug):
        """Get a view by slug."""
        for view in self.views:
            if view.slug == slug:
                return view

        raise KeyError(
            'View with slug {} not in router {}'.format(
                slug,
                type(self).__name__,
            )
        )
