from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from depot.manager import DepotManager


# This is just an horrible way to keep around
# uploaded files, but in the end we just wanted
# to showcase how to setup DEPOT, not how to upload files.
UPLOADED_FILES = []


def index(request):
    if request.method == 'POST':
        file = request.FILES['file']
        if file:
            fileid = DepotManager.get().create(file)
            UPLOADED_FILES.append(fileid)
            return HttpResponseRedirect('/')

    files = [DepotManager.get().get(fileid) for fileid in UPLOADED_FILES]

    template = loader.get_template('index.html')
    return HttpResponse(template.render({
        'files': files
    }, request))


