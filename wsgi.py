from app import create_app

application = create_app('production')
app = application

if __name__ == '__main__':
    app.run()

# Si tu archivo principal se llama distinto, cambia 'app' por el nombre correcto:
# from main import app as application