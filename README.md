# sqlite_viz reusable Django app

Reusable Django app for visualizing and editing local SQLite database files.

## Features

- List tables
- List rows
- Delete one or multiple tables
- Delete one or multiple rows
- Browser UI and HTTP API (Django Ninja)

## How to Use

- Install the package
- Add to `INSTALLED_APPS`: `INSTALLED_APPS.append("sqlite_viz")`
- Add to URLs: `urlpatterns.append(path("sqlite-viz/", include("sqlite_viz.urls")))`

!> [!NOTE]
> Copy the URL as it's shown above, don't change the path!

