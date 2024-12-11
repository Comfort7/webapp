from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from flask_migrate import Migrate
from datetime import datetime
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:comfort@localhost/birthday_website'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class Celebrant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    shareable_link = db.Column(db.String(255), unique=True, nullable=False)

class Wish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    celebrant_id = db.Column(db.Integer, db.ForeignKey('celebrant.id'), nullable=False)
    well_wisher_name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/celebrant", methods=["POST"])
def create_celebrant():
    name = request.form.get("name")
    birthdate = request.form.get("birthdate")

    # Generate a unique shareable link
    birthdate_obj = datetime.strptime(birthdate, '%Y-%m-%d')
    formatted_birthdate = birthdate_obj.strftime('%Y%m%d')  # Format to YYYYMMDD
    shareable_link = f"http://localhost:5000/share/{name.lower().replace(' ', '-')}-{formatted_birthdate}"

    # Check if the shareable link already exists
    existing_celebrant = db.session.query(Celebrant).filter_by(shareable_link=shareable_link).first()
    if existing_celebrant:
        return f"Shareable link already exists: {shareable_link}", 400  # Return an error response

    # Add celebrant to the database
    new_celebrant = Celebrant(name=name, birthdate=birthdate, shareable_link=shareable_link)

    try:
        db.session.add(new_celebrant)
        db.session.commit()
        return redirect(url_for('share_page', link=shareable_link))
    except IntegrityError:
        db.session.rollback()  # Rollback the session in case of error
        return "An error occurred while creating the celebrant.", 500

@app.route("/share/<path:link>")
def share_page(link):
    return render_template("share_page.html", link=link)

@app.route("/wish/<path:link>", methods=["GET", "POST"])
def wish_page(link):
    if request.method == "POST":
        well_wisher_name = request.form.get("wisher_name")
        message = request.form.get("message")
        images = request.files.getlist("images")

        # Check if the number of images exceeds the limit
        if len(images) > 3:
            return "You can only upload a maximum of 3 images.", 400  # Return an error response

        # Save images and create a list of image paths
        image_paths = []
        for image in images:
            if image and allowed_file(image.filename):  # Check if the file is allowed
                # Define your upload path
                image_path = os.path.join('static', 'uploads', image.filename)
                
                # Save the image
                image.save(image_path)  # Save the image

                # Store the relative path for web access
                relative_image_path = f"/static/uploads/{image.filename}"
                image_paths.append(relative_image_path)

        # Join image paths into a single string
        image_paths_string = ','.join(image_paths)

        # Find the celebrant by the shareable link
        celebrant = db.session.query(Celebrant).filter_by(shareable_link=link).first()
        if celebrant:
            new_wish = Wish(celebrant_id=celebrant.id, well_wisher_name=well_wisher_name, message=message, image_path=image_paths_string)
            db.session.add(new_wish)
            db.session.commit()
            return redirect(url_for('share_page', link=link))  # Redirect back to the share page

    return render_template("wish_page.html", link=link)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route("/celebrant/<path:link>")
def celebrant_wishes(link):
    # Find the celebrant by the shareable link
    celebrant = db.session.query(Celebrant).filter_by(shareable_link=link).first()
    if celebrant:
        # Fetch all wishes for the celebrant
        wishes = db.session.query(Wish).filter_by(celebrant_id=celebrant.id).all()
        if not wishes:
            # Redirect to the share page if no wishes are found
            return redirect(url_for('share_page', link=link))
        return render_template("celebrant_wishes.html", celebrant=celebrant, wishes=wishes)
    
    # If celebrant is not found, you can also redirect to the share page
    return redirect(url_for('share_page', link=link))

if __name__ == "__main__":
    app.run(debug=True)
