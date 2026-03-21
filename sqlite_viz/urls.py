from django.urls import path

from .api import api
from .views import SqliteVizHomeView

urlpatterns = [
    path("", SqliteVizHomeView.as_view(), name="sqlite-viz-home"),
    path("api/", api.urls),
]
