from bs4 import BeautifulSoup
import os
import logging
import json
import re

class Utilities():
    """Class that contains utility methods to handle commonly used functions"""
    def __init__(self):
        # code to setup logging obj
        self.logger = logging.getLogger("Utilities")
        self.logger.setLevel(level=logging.DEBUG)
        for hdlr in self.logger.handlers[:]:    # remove all old handlers
            self.logger.removeHandler(hdlr)
        
        # create and add file handler to logging obj
        fileh = logging.FileHandler('Utilities.log')
        formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S")
        fileh.setFormatter(formatter)
        self.logger.addHandler(fileh)
    
    def parse_photo_roll_raw_info(self, path_to_photo_roll_raw_info):
        """Parses individual photo info from raw photo roll data in html format.
        Returns boolean indicating whether photo roll data parsing is successful or not."""
        json_photos_info_path = 'photos_info.json'
        # if given path to raw photots info exits, proceed to parse it
        if(os.path.exists(path_to_photo_roll_raw_info)):
            with open(path_to_photo_roll_raw_info, 'r') as f:
                raw_info = f.read()
            new_objects_added = 0
            new_photos_added = 0
            json_photos_info = {}
            # if output file path exits, extract existing json photos info
            if(os.path.exists(json_photos_info_path)):
                with open(json_photos_info_path, 'r') as f:
                    try:
                        json_photos_info = json.load(f)
                    # if output file parsing fails, assume no initial info
                    except:
                        json_photos_info = {}
                        self.logger.debug("Loading data from existing photo roll json info file failed. Assuming no initial info.")
            try:
                # extract list of li elements which contain photo info
                self.logger.debug("Starting photo roll raw info file parsing.")
                soup = BeautifulSoup(raw_info, "html.parser")
                list_elements = soup.find_all("li")
                
                # for each li element
                for list_element in list_elements:
                    # extract photo heading
                    heading = list_element.find('h3')
                    # if heading is present
                    if(heading):
                        try:
                            # extract object info for the current photo
                            object_names_in_heading = [x.strip() for x in heading.text.split('(')]
                            object_name_primary = object_names_in_heading[0]
                            object_names = [object_name_primary]
                            if("Messier" in object_name_primary):
                                object_names.append("M" + re.search(r'\d+', object_name_primary).group())
                            if(len(object_names_in_heading) > 1):
                                secondary_names = [x.strip() for x in object_names_in_heading[1].strip(')').split('/')]
                                if len(secondary_names) > 1:
                                    if "NGC" in secondary_names[0] and "NGC" not in secondary_names[1]:
                                        secondary_names[1] = "NGC " + secondary_names[1]
                                object_names += secondary_names
                            
                            # extract photo url for the current photo
                            photo_url = re.search('(http.*)\"',list_element.find('a').get('style')).group(1)
                            # extract photo description for the current photo
                            photo_desc = list_element.find_all('p')
                            curr_photo_info = {
                                "photo_url": photo_url,
                                "photo_desc": {}
                            }
                            for desc in photo_desc:
                                curr_desc = [x.strip() for x in desc.text.split(':', 1)]
                                if(len(curr_desc) > 1):
                                    curr_photo_info["photo_desc"][curr_desc[0]] = curr_desc[1]
                                else:
                                    curr_photo_info["photo_desc"]["Date"] = curr_desc[0]
                            
                            # if any photos already present for the current object
                            if object_name_primary in json_photos_info:
                                # add current photo to the object if it doesn't already exist
                                if curr_photo_info not in json_photos_info[object_name_primary]["photos"]:
                                    json_photos_info[object_name_primary]["photos"].append(curr_photo_info)
                                    new_photos_added += 1
                            # else if no photos are present for the current object
                            else:
                                # add current object along with current photo
                                json_photos_info[object_name_primary] = {
                                    "object_names": object_names,
                                    "photos": [curr_photo_info]
                                }
                                new_photos_added += 1
                                new_objects_added += 1
                        except Exception as err:
                            self.logger.debug(f"Could not parse photo info from {str(heading)} - {str(err)}")
                
                # write final photos info to output file
                with open(json_photos_info_path, 'w') as f:
                    json.dump(json_photos_info, f, indent = 4)
                self.logger.debug(f"Photo roll raw info file parsing complete. {str(new_photos_added)} new photos added. {str(new_objects_added)} new objects added.")
                return True
            # if any error occurs while parsing individual photos, return True and log successfully extracted photos count till now.
            except Exception as err:
                self.logger.debug(f"Photo roll raw info file parsing could not be completed successfully - {str(err)}. {str(new_photos_added)} new photos added. {str(new_objects_added)} new objects added.")
                return True
        # else if given path to raw photots info does not exit, return False
        else:
            self.logger.debug("Photo roll raw info file doesn't exist!!")
            return False
        
    def extract_urls_to_objects_with_no_photos(self, path_to_object_info_json_file, path_to_photos_json_file):
        """Parses photos info + object info and returns urls to objects with no photos."""
        
        # if both object info file and photo info file exists
        if(os.path.exists(path_to_object_info_json_file) and os.path.exists(path_to_photos_json_file)):
            # extract object info
            object_info = {}
            with open(path_to_object_info_json_file, 'r') as f:
                object_info = json.load(f)
            # extract photo info
            photo_info = {}
            with open(path_to_photos_json_file, 'r') as f:
                photo_info = json.load(f)
            
            object_names_from_object_info = list(object_info.keys())
            urls_to_objects_with_no_photos = []
            # for each object in object info
            for obj in object_names_from_object_info:
                is_obj_found = False
                # check if any photo exist for the current object (check photos with any of the possible object names)
                for photos_obj in photo_info.keys():
                    for name in photo_info[photos_obj]["object_names"]:
                        if name.upper() in obj.upper():
                            is_obj_found = True
                # f no photo is found, append current object url to the list of urls to the objects with no photos
                if not is_obj_found:
                    urls_to_objects_with_no_photos.append(object_info[obj]["object_url"])
            self.logger.debug(f"{str(len(urls_to_objects_with_no_photos))} objects found without any photos.") 
            return urls_to_objects_with_no_photos
        # else if one or more files doesn't exist, return empty list
        else:
            return []