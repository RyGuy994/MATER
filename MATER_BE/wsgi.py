# MATER/MATER_BE/wsgi.py
from backend import create_app
from backend.models.user import db, User

app = create_app()

# Auto-seed test user on first startup (runs once)
with app.app_context():
    if not User.query.filter_by(username="test").first():
        print("🌱 Seeding test user...")
        user = User(username="test", email="test@test.com")
        user.set_password("test")
        user.mfa_required = False
        db.session.add(user)
        db.session.commit()
        print("✓ Test user created: test@test.com / test")
    else:
        print("✓ Test user already exists")

@app.shell_context_processor
def make_shell_context():
    """Provides objects to `flask shell` command."""
    return {"db": db, "User": User}

@app.cli.command("seed-db")
def seed_db():
    """Seed the database with test data (manual)."""
    with app.app_context():
        if not User.query.filter_by(username="test").first():
            user = User(username="test", email="test@test.com")
            user.set_password("test")
            user.mfa_required = False
            db.session.add(user)
            db.session.commit()
            print("✓ Test user created")
        else:
            print("✓ Test user already exists")

if __name__ == "__main__":
    app.run(debug=True)
