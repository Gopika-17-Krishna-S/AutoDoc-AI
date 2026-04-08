from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, DeleteView, UpdateView
from django.views import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from .models import Project, APIEndpoint
from parser.utils import parse_project_zip

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user).order_by('-created_at')

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

class ProjectDocsView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_docs.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object
        endpoints = list(project.endpoints.values('name', 'path', 'method', 'category', 'path_params', 'description'))
        
        # Group by category
        from collections import defaultdict
        groups = defaultdict(list)
        for ep in project.endpoints.all():
            groups[ep.category or 'general'].append(ep)
        ctx['endpoint_groups'] = dict(groups)
        
        # Re-detect workflows from stored endpoints
        from parser.utils import detect_workflows
        ctx['workflows'] = detect_workflows(endpoints)
        return ctx

class ProjectExplorerView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_explorer.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        project = self.object

        # Group endpoints by source file
        from collections import defaultdict
        file_ep_map = defaultdict(list)
        for ep in project.endpoints.all():
            key = ep.source_file or 'unknown'
            file_ep_map[key].append(ep)

        # Build file list sorted by endpoint count desc
        files = []
        for fname, eps in file_ep_map.items():
            categories = sorted(set(ep.category for ep in eps))
            methods = sorted(set(ep.method for ep in eps))
            files.append({
                'name': fname,
                'short_name': fname.split('/')[-1] if '/' in fname else fname,
                'endpoint_count': len(eps),
                'categories': categories,
                'methods': methods,
                'endpoints': eps,
                'has_routes': len(eps) > 0,
            })
        files.sort(key=lambda f: -f['endpoint_count'])
        ctx['files'] = files

        # Per-category counts (fix the "39 for everything" bug)
        cat_counts = defaultdict(int)
        for ep in project.endpoints.all():
            cat_counts[ep.category or 'general'] += 1
        ctx['category_counts'] = dict(cat_counts)

        all_categories = sorted(cat_counts.keys())
        all_methods = sorted(set(ep.method for ep in project.endpoints.all()))
        ctx['all_categories'] = all_categories
        ctx['all_methods'] = all_methods

        all_eps = list(project.endpoints.values('name', 'path', 'method', 'category', 'path_params', 'description'))
        from parser.utils import detect_workflows
        ctx['workflows'] = detect_workflows(all_eps)
        return ctx

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'description', 'source_file', 'github_url']
    success_url = reverse_lazy('projects:project_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_form.html'
    fields = ['name', 'description', 'github_url']

    def get_success_url(self):
        return reverse_lazy('projects:project_detail', kwargs={'pk': self.object.pk})

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/project_confirm_delete.html'
    context_object_name = 'project'
    success_url = reverse_lazy('projects:project_list')

class ProjectExportView(LoginRequiredMixin, View):
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        data = {
            'project': project.name,
            'description': project.description,
            'source': project.github_url or (project.source_file.name if project.source_file else None),
            'endpoints': [
                {
                    'path': ep.path,
                    'method': ep.method,
                    'name': ep.name,
                    'category': ep.category,
                    'description': ep.description,
                    'path_params': ep.path_params or [],
                }
                for ep in project.endpoints.all().order_by('category', 'path')
            ]
        }
        response = JsonResponse(data, json_dumps_params={'indent': 2})
        response['Content-Disposition'] = f'attachment; filename="{project.name}_api_docs.json"'
        return response

class ProjectParseView(View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        
        try:
            if project.source_file:
                endpoints, workflows, files_info = parse_project_zip(project.source_file)
            elif project.github_url:
                from parser.utils import download_github_zip
                zip_io = download_github_zip(project.github_url)
                endpoints, workflows, files_info = parse_project_zip(zip_io)
            else:
                messages.error(request, "No source file or GitHub URL provided for this project.")
                return redirect('projects:project_detail', pk=project.pk)
            
            if not endpoints:
                messages.warning(request, "No API endpoints found. Ensure your codes use Flask or FastAPI route syntax.")
            else:
                project.endpoints.all().delete()
                for ep in endpoints:
                    APIEndpoint.objects.create(
                        project=project,
                        path=ep.get('path', ''),
                        method=ep.get('method', 'GET'),
                        name=ep.get('name', ''),
                        description=ep.get('description', '') or '',
                        category=ep.get('category', 'general'),
                        path_params=ep.get('path_params', []),
                        source_file=ep.get('source_file', ''),
                    )
                messages.success(request, f"{len(endpoints)} endpoints parsed across {len(files_info)} files in {len(set(e['category'] for e in endpoints))} categories. Workflows: {len(workflows)} detected.")
        except Exception as e:
            messages.error(request, f"Failed to parse project: {str(e)}")
            
        return redirect('projects:project_detail', pk=project.pk)

