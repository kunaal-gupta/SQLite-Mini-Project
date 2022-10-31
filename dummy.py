import sqlite3
from datetime import datetime
import os
import time
from getpass import getpass

conn = sqlite3.connect('./temp.db')
cur = conn.cursor()


def start_session(id):
    # Implement Start a session
    print()
    cur.execute("select * from sessions where uid=?", (id,))
    data = cur.fetchall()

    # Storing all the Sno related to given Uid
    store = []
    for row in data:
        store.append(row[1])

    # Finding a unique Sno
    i = 1
    while True:
        if i not in store:
            sno = i
            break
        i = i + 1

    now = datetime.now()
    current_date = now.date()

    query_vals = (id, sno, current_date)
    cur.execute("INSERT INTO sessions (uid, sno, start) VALUES (?,?,?)", query_vals)
    conn.commit()

    return sno


def search_songs_playlists():
    clearTerminal()
    while True:
        keyword = input("Please enter one or more keywords to search for, each separated by a single space: ")
        keywords = keyword.split(' ')
        uniqueKeywords = []
        results = []
        counts = {}
        query = "WITH temp as (select pid from playlists where "  # Construct temp table to get matching playlist IDs
        for k in keywords:
            if (k.lower() not in uniqueKeywords):
                uniqueKeywords.append(k.lower())
                query += "(title like '%{}%') or ".format(k)
        query = query[:len(query) - 3] + ") select sid, title, duration, ("  # Get matching songs
        for k in uniqueKeywords:  # get number of keyword matches
            query += "case when title like '%{}%' then 1 else 0 end + ".format(k)
        query = query[:len(query) - 3] + ") as rank, 'Song' from songs where "
        for k in uniqueKeywords:  # construct the WHERE clause
            query += "(title like '%{}%') or ".format(k)
        query =  query[:len(query) - 3] + "union select p.pid, p.title, sum(s.duration) as duration, ("  # Playlists
        for k in uniqueKeywords:  # get number of keyword matches
            query += "case when p.title like '%{}%' then 1 else 0 end + ".format(k)
        query = query[:len(query) - 3] + ") as rank, 'Playlist' from playlists p, plinclude pl, temp t, songs s "
        query += "where p.pid = t.pid and p.pid = pl.pid and pl.sid = s.sid group by p.pid order by rank DESC "
        
        cur.execute(query)
        data = cur.fetchall()
        i = 1
        for row in data:
            results.append('{}.\t{} ID: {} | Title: {} | Duration: {} seconds'.format(i, row[4], row[0], row[1], row[2]))
            i+=1

        # menu = "Please enter one or more keywords to search for, each separated by a single space: "
        # + keyword + "\nTotal number of results: {}".format(i-1)
        print("Total number of results: {}".format(i-1))
        j = 0
        print(*results[j:j+5],sep="\n")
        j += 5
        userInput = input("\nPlease select a row number, or type 'more' to see more results: ").lower()
        done = False
        while done == False:
            prompt = "\nUnrecognized input. Please select a row number, or type 'more' to see more results: "
            try:  # User entered a number
                userInput = int(userInput)-1
                if (userInput in range(len(data))):
                    done = True
                    song_action(data[userInput][0], data[userInput][1], data[userInput][4])
            except ValueError:  # User entered a string
                if userInput == 'more':
                    print(*results[j:j+5],sep="\n")
                    j += 5
                    prompt = "\nPlease select a row number, or type 'more' to see more results: "

            if done == False: userInput = input(prompt).lower()


