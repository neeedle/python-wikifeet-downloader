import requests
import re
import json 
import os
import argparse
import sys

# using this header to prevent the server from blocking our script, forbidding (403) our access to the website
non_bot_header = {'User-Agent': 'Mozilla/5.0'}

# pattern used to recognize if given url is a valid wikifeet one
wikifeet_pattern = 'https:\/\/www\.wikifeet\.com\/[a-zA-Z_]+'


# JSONExtractor class extracts the javascript associative array found in every model html page;
# it contains a lists of every model feet pic and can be interpreted as json data
class JSONExtractor:

    js_variable = "messanger['gdata'] = ["

    def __init__(self, text=""):
        self.text = text

    def set_text(self, text):
        self.text = text

    def get_json_dict(self):
        # pinpointing the exact location of the json dictionary containing the picture ids
        start_index = self.text.find(self.js_variable)
        start_index = start_index + len(self.js_variable) - 1
        end_index = self.text.find(';', start_index)
        actress_json_data_string = self.text[start_index:end_index]
        return json.loads(actress_json_data_string)


# LinkBuilder class needs a model name to be instantiated, which is then used
# to build the link to the actual picture
class LinkBuilder:

    def __init__(self, model):
        self.model = model.replace('_', '-')

    def set_model(self, model):
        self.model = model.replace('_', '-')

    def build_link(self, pid):
        return "https://pics.wikifeet.com/" + self.model + "-Feet-" + str(pid) + ".jpg"


# JPGDownloader class can download a picture from any given link to a specified path
class JPGDownloader:

    def __init__(self, path):
        self.path = path

    def download_image(self, link):
        filename = link.split('/')[-1]
        filepath = os.path.join(self.path, filename)
        r = requests.get(link, non_bot_header, stream=True)
        if r.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(r.content)
        else:
            print("Error: {}".format(r.status_code))


# pid = picture id, used later to build a link to the picture itself
def build_pid_list(json_dict):
    pids = []
    for index, element in enumerate(json_dict):
        pids.append(json_dict[index]['pid'])
    pids.sort()

    return pids


if __name__=="__main__":
    try:

        # obtaining arguments from command line 
        parser = argparse.ArgumentParser()

        parser.add_argument("url")
        parser.add_argument("--download_path")

        args = parser.parse_args()
        url = args.url

        # get model name from the link ending
        model_name = url.split('/')[-1]


        # if link looks like a wikifeet.com one, proceed
        if re.search(wikifeet_pattern, url):
            r = requests.get(url, non_bot_header)

            # checking if the link is actually valid, and if we can obtain (GET) the page
            if r.status_code == 200:

                # begin extracting procedure on downloaded page
                json_extractor = JSONExtractor(r.text)
                extracted_json = json_extractor.get_json_dict()

                pids = build_pid_list(extracted_json)
                link_builder = LinkBuilder(model_name)

                # deciding where to put downloaded pictures
                if args.download_path:
                    if os.path.exists(args.download_path):
                        download_path = args.download_path
                    else:
                        print("Path does not exist, it will be created")
                        os.mkdir(args.download_path)
                        print(args.download_path)
                        download_path = args.download_path
                else:
                    download_path = os.path.join(os.getcwd(), model_name)
                    if not os.path.exists(download_path):
                        os.mkdir(download_path)
                
                # now we're ready to go
                jpgdownloader = JPGDownloader(download_path)

                # download every picture by building the link with a pid first, 
                # then feeding it to the JPGDownloader object "download_image" method;
                # progress is expressed in % points
                for index, pid in enumerate(pids):
                    link = link_builder.build_link(pid)
                    jpgdownloader.download_image(link)
                    print("Progress: {:.1f}%".format(((index + 1) / len(pids))*100), end='\r')
            else:
                print("Error: {}".format(r.status_code))
        else:
            print("Error: No wikifeet.com url detected")
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        sys.exit(0)
    sys.exit(0)
