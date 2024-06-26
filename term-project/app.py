import psycopg2
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime

app = Flask(__name__)
connect = psycopg2.connect("dbname=tutorial user=postgres password=postgres")
cur = connect.cursor()  # create cursor


@app.route('/')
def login():
    return render_template("login.html")

@app.route('/main')
def main():
    id = request.args.get('id')
    movie_filter = request.args.get('movie_filter')
    review_filter = request.args.get('review_filter')

    if movie_filter == 'genre':
        cur.execute("""
            SELECT movies.title, COALESCE(trunc(avg(reviews.ratings), 1), 0) as avg_rating, 
                movies.director, movies.genre, movies.rel_date, movies.id
            FROM movies
            LEFT JOIN reviews ON movies.id = reviews.mid
            GROUP BY movies.id
            ORDER BY movies.genre;
        """)
    elif movie_filter == 'ratings':
        cur.execute("""
            SELECT movies.title, COALESCE(trunc(avg(reviews.ratings), 1), 0) as avg_rating, 
                movies.director, movies.genre, movies.rel_date, movies.id
            FROM movies
            LEFT JOIN reviews ON movies.id = reviews.mid
            GROUP BY movies.id
            ORDER BY avg_rating DESC;
        """)
    else:
        cur.execute("""
            SELECT movies.title, COALESCE(trunc(avg(reviews.ratings), 1), 0) as avg_rating, 
                movies.director, movies.genre, movies.rel_date, movies.id
            FROM movies
            LEFT JOIN reviews ON movies.id = reviews.mid
            GROUP BY movies.id
            ORDER BY movies.rel_date DESC;
        """)

    movies = cur.fetchall()

    # Review filtering
    if review_filter == 'title':
        cur.execute("SELECT ratings, uid, title, review, rev_time, movies.id FROM reviews, movies WHERE reviews.mid = movies.id ORDER BY title;")
    elif review_filter == 'followers':
        # get flollowers number of the reviewer and order by it
        cur.execute("SELECT ratings, uid, title, review, rev_time, movies.id FROM reviews, movies WHERE reviews.mid = movies.id ORDER BY (SELECT COUNT(*) FROM ties WHERE ties.opid = reviews.uid AND ties.tie = 'follow') DESC;")
    elif review_filter == 'followings':
        # ! Additional Feature 1. get reviews only from the people who the user follows
        cur.execute("SELECT ratings, uid, title, review, rev_time, movies.id FROM reviews, movies WHERE reviews.mid = movies.id AND reviews.uid IN (SELECT opid FROM ties WHERE ties.id = %s AND ties.tie = 'follow') ORDER BY rev_time DESC;", (id,))
    else:
        cur.execute("SELECT ratings, uid, title, review, rev_time, movies.id FROM reviews, movies WHERE reviews.mid = movies.id ORDER BY rev_time DESC;")
    reviews = cur.fetchall()

    return render_template("main.html", movies=movies, reviews=reviews, id=id)

@app.route('/user_info', methods=['get'])
def user_info():
    id = request.args.get('id')
    user_id = request.args.get('user_id')
    cur.execute("SELECT id, role FROM users WHERE id = %s;", (user_id,))
    user_info = cur.fetchone()
    cur.execute("SELECT ratings, title, review, rev_time, movies.id FROM reviews, movies WHERE reviews.mid = movies.id AND reviews.uid = %s;", (user_id,))
    reviews = cur.fetchall()
    cur.execute("SELECT opid FROM ties WHERE id = %s AND tie = 'follow';", (user_id, ))
    followings = cur.fetchall()
    cur.execute("SELECT id FROM ties WHERE opid = %s AND tie = 'follow';", (user_id, ))
    followers = cur.fetchall()
    cur.execute("SELECT opid FROM ties WHERE id = %s AND tie = 'mute';", (user_id, ))
    muted = cur.fetchall()
    return render_template("user_info.html", id=id, user_info=user_info, reviews=reviews, followers=followers, followings=followings, muted=muted)

