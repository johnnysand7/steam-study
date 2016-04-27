from flask import Flask, render_template, request
import requests, re, graphlab, cPickle
from bs4 import BeautifulSoup

app = Flask(__name__)

#@app.route('/return_words', methods=['POST'])
#def return_words():
#    words = request.form.projectFilePath
#    return words.upper()




@app.route('/', methods=['POST'])
def my_form_post():

    url = request.form['text']
    if "steamcommunity.com" not in url:
        return render_template('index.html', bad_url="Must be a Steam community profile URL")#, link2=l2,link3=l3, name1=n1, name2=n2,name3=n3)
    response = requests.get(url)
    uid = re.search(r"([0-9]{17})", response.text).group()
    #processed_text = text.upper()
    top_3 = model.get_similar_users([int(uid)], k=3)["similar"]
    profile_url = "http://www.steamcommunity.com/profiles/"
    n1 = user_names["personaname"][int(top_3[0])].encode('ascii', 'ignore')
    n2 = user_names["personaname"][int(top_3[1])].encode('ascii', 'ignore')
    n3 = user_names["personaname"][int(top_3[2])].encode('ascii', 'ignore')
    i1 = user_names["avatarfull"][int(top_3[2])]
    l1 = profile_url + str(top_3[0])
    l2 = profile_url + str(top_3[1])
    l3 = profile_url + str(top_3[2])
    return render_template('index.html', link1=l1, link2=l2,link3=l3, name1=n1, name2=n2,name3=n3)#, img1=i1)


# home page
@app.route('/')
def index():
    return render_template('index.html')

# contact page
#@app.route('/contact')
#def contact():
#    return render_template('contact.html')

if __name__ == '__main__':
    with open("user_names") as f:
        user_names = cPickle.load(f)
    model = graphlab.load_model("first_model/first_model")
    app.run(host='0.0.0.0', port=8080, debug=True)
