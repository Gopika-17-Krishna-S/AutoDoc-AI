from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('project/new/', views.ProjectCreateView.as_view(), name='project_create'),
    path('project/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('project/<int:pk>/docs/', views.ProjectDocsView.as_view(), name='project_docs'),
    path('project/<int:pk>/parse/', views.ProjectParseView.as_view(), name='project_parse'),
    path('project/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('project/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('project/<int:pk>/export/json/', views.ProjectExportView.as_view(), name='project_export_json'),
    path('project/<int:pk>/explorer/', views.ProjectExplorerView.as_view(), name='project_explorer'),
]