# TODO -  If a playlist is selected, the id, the title and the duration of all songs in the playlist should be listed.
def song_action(selectionID, selectionTitle, songOrPlaylist):
    # Song Action
    clearTerminal()
    print("1. Listen to '{}'".format(selectionTitle) + "\n2. See more information\n3. Add {} to a playlist".format(selectionTitle))
    userInput = input("Please select an action to perform for the song '{}': ".format(selectionTitle))
    done = False
    while done == False:
        prompt = "Unrecognized input. Please select an action to perform for the song '{}': ".format(selectionTitle)
        try:  # User entered a number
            userInput = int(userInput)
            if userInput in range(1,4):
                done = True
                if userInput == 1:  # Listen - TODO FINISH THIS
                    print("now listening")
                elif userInput == 2:  # See more information
                    # Print all artists that performed the song
                    cur.execute("SELECT a.name from perform p, artists a where p.sid = ? and p.aid = a.aid", (selectionID,))
                    artists = cur.fetchall()
                    result = "Artist(s): "
                    for a in artists:
                        result += a[0] + ", "
                    print("\n" + result[:len(result) - 2])
                    
                    # Print id, title and duration of song
                    cur.execute("SELECT * from songs where sid = ?;", (selectionID,))
                    data = cur.fetchall()
                    print('Song ID: {}\nTitle: {}\nDuration: {} seconds'.format(data[0][0], data[0][1], data[0][2]))

                    # Print matching playlists
                    cur.execute("SELECT p.title from playlists p, plinclude pl where pl.sid = ? and pl.pid = p.pid", (selectionID,))
                    playlists = cur.fetchall()
                    result = "Playlist(s): "
                    cnt = 0
                    for p in playlists:
                        result += p[0] + ", "
                        cnt += 1
                    if cnt == 0:
                        print("This song does not appear in any playlists.\n")
                    else:
                        print(result[:len(result) - 2] + "\n")
                else:  # Add it to a playlist - TODO FINISH THIS
                    print("adding to a playlist")
            else:
                prompt = "Invalid number entered! Please enter a number between 1 and 3: "
        except ValueError:  # User did not enter a number
            prompt = "Input was not a number! Please enter a valid number between 1 and 3: "
        
        if done == False: userInput = input(prompt)


def search_artists():
    keyword = input('Search for an artist\'s name: ').strip()
    cur.execute("with e1 as (Select a.name ename, count(a.name) num from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and (s.title like '%{}%' or a.name like '%{}%') group by ename)".format(keyword, keyword) + " Select a.name, a.nationality, count(s.sid) from songs s, artists a, perform p, e1 where a.aid = p.aid and s.sid = p.sid and e1.ename = a.name group by a.name order by num desc")
    data = cur.fetchall()

    if len(data) == 0:
        print('\nSorry! There is no artist with this name')

    else:
        i = 0
        print()
        print(str('Found ' + str(len(data)) + ' matching results (Name, Nationality, Number of Songs)').center(150, '-'))

        for j in data:
            print(j)

            i +=1
            if i == len(data):
                print(i, 'hi')
                print('This is end of our search result.'.center(150, '-'))
                UserInput = input('Do you want to continue searching ' + str(len(data) -i) + ' left (Press Y/N) or Select an artist (type name)? ').strip()
                search_song(UserInput)

            if i % 5 == 0:
                print()
                UserInput = input('Do you want to continue searching ' + str(len(data) -i) + ' left (Press Y/N) or Select an artist (type name)? ').strip()
                print()
                if UserInput.lower() == 'y':
                    continue

                elif UserInput.lower() == 'n':
                    print()
                    print('This is end of our search result.'.center(150, '-'))
                    break

                else:
                    search_song(UserInput)
                    break

def search_song(UserInput):
    # created for search_artist function to avoid writing duplicate code. This function is not required by assignment schema

    cur.execute("Select s.sid, s.title, s.duration from songs s, artists a, perform p where a.aid = p.aid and s.sid = p.sid and a.name in {};".format((UserInput.title(), UserInput.lower(), UserInput.upper(), UserInput.capitalize())))
    artist_data = cur.fetchall()

    if len(artist_data) == 0:
        print('Invalid choice! Try again later ')

    print(str('Songs of ' + UserInput.title() + ' (id, title, duration)').center(150, '-'))
    for i in artist_data:
        print(i)

    print()
    SongSelection = input('Do you want to select any song - Enter it\'s name: ').strip()




def user_session(id):
    # User Session
    menu = "User Session\n1. Start a session\n2. Search for songs and playlists\n3. Search for artists\n4. End the session"
    while True:
        print(menu)

        user_option = input(str("Please enter an option #: ")).strip()
        while (user_option not in ["1", "2", "3", "4"]):
            clearTerminal()
            print(menu)
            user_option = input(str("Invalid option entered. Please enter an option #: ")).strip()

        if user_option == "1":
            returned_sno = start_session(id)

        elif user_option == "2":
            search_songs_playlists()

        elif user_option == "3":
            search_artists()

        elif user_option == "4":
            now = datetime.now()
            current_date = now.date()
            cur.execute("UPDATE sessions set end = ? where uid = ? and sno = ?", (current_date, id, returned_sno))
            conn.commit()
            break

        else:
            print("Please enter a valid Option #")


