from django.urls import path
from .views import FileCreateView, FileListView

urlpatterns = [
    path(
        "",
        FileListView.as_view(),
        name="files-list",
    ),
    path(
        "upload/",
        FileCreateView.as_view(),
        name="files-create",
    ),
]


"""
URL Documentation:
==================================================

Path: 
Name: files-list
View: FileListView
Reversed URL: /api/v1/files/
Method: GET
Description: List all files with pagination
--------------------------------------------------

Path: upload/
Name: files-create
View: FileCreateView
Reversed URL: /api/v1/files/upload/
Method: POST
Description: Upload a new file
--------------------------------------------------
"""
