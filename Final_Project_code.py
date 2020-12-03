from bs4 import BeautifulSoup
import requests
import json
import plotly.graph_objects as go
import sqlite3

CACHE_FILE_NAME = 'movie_cache.json'

def open_cache():
    
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_contents = cache_file.read()
        cache_dict = json.loads(cache_contents)
        cache_file.close()
    except:
        cache_dict = {}
    return cache_dict


def save_cache(cache_dict):
    
    dumped_json_cache = json.dumps(cache_dict)
    fw = open(CACHE_FILE_NAME,"w")
    fw.write(dumped_json_cache)
    fw.close() 

def create_movie_table(cur):
    create_movie = '''
        CREATE TABLE IF NOT EXISTS "Movies" (
            "Id" INTEGER NOT NULL,
            "Name"        TEXT NOT NULL,
            "ReleaseInfo"  TEXT NOT NULL,
            "Duration" TEXT NOT NULL,
            "Category"  TEXT NOT NULL,
            "RatingScore"    TEXT NOT NULL,
            "RatingCount"    TEXT NOT NULL,
            PRIMARY KEY("Id" AUTOINCREMENT)
        );
    '''
    cur.execute(create_movie)
    conn.commit()

def create_rating_table(cur):
    create_rating = '''
        CREATE TABLE IF NOT EXISTS "RatingDetail" (
            "Id"   INTEGER NOT NULL,
            "10"  TEXT NOT NULL,
            "9"  TEXT NOT NULL,
            "8"  TEXT NOT NULL,
            "7"  TEXT NOT NULL,
            "6"  TEXT NOT NULL,
            "5"  TEXT NOT NULL,
            "4"  TEXT NOT NULL,
            "3"  TEXT NOT NULL,
            "2"  TEXT NOT NULL,
            "1"  TEXT NOT NULL,
            PRIMARY KEY("Id" AUTOINCREMENT)
        );
    '''
    cur.execute(create_rating)
    conn.commit()

class Movie():

    def __init__(self,name,release_info,duration,category,rating,rating_count,rating_detail_url):
        self.name = name
        self.release_info = release_info
        self.duration = duration
        self.category = category
        self.rating = rating
        self.rating_count = rating_count
        self.rating_detail_url = rating_detail_url
    
    def info(self):
        return "'" + self.name + "'" + " releasing on " + self.release_info + " (" + self.duration + ") [" + self.category + "]  " + self.rating + "/10"


def get_popular_movies():

    BASE_URL = "https://www.imdb.com/chart/moviemeter/?ref_=nv_mv_mpm"
    movie_list_class = "lister-list"

    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text,'html.parser')
    
    movie_list_parent = soup.find("tbody",class_ = movie_list_class)
    
    movie_list_tds = movie_list_parent.find_all("td",class_="titleColumn")

    movie_list_as = []
    for td in movie_list_tds:
        movie_list_a = td.find("a",recursive=False)
        movie_list_as.append(movie_list_a)

    info_dict = {}
    for a in movie_list_as:
        title = a.string.strip()
        sufurl = a['href']
        url = "https://imdb.com"+sufurl
        info_dict[title] = url

    return info_dict

def get_popular_movies_with_cache():

    if "popular movies" in CACHE_DICT.keys():
        print("Using Cache...")
        return CACHE_DICT["popular movies"]
    else:
        print("Fetching...")
        CACHE_DICT["popular movies"] = get_popular_movies()
        save_cache(CACHE_DICT)
        return CACHE_DICT["popular movies"]


def get_movie_instance(url):

    info_dict = get_popular_movies_with_cache()
    for key,value in info_dict.items():
        if url in value:
            movie_name = key
    response = requests.get(url)
    soup = BeautifulSoup(response.text,'html.parser')
    try:
        movie_release_info = soup.find("a",title = "See more release dates").string.strip()
    except:
        movie_release_info = '(unknown yet)'
    
    try:
        movie_duration = soup.find("time").string.strip()
    except:
        movie_duration = 'N/A'
    try:
        movie_category = soup.find("div",class_="subtext").find("a").string.strip()
    except:
        movie_category = 'N/A'
    try:
        movie_rating = soup.find("span",itemprop = "ratingValue").string.strip()
    except:
        movie_rating = 'N/A'
    try:
        movie_rating_count = soup.find("span",itemprop = "ratingCount").string.strip()
    except:
        movie_rating_count = 0
    try:
        movie_rating_url = "https://imdb.com" + soup.find("div",class_="imdbRating").find("a")["href"]
    except:
        movie_rating_url = ''

    return Movie(movie_name,movie_release_info,movie_duration,movie_category,movie_rating,movie_rating_count,movie_rating_url)

def get_movie_instance_with_cache(url):

    if url in CACHE_DICT.keys():
        return Movie(CACHE_DICT[url]["name"],CACHE_DICT[url]["release_info"],CACHE_DICT[url]["duration"],CACHE_DICT[url]["category"],CACHE_DICT[url]["rating"],CACHE_DICT[url]["rating_count"],CACHE_DICT[url]["rating_detail_url"])
        
    else:
        movie_ins = get_movie_instance(url)
        CACHE_DICT[url] = movie_ins.__dict__
        save_cache(CACHE_DICT)
        return movie_ins

