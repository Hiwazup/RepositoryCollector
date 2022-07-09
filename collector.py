"""
This program finds and downloads a dataset of public repositories in Git through a process of finding popular
repositories that are found with a random word.
"""
import configparser
import datetime
import io

import requests
import zipfile
import time

# Defaults. Set in config.ini
number_of_repos_per_word = 10
number_of_repos_wanted = 100
random_words = []
directory = "C:/"
token = ""


def main():
    read_config_file()
    start_time = time.time()
    print("***** GETTING %d REPOS *****" % number_of_repos_wanted)
    print("Target directory is %s" % directory)
    repos = get_repos()
    end_time = time.time()
    print("Retrieval completed. Total time taken is %s" % str(datetime.timedelta(seconds=(end_time - start_time))))
    download_repos(repos)
    end_time = time.time()
    print("Download completed. Total time taken is %s" % str(datetime.timedelta(seconds=(end_time - start_time))))
    print("***** FINISHED GETTING REPOS *****")


def read_config_file():
    """
    Gets the values from config.ini and fills them into the global variables
    """
    config = configparser.ConfigParser()
    config.sections()
    config.read('config.ini')
    if 'github.com' in config:
        global token
        token = config['github.com']['token']
    if 'repositories' in config:
        global number_of_repos_wanted
        number_of_repos_wanted = int(config['repositories']['number_of_repos_wanted'])

        global number_of_repos_per_word
        number_of_repos_per_word = int(config['repositories']['number_of_repos_per_word'])

        global directory
        directory = config['repositories']['directory']


def get_repos():
    """
    Gets a list of repositories using multiple random words to make sure that the repositories are a purely random
    sample.
    :return: The list of repositories.
    """
    count = 0
    repos = []
    while len(repos) < number_of_repos_wanted:
        count = count + 1
        word = get_random_word()
        repos_still_needed = number_of_repos_wanted - len(repos)
        number_of_repos_for_search = number_of_repos_per_word if (repos_still_needed >= number_of_repos_per_word) \
            else repos_still_needed
        repos_found = find_x_repos_for_text(word, number_of_repos_for_search)
        repos.extend(repos_found)
        if len(repos_found) > 0:
            print("I now have %d repos thanks to the word %s" % (len(repos), word))
    print("Took %d words to find all %d repos" % (count, number_of_repos_wanted))
    return repos


def get_random_word():
    """
    Gets a random word from a public API.
    :return: The word found.
    """
    response = requests.get("https://random-word-api.herokuapp.com/word").json()
    word = response[0]

    if word in random_words:
        return get_random_word()

    random_words.append(word)
    return word


def find_x_repos_for_text(text, number_of_repos):
    """
    Collects a list of repositories that are found with the string found in text. The sleep is added for rate limiting.
    :param text: The text to be used in the search query.
    :param number_of_repos: The maximum amount of repositories to find with the search.
    :return: The list of repositories found.
    """
    result = []
    response = requests.get(
        "https://api.github.com/search/repositories?q=%s+language:java&sort=stars&order=desc" % text).json()
    if 'items' in response:
        items = response['items']
        for item in items:
            if len(result) < number_of_repos:
                if is_suitable_repo(item):
                    full_name = item['full_name']
                    result.append(full_name)

    time.sleep(3)
    return result


def is_suitable_repo(repo):
    """
    Checks if a repository fits the set criteria for the dataset. The requirements are:
        * The repo is public
        * The repo is not a fork
        * The repo consists of over 2000 lines
        * The repo has more than 100 stars
        * The repo has been updated in the last year (2021 or 2022)
        * The repo is not android based
    :param repo: The repo to examine
    :return: True if it's suitable, False otherwise
    """
    is_suitable = True
    if repo['private'] or repo['fork'] or repo['size'] < 2000 or repo['stargazers_count'] < 100 or \
            not str(repo['updated_at']).startswith(tuple(["2021", "2022"])) or repo_contain_android(repo):
        is_suitable = False

    return is_suitable


def repo_contain_android(repo):
    """
    Checks it the given repository appears to be android based.
    :param repo: The repository to examine
    :return: True if it seems to be android based otherwise False
    """
    topics = repo['topics']
    for topic in topics:
        if 'android' in str(topic).lower():
            return True
    if 'android' in str(repo['description']).lower():
        return True

    return False


def download_repos(repos):
    """
    Calls download_repo for each repository.
    :param repos: The list of repositories to download.
    """
    for repo in repos:
        download_repo(repo)


def download_repo(repo):
    """
    Downloads a repository as a zip file and then extracts it to the directory value set globally. The sleep is added
    for rate limiting.
    :param repo: The repository to download
    """
    print("Creating %s" % repo)
    try:
        repo = requests.get("https://api.github.com/repos/%s/zipball" % repo,
                            headers={"Authorization": "token %s" % token},
                            stream=True)
        zip = zipfile.ZipFile(io.BytesIO(repo.content))
        zip.extractall(directory)
    except:
        print("ERROR: Unable to download %s" % repo)
    time.sleep(2)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
