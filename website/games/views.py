from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    """Index view."""

    template_name = "games/index.html"

    def get(self, request, **kwargs):
        """
        GET request for IndexView.

        :param request: the request
        :param kwargs: keyword arguments
        :return: a render of the index page
        """
        return render(request, self.template_name)
