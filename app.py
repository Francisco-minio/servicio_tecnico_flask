import os
from factory import create_app

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(host='localhost', port=8080, debug=True)
