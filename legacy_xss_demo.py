"""
XSS Before / After demonstration (comments)
"""

from flask import Flask, request, render_template_string, redirect

app = Flask(__name__)

# Comments are kept in memory only, nothing touches the main MySQL database
comments = []

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <main class="wide-card">
        <h1>{{ title }}</h1>
        <p class="subtitle">{{ note }}</p>

        <form method="POST">
            <label for="comment">Your comment</label>
            <textarea id="comment" name="comment" rows="3"></textarea>
            <button type="submit">Post Comment</button>
        </form>

        <h2 class="section-heading">Recent comments</h2>
        {% for c in comments %}
            <article class="comment-item">
                {% if unsafe %}
                    <!-- BEFORE: |safe tells Jinja not to escape, so HTML runs in the browser -->
                    <p class="comment-text">{{ c|safe }}</p>
                {% else %}
                    <!-- AFTER: normal Jinja output, special characters are escaped -->
                    <p class="comment-text">{{ c }}</p>
                {% endif %}
            </article>
        {% else %}
            <p class="empty-state">No comments yet.</p>
        {% endfor %}

        <p><a href="/">Back</a></p>
    </main>
</body>
</html>
"""


@app.route("/")
def index():
    return ('<p><a href="/vulnerable/comments">BEFORE: vulnerable comments</a></p>'
            '<p><a href="/secure/comments">AFTER: secure comments</a></p>'
            '<p><a href="/clear">Clear comments</a></p>')


# BEFORE: comment text is rendered as raw HTML
@app.route("/vulnerable/comments", methods=["GET", "POST"])
def vulnerable_comments():
    if request.method == "POST":
        comments.append(request.form.get("comment", ""))
        return redirect("/vulnerable/comments")
    return render_template_string(PAGE, title="BEFORE - Vulnerable Comments",
                                  note="Comments are shown without escaping.",
                                  comments=comments, unsafe=True)


# AFTER: comment text is escaped, so it is shown as plain text
@app.route("/secure/comments", methods=["GET", "POST"])
def secure_comments():
    if request.method == "POST":
        comments.append(request.form.get("comment", ""))
        return redirect("/secure/comments")
    return render_template_string(PAGE, title="AFTER - Secure Comments",
                                  note="Comments are escaped before display.",
                                  comments=comments, unsafe=False)


@app.route("/clear")
def clear():
    comments.clear()
    return redirect("/")


if __name__ == "__main__":
    # Local demonstration only - never deploy this file
    app.run(host="127.0.0.1", port=5003, debug=False, threaded=False)