def artist_session():
    print("Artist Session")


def clearTerminal():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear the system terminal to look cleaner


def main():
    while True:
        userfound = False
        artistfound = False

        clearTerminal()  # Clear the system terminal to look cleaner
        id = input("Login Screen: Please enter your ID:  ").strip()
        cur.execute("select name from users where uid=?", (id,))
        data = cur.fetchall()

        if not data:
            userfound = False
        else:
            userfound = True
            foundUserName = data[0][0]

        cur.execute("select name from artists where aid=?", (id,))
        data = cur.fetchall()

        if not data:
            artistfound = False
        else:
            artistfound = True
            foundArtistName = data[0][0]

        # If the ID exists in both users and artists
        if (artistfound == True and userfound == True):
            print("This ID exists for both a user and an artist")
            print("Press 1 to log in as the user {}: {}".format(id, foundUserName))
            print("Press 2 to log in as the artist {}: {}".format(id, foundArtistName))

            user_option = 0
            user_option = input("\nPlease enter your option: ")

            while (user_option != "1" and user_option != "2"):
                print("\r", end="")
                user_option = input("Invalid option. Please enter either 1 for user or 2 for artist: ").strip()

            userpass = getpass(
                prompt=("Please enter your password (as a" + (" user): " if user_option == "1" else "n artist): ")))
            cur.execute("select {} from {} where {}=? and pwd=?".format(
                "uid" if user_option == "1" else "aid", "users" if user_option == "1" else "artists",
                "uid" if user_option == "1" else "aid"), (id, userpass))
            data = cur.fetchall()

            while (not data):
                userpass = getpass(prompt="Incorrect password. Please try again: ")
                cur.execute("select {} from {} where {}=? and pwd=?".format(
                    "uid" if user_option == "1" else "aid", "users" if user_option == "1" else "artists",
                    "uid" if user_option == "1" else "aid"), (id, userpass))
                data = cur.fetchall()

            print("Log-in Successful! Navigating to main screen...")
            time.sleep(0)
            clearTerminal()
            user_session(id)


        # If the id exists for only the user
        elif (userfound == True and artistfound == False):
            userpass = getpass(prompt="Please enter your password: ")
            cur.execute("select uid from users where uid=? and pwd=?", (id, userpass))
            data = cur.fetchall()

            while (not data):
                userpass = getpass(prompt="Incorrect password. Please try again: ")
                cur.execute("select uid from users where uid=? and pwd=?", (id, userpass))
                data = cur.fetchall()
            else:
                print("Log-in Successful! Navigating to main screen...")
                time.sleep(0)
                clearTerminal()
                user_session(id)

        # If the id exists for only the artists
        elif (userfound == False and artistfound == True):
            userpass = getpass(prompt="Please Enter your Password: ")
            cur.execute("select aid from artists where aid=? and pwd=?", (id, userpass))
            data = cur.fetchall()

            while (not data):
                userpass = getpass(prompt="Incorrect password. Please try again: ")
                cur.execute("select aid from artists where aid=? and pwd=?", (id, userpass))
                data = cur.fetchall()
            else:
                print("Log-in Successful! Navigating to main screen...")
                time.sleep(0)
                clearTerminal()
                user_session(id)

                # Invalid Id. Ask for Sign-up
        else:
            print("No valid user or artist ID found. Would you like to sign-up as a new user?")
            user_option = input(str("Press 1 to continue!! ")).strip()

            if user_option == "1":
                id = input("Please provide a user-id: ").strip()
                cur.execute("select uid from users where uid=?", (id,))
                data = cur.fetchall()

                if not data:
                    name = input("Please provide a name: ").strip()
                    password = input("Please provide a Password: ").strip()

                    query_vals = (id, name, password)
                    cur.execute("INSERT INTO users (uid, name, pwd) VALUES (?,?,?)", query_vals)
                    conn.commit()

                    print("Sign-Up Successfull! You are now logged-in")
                    user_session(id)

                else:
                    print("This user-id already exists.")

# search_artists()
main()