def print_movie_list(info_dict):
    
    print("\n Most Popular Movies determined by IMDb Users \n")
    print("="*50)
    i = 1
    for key in info_dict.keys():
        print("[" + str(i) +"]" + key)
        i += 1

def get_rating_info(ins):

    if ins.rating_detail_url == '':
        return "\n No ratings available yet. \n"
    else:
        response = requests.get(ins.rating_detail_url)
        soup = BeautifulSoup(response.text,'html.parser')

        rating_count_parent = soup.find("table",cellpadding="0")
        rating_count_list = rating_count_parent.find_all("tr")

        votes_list = []
        i = 11

        for row in rating_count_list:
            votes = row.find("div",class_="leftAligned").string.strip()
            votes_list.append((i,votes))
            i -= 1
        
        votes_list.pop(0)        
        return votes_list

def get_rating_info_with_cache(ins):

    if ins.name in CACHE_DICT.keys():
        print("Using Cache...")
        return CACHE_DICT[ins.name]
    else:
        print("Fetching...")
        CACHE_DICT[ins.name] = get_rating_info(ins)
        save_cache(CACHE_DICT)
        return CACHE_DICT[ins.name]

def print_rating_info(rating_list):

    for item in rating_list:
        print(str(item[0]) + ": " + str(item[1]))

def rating_graph(rating_list):

    rating_scale = []
    count = []

    for item in rating_list:
        rating_scale.append(item[0])
        count.append(item[1])
    
    bar_data = go.Bar(x=rating_scale, y=count)
    fig = go.Figure(data=bar_data)
    fig.show()


if __name__ == "__main__":
    CACHE_DICT = open_cache()
    conn = sqlite3.connect("movie_info.sqlite")
    cur = conn.cursor()
    create_movie_table(cur)
    create_rating_table(cur)
    info_dict = get_popular_movies_with_cache()
    print_movie_list(info_dict)
    print("-"*50)
    while True:
        ans1 = input("Enter the number of the movie you want to see more details or 'exit'. \n\n")
        if ans1 == "exit":
            break
        elif ans1.isnumeric() and int(ans1) >= 1 and int(ans1) <= 100:
            for key,value in info_dict.items():
                movie_name = list(info_dict.keys())[int(ans1)-1]
                movie_url = info_dict[movie_name]
            movie_ins = get_movie_instance_with_cache(movie_url)
            insert_info = '''
            INSERT INTO Movies
            VALUES (NULL,?,?,?,?,?,?)
            '''
            movie_info = [movie_ins.name,movie_ins.release_info,movie_ins.duration,movie_ins.category,movie_ins.rating,movie_ins.rating_count]
            cur.execute(insert_info,movie_info)
            conn.commit()
            print(movie_ins.info() + "\n")
            print("-"*40)
            if movie_ins.rating == "N/A":
                insert_rating = '''
                INSERT INTO RatingDetail
                VALUES (NULL,?,?,?,?,?,?,?,?,?,?)
                '''
                ratings = ['N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A','N/A']
                cur.execute(insert_rating,ratings)
                conn.commit()
                while True:
                    ans2 = input("Enter 'back' to see another movie or 'exit' to end the search. \n")
                    if ans2 == "back":
                        break
                    elif ans2 == "exit":
                        break
                    else:
                        print("Invalid Input. \n")
                if ans2 == "exit":
                    break
            else:
                while True:
                    ans2 = input("Do you want to see the rating distribution of this movie? Y/N \n")
                    if ans2.lower() == "y":
                        rating_list = get_rating_info_with_cache(movie_ins)
                        insert_rating = '''
                        INSERT INTO RatingDetail
                        VALUES (NULL,?,?,?,?,?,?,?,?,?,?)
                        '''
                        ratings = []
                        for item in rating_list:
                            rating = item[1]
                            ratings.append(rating)
                        cur.execute(insert_rating,ratings)
                        conn.commit()
                        while True:
                            ans3 = input("Do you prefer number scale or graph? Enter 1 for number, 2 for graph, 3 for both. \n")
                            if int(ans3) == 1:
                                print("-"*30)
                                print_rating_info(rating_list)
                                break
                            elif int(ans3) == 2:
                                rating_graph(rating_list)
                                break
                            elif int(ans3) == 3:
                                print("-"*30)
                                print_rating_info(rating_list)
                                rating_graph(rating_list)
                                break
                            else:
                                print("Invalid input. Please enter either 1, 2 or 3. \n")
                        break
                    elif ans2.lower() == "n":
                        break
                    else:
                        print("Invalid input. Please enter 'Y' or 'N'. \n")
        else:
            print("Please enter a number between 1 and 100 or 'exit'. \n")
    
    save_cache(CACHE_DICT)
