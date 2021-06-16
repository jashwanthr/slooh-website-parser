from utilities import Utilities
from slooh_website_parser import SloohWebsiteParser

import sys
import os
import schedule
import time
import getpass

username = getpass.getuser()

global slooh_web_parser_obj
global util_obj

def parse_slooh_photo_roll():
    """Parse photo roll from https://slooh.com/"""
    slooh_web_parser_obj.search_parser()
    if(slooh_web_parser_obj.login()):
        photo_roll_parsing_status = slooh_web_parser_obj.photo_roll_parser()
        if(photo_roll_parsing_status):
            slooh_web_parser_obj.logout()
            util_obj.parse_photo_roll_raw_info('photo_roll_info.txt')
    else:
        print("Login failed!! Please try again...")

def reserve_missions():
    """Reserve missions in https://slooh.com/ for objects with no images yet"""
    objects_without_photos = util_obj.extract_urls_to_objects_with_no_photos('slooh_object_info.json', 'photos_info.json')
    active_missions = []
    if(os.path.exists('ActiveMissions.txt')):
        with open('ActiveMissions.txt', 'r') as f:
            active_missions = f.readlines()
    for object_url in objects_without_photos:
        if (object_url + '\n') not in active_missions:
            mission_booking_status, active_mission_count = slooh_web_parser_obj.reserve_mission_using_object_url(object_url)
            if(mission_booking_status):
                active_missions.append(object_url + '\n')
            if(active_mission_count >= 5):
                break
    with open('ActiveMissions.txt', 'a') as f:
        f.writelines(active_missions)
        
def dispose_slooh_obj():
    """Dispose slooh object"""
    slooh_web_parser_obj.logout()

def work():
    """Perform slooh photo roll parsing and mission reservation"""
    parse_slooh_photo_roll()    # parse photo roll to extract latest photos info
    reserve_missions()          # reserve missions for objects with no photos
    dispose_slooh_obj()         # dispose slooh object

if __name__ == '__main__':
    # Create slooh website parser object - sys.argv[1] = email, sys.argv[2] = password, sys.argv[3] = chromedriver path
    slooh_web_parser_obj = SloohWebsiteParser(sys.argv[1], sys.argv[2], sys.argv[3])
    # Create utilities object
    util_obj = Utilities()
    
    schedule.every().day.at("09:30").do(work)   # schedule 'work' at 09:30 AM local time every day
    while(True):
        schedule.run_pending()