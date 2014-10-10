from flask import Flask, request, redirect, url_for, render_template

app = Flask(__name__)

# This is just an horrible way to keep around
# uploaded files, but in the end we just wanted
# to showcase how to setup DEPOT, not how to upload files.
UPLOADED_FILES = []


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            fileid = DepotManager.get().create(file)
            UPLOADED_FILES.append(fileid)
            return redirect(url_for('index'))

    files = [DepotManager.get().get(fileid) for fileid in UPLOADED_FILES]
    return render_template('index.html', files=files)


from depot.manager import DepotManager
DepotManager.configure('default', {'depot.storage_path': '/tmp/'})
app.wsgi_app = DepotManager.make_middleware(app.wsgi_app)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
