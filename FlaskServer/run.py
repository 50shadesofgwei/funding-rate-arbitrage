from FlaskServer import create_app

app = create_app()

def run():
    app.run()

if __name__ == "__main__":
    run()