@app.route('/movie_info', methods=['get', 'post'])
def movie_info():
    id = request.args.get('id')
    movie_id = request.args.get('movie_id')

    # if method is post, insert review
    if request.method == 'POST':
        mid = movie_id
        uid = id
        ratings = request.form["rating"]  # Change "ratings" to "rating"
        review = request.form["review"]
        rev_time = datetime.now()
        cur.execute("INSERT INTO reviews (mid, uid, ratings, review, rev_time) VALUES (%s, %s, %s, %s, %s);", (mid, uid, ratings, review, rev_time))
        connect.commit()

    cur.execute("SELECT title, director, genre, rel_date, movies.id FROM movies WHERE id = %s;", (movie_id,))
    movie_info = cur.fetchone()
    cur.execute("SELECT ratings, uid, review, rev_time FROM reviews WHERE mid = %s;", (movie_id,))
    reviews = cur.fetchall()
    cur.execute("SELECT trunc(avg(ratings), 1) FROM reviews WHERE mid = %s;", (movie_id,))
    avg_rating = cur.fetchone()

    return render_template("movie_info.html", id=id, movie_info=movie_info, reviews=reviews, avg_rating=avg_rating)

@app.route('/add_movie', methods=['post'])
def add_movie():
    id = request.form["user_id"]
    if id != 'admin':
        return 'You are not an admin. Please log in as an admin.'
    
    title = request.form["title"]
    director = request.form["director"]
    genre = request.form["genre"]
    rel_date = request.form["rel_date"]
    
    cur.execute("SELECT id FROM movies order by id desc;")
    next_id = int(cur.fetchone()[0]) +1
    
    cur.execute("INSERT INTO movies (id, title, director, genre, rel_date) VALUES (%s, %s, %s, %s, %s);", (next_id, title, director, genre, rel_date))
    connect.commit()
    
    return redirect(url_for('main', id=id))

# ! Additional Feature 2. Delete review
@app.route('/delete_review', methods=['post'])
def delete_review():
    user_id = request.form["user_id"]
    review_id = request.form["movie_id"]
    cur.execute("DELETE FROM reviews WHERE uid = %s and mid = %s;", (user_id,review_id))
    connect.commit()
    return redirect(url_for('user_info', id=user_id, user_id=user_id))

@app.route('/return', methods=['post'])
def re_turn():
    return render_template("main.html")


@app.route('/print_table', methods=['post'])
def print_table():
    cur.execute("SELECT * FROM users;")
    result = cur.fetchall()

    return render_template("print_table.html", users=result)

@app.route('/social_action', methods=['post'])
def social_action():
    id = request.form["id"]
    user_id = request.form["user_id"]
    action = request.form["action"]
    if id == user_id:
        # return error
        return 'You cannot follow or mute yourself.'
    if action == "follow":
        cur.execute("INSERT INTO ties (id, opid, tie) VALUES (%s, %s, 'follow');", (id, user_id))
    elif action == "mute":
        cur.execute("INSERT INTO ties (id, opid, tie) VALUES (%s, %s, 'mute');", (id, user_id))
    elif action == "unfollow":
        cur.execute("DELETE FROM ties WHERE id = %s AND opid = %s AND tie = 'follow';", (id, user_id))
    elif action == "unmute":
        cur.execute("DELETE FROM ties WHERE id = %s AND opid = %s AND tie = 'mute';", (id, user_id))
    connect.commit()
    return redirect(url_for('user_info', id=id, user_id=user_id))



@app.route('/register', methods=['post'])
def register():
    id = request.form["id"]
    password = request.form["password"]
    send = request.form["send"]
    if send == "sign up":
        # The id and password must be at least 1 character long
        if len(id) < 1 or len(password) < 1:
            return 'Invalid input. Please enter a valid id and password.'
        
        # Check if the id already exists in the "users" table
        cur.execute("SELECT id FROM users WHERE id = %s;", (id,))
        existing_user = cur.fetchone()
        
        if existing_user:
            # If the id already exists, redirect to "ID_collision.html"
            return render_template("login.html", error="The id already exists. Please try again.")
        else:
            # If the id doesn't exist, insert the new record into the "users" table
            cur.execute("INSERT INTO users (id, password, role) VALUES (%s, %s, %s);", (id, password, 'user'))
            connect.commit()
            # Redirect to a success page or return a success message
            return redirect(url_for('main',id=id))
    elif send == "sign in":
        cur.execute("SELECT id, password FROM users WHERE id = %s AND password = %s;", (id, password))
        existing_user = cur.fetchone()
        if existing_user:
            return redirect(url_for('main', id=id))
        else:
            return render_template("login.html", error="Invalid id or password. Please try again.")

if __name__ == '__main__':
    app.run()
