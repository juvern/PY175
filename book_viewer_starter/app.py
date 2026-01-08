from flask import Flask, render_template, g, redirect, request

# g is a special object unique for each request

app = Flask(__name__) # creates an instance of the Flask class


@app.before_request # done before every request
def load_content():
    with open("book_viewer/data/toc.txt", "r") as f:
        g.contents = f.readlines() # globally available for the single request 


# Define and register the filter using `template_filter` decorator
@app.template_filter('in_paragraphs')
def in_paragraphs(text):
    return text.split("\n\n")

# when browser visits /, call this function
@app.route("/")
def index(): # view function
    
    return render_template('home.html', contents=g.contents)

@app.route("/chapters/<page_num>/")
def chapter(page_num):

    if page_num.isdigit() and (1 <= int(page_num) <= len(g.contents)):
        chapter_title = f"Chapter {page_num}"
        chapter_name = g.contents[int(page_num) - 1]

        chapter_file = f"book_viewer/data/chp{page_num}.txt"
        with open(chapter_file, "r") as f:
            chapter = f.read()

        return render_template('chapter.html', 
                                chapter_title=chapter_title,
                                chapter_name=chapter_name,
                                contents=g.contents, 
                                chapter=chapter,
                                chapter_file=chapter_file)
    else:
        return redirect("/")        


@app.route("/search")
def search():
    query = request.args.get('query', '')

    page_num = 1
    results = {} # {'chapter': [(1, 'some'), (2, 'nother')]}
    for chapter_title in g.contents:
        chapter_file = f"book_viewer/data/chp{page_num}.txt"
        
        with open(chapter_file, "r") as f:
            paragraphs = f.read()
        
        for id_num, paragraph in enumerate(paragraphs.split("\n\n")):
            if query in paragraph:
                results.setdefault(chapter_title, []).append((id_num, paragraph))
        
        page_num += 1


    return render_template('search.html',
                            contents=g.contents,
                            query=query,
                            results=results)    


@app.errorhandler(404)
def page_not_found(_error):
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=5003)