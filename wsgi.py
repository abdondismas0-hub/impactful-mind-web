# wsgi.py
# Faili hili linaunganisha Gunicorn na Flask app yako.

from app import app
# *Ikiwa ulitumia jina tofauti la kigezo (variable) kwa ajili ya Flask app yako*
# (yaani: 'application = Flask(__name__)' badala ya 'app = Flask(__name__)'),
# badilisha mstari hapo juu uwe: from app import application

if __name__ == '__main__':
    app.run()
