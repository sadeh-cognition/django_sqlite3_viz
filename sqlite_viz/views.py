from django.views.generic import TemplateView


class SqliteVizHomeView(TemplateView):
    template_name = "sqlite_viz/index.html"
