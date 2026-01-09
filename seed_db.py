from app import app, db, User, bcrypt

def seed():
    with app.app_context():
        # Create database if not exists
        db.create_all()
        
        # Check if demo user exists
        demo_user = User.query.filter_by(email="demo@example.com").first()
        if not demo_user:
            hashed_pw = bcrypt.generate_password_hash("password123").decode('utf-8')
            new_user = User(username="DemoUser", email="demo@example.com", password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()
            print("Demo user created successfuly!")
            print("Email: demo@example.com")
            print("Password: password123")
        else:
            print("Demo user already exists.")

if __name__ == "__main__":
    seed()
