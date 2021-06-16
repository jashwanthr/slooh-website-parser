from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime
import time
import logging
import os
import json
import re
import getpass

username = getpass.getuser()

class SloohWebsiteParser():
    """Class that contains methods to handle https://slooh.com/ parsing using selenium"""

    def __init__(self, email, password, chrome_driver_path):
        """Initialize required variables"""        
        # code to setup logging obj
        self.logger = logging.getLogger("SloohWebsiteParser")
        self.logger.setLevel(level=logging.DEBUG)
        for hdlr in self.logger.handlers[:]:    # remove all old handlers
            self.logger.removeHandler(hdlr)
        
        # create and add file handler to logging obj
        fileh = logging.FileHandler('SloohWebsiteParser.log')
        formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s",
                                      "%Y-%m-%d %H:%M:%S")     # set format of the logs
        fileh.setFormatter(formatter)
        self.logger.addHandler(fileh)

        # create selenium driver obj
        self.driver = webdriver.Chrome(executable_path = chrome_driver_path)
        
        # set required variables
        self.login_url = "https://slooh.com/guestDashboard"
        self.new_dashboard_url = "https://slooh.com/newDashboard"
        self.is_logged_in = False
        self.email = email
        self.password = password
        self.DEFAULT_DRIVER_SLEEP = 0.5

    def login(self):
        """Try to login into slooh website. Return True if login is successful, False otherwise."""
        # if already logged in, return True
        if(self.is_logged_in):
            return True
        # else if not already logged in, try to login
        try:
            #load slooh website
            self.logger.debug("Trying to load slooh")
            self.driver.get(self.login_url)
            time.sleep(12)

            
            #click sign-in btn
            self.driver.find_elements_by_class_name("button-list")[1].click()
            time.sleep(1)

            #login
            self.logger.debug("Trying to login to slooh")
            self.driver.find_element_by_name("username").send_keys(self.email)
            self.driver.find_element_by_name("pwd").send_keys(self.password)
            self.driver.find_elements_by_xpath("//form//button")[0].click()
            time.sleep(15)
            
            # profile-card is found, return True as login is successful
            if(self.driver.find_element_by_class_name("profile-card-main")):
                self.logger.debug("Login success")
                self.is_logged_in = True
                return True
            # else if profile-card is not found, raise exception as login is failed
            else:
                self.logger.debug("Could not locate profile card")
                raise Exception("Could not locate profile card")
        except Exception as err:
            self.logger.debug(f"Login failed - {str(err)}")
            return False

    def logout(self):
        """Try to logout from slooh website. Return True if logout is successful, False otherwise."""
        try:
            if(self.is_logged_in):
                # load homepage
                self.logger.debug("Trying to logout")
                self.driver.get(self.new_dashboard_url)
                time.sleep(12)
                
                # click on right-menu 
                right_menu_btns = self.driver.find_element_by_class_name("right-menu").find_elements_by_tag_name("button")
                right_menu_btns[-1].click()
                time.sleep(self.DEFAULT_DRIVER_SLEEP)
                
                # click on logout
                menu_items = self.driver.find_element_by_class_name("open").find_elements_by_class_name("primary-button")
                menu_items[-1].click()
                
                # TODO : Validate logout
                self.logger.debug("Logout successful")
                return True
            else:
                self.logger.debug("Unable to logout. User not logged in yet.")
                return True
        except Exception as err:
            self.logger.debug(f"Logout failed - {str(err)}")
            return False
        
    def search_parser(self):
        """Parses object info from search option in website. 
        Return boolean indicating whether parsing is successful or not."""
        json_object_info_filepath = 'slooh_object_info.json'
        try:
            # load homepage
            self.logger.debug("Trying to extract object info from search option")
            self.driver.get(self.new_dashboard_url)
            time.sleep(12)
            
            # click on search icon
            self.driver.find_element_by_class_name("icon-search").click()
            time.sleep(3)
            
            json_data = {}
            object_infos_modified = 0
            object_infos_added = 0
            # load existing json data
            if os.path.exists(json_object_info_filepath):
                with open(json_object_info_filepath, 'r') as f:
                    json_data = json.load(f)
            
            # extract grand-parents in search window
            grandparents = self.driver.find_elements_by_class_name("search-results-grandparent")    
            grandparents_len = len(grandparents)
            for i in range(grandparents_len):
                elem = self.driver.find_elements_by_class_name("search-results-grandparent")[i]
                grandparent_name = elem.text.strip()
                # expand current grand-parent
                elem.find_element_by_class_name("icon-plus").click()
                # expand parents under current grand-parent                               
                parents = self.driver.find_elements_by_class_name("search-results-parent")          
                parents_len = len(parents)
                for j in range(parents_len):
                    # log debug info once for every 10 parent processing is done
                    if(j % 10 == 0):
                        self.logger.debug("Currently extracting grand-parent - " + str(i) + "/" + str(grandparents_len) + ", " +
                                            "parent - " + str(j) + "/" + str(parents_len))
                    try:
                        # scroll to current parent
                        self.driver.execute_script("arguments[0].scrollIntoView();", self.driver.find_elements_by_class_name("search-results-parent")[j])
                        time.sleep(self.DEFAULT_DRIVER_SLEEP // 2)
                        if "icon-plus" in self.driver.find_elements_by_class_name("search-results-parent")[j].get_attribute("innerHTML"):                
                            elem = self.driver.find_elements_by_class_name("search-results-parent")[j]
                            parent_name = elem.text.strip()
                            # expand items under current parent
                            elem.find_element_by_class_name("icon-plus").click()                    
                            items = self.driver.find_elements_by_class_name("search-results-item")
                            # for each item in items under cirrent parent
                            for item in items:
                                # scroll to current item
                                self.driver.execute_script("arguments[0].scrollIntoView();", item)
                                time.sleep(self.DEFAULT_DRIVER_SLEEP // 2)
                                # extract object name
                                object_name = item.text.strip()
                                # if object name already exists in json data
                                if object_name in json_data:
                                    is_object_modified = False
                                    # if current parent name is not present in the object info
                                    if parent_name not in json_data[object_name]["parent"]:
                                        # add parent name in object info
                                        json_data[object_name]["parent"].append(parent_name)        
                                        is_object_modified = True
                                    # if current grand-parent name is not present in the object info
                                    if grandparent_name not in json_data[object_name]["grandparent"]:
                                        # add grand-parent name in object info
                                        json_data[object_name]["grandparent"].append(grandparent_name)  
                                        is_object_modified = True
                                    # if parent/grandparent has been modified above, increment 'is_object_modified' counter
                                    if(is_object_modified):
                                        object_infos_modified += 1
                                # else if object name does not exist in json data
                                else:
                                    # add new object to the json data along with object info
                                    object_url = item.find_element_by_tag_name('a').get_attribute('href')
                                    json_data[object_name] = {
                                        "object_url": object_url,
                                        "parent": [parent_name],
                                        "grandparent": [grandparent_name],
                                    }
                                    # Increment 'object_infos_added' counter
                                    object_infos_added += 1
                            # minimize current parent
                            self.driver.find_elements_by_class_name("search-results-parent")[j].find_element_by_class_name("icon-minus").click()
                    except Exception as err:
                        self.logger.debug(f"Unable to extract object info for grand-parent - {str(i)} & parent - {str(j)} : - {str(err)}")
                # minimize current grand-parent        
                self.driver.find_elements_by_class_name("search-results-grandparent")[i].find_element_by_class_name("icon-minus").click()
            
            # save updted json data to file
            with open(json_object_info_filepath, 'w') as f:
                json.dump(json_data, f, indent = 4)
            self.logger.debug(f"Object extraction complete. {str(object_infos_added)} new objects found. {str(object_infos_modified)} objects modified.")
            return True
        except Exception as err:
            self.logger.debug(f"Object extraction failed - {str(err)}")
            return False
            
    def photo_roll_parser(self):
        """Parses photos info from photo roll page. 
        Returns boolean indicating whether parsing is successful or not."""
        # if login is successful, proceed to parse photo roll
        if(self.login()):
            try:
                # load phot roll page
                self.logger.debug("Trying to parse photo roll")
                self.driver.get("https://slooh.com/my-pictures/photo-roll")
                time.sleep(30)
                
                # extract next btn element
                next_elem = self.driver.find_element_by_class_name("next")
                page = 1
                retry_count = 0
                
                # open output file for writing
                f = open('photo_roll_info.txt', 'a')
                while "active" in next_elem.get_attribute('class'):
                    try:
                        # log current page info once every 20 pages
                        if(page % 20 == 1):
                            self.logger.debug("Parsing page - " + str(page))
                        
                        # write raw photos info from current page in html format to the output file
                        f.write(self.driver.find_elements_by_class_name("undefined")[-1].get_attribute("innerHTML") + '\n')
                        time.sleep(self.DEFAULT_DRIVER_SLEEP)
                        
                        # go to next page
                        next_elem.click()
                        time.sleep(self.DEFAULT_DRIVER_SLEEP * 8)
                        # extract next btn element from next page
                        next_elem = self.driver.find_element_by_class_name("next")
                        page += 1
                    except:
                        # if more than 5 excpetions occur during photo roll parsing, raise an excpetion and abort
                        if(retry_count == 5):
                            raise Exception("Photo roll parsing failed even after 5 tries!!")
                        # else, increment retry count and wait for 30s before trying again
                        retry_count += 1
                        self.logger.debug("Excpetion during photo roll parsing. Retrying again.. (Retry count - " + str(retry_count) + ").")
                        time.sleep(30)
                        # currently assuming next element always appears after 30s wait.. need to handle scenario (albeit rare) where it doesn't appear
                        next_elem = self.driver.find_element_by_class_name("next")
                        page += 1
                self.logger.debug("Photo roll parsing complete.")
                return True
            except Exception as err:
                self.logger.debug(f"Photo roll parsing failed - {str(err)}")
                return False
            # close the output file finally
            finally:
                f.close()
        # else if login fails, return False
        else:
            self.logger.debug("Not logged in before parsing photo roll.")
            return False
    
    def reserve_mission_using_object_url(self, object_url):
        """Parses photos info from photo roll page. 
        Returns boolean indicating whether parsing is successful or not."""
        # if login is successful, proceed to reseve mission using given object url
        if(self.login()):
            # load mission page using given object url
            self.logger.debug(f"Trying to book mission using {object_url}")
            mission_url = object_url + "/missions"
            active_missions = 0
            self.driver.get(mission_url)
            time.sleep(30)
            
            # if no redirects happen i.e. mission url is loaded successfully
            if(self.driver.current_url == mission_url):
                # extract active missions
                active_missions_text = self.driver.find_element_by_class_name("title-bg").find_element_by_tag_name('h2').text
                active_missions = int(re.search('\d+', active_missions_text).group())
                # if active missions are 5 or more, return 'False' (mission booking failed) and active missions count
                if(active_missions >= 5):
                    return False, active_missions
                
                # if active missions are less than five, proceed to book mission
                try:
                    # extract divs corresponding to all avaialbel missions
                    missions_available = self.driver.find_elements_by_class_name("mission-card-container")
                    mission_to_choose = max_altitude =  0
                    # try to extract missions where object altitude is at the highest
                    try:
                        for mission in range(len(missions_available)):
                            mission_descs = missions_available[mission].find_elements_by_class_name("details-text")
                            for desc in mission_descs:
                                desc_text = desc.text
                                if "Altitude" in desc_text:
                                    object_altitude = int(re.search(r'\d+', desc_text))
                                    if object_altitude > max_altitude:
                                        max_altitude = object_altitude
                                        mission_to_choose = mission
                    # if mission where object altitude is maximum could not be found, choose first available mission
                    except Exception as err:
                        mission_to_choose = 0
                        self.logger.debug(f"Unable to extract object altitudes - {str(err)}. Choosing first available mission.")
                    
                    # reserve the above selected mission for given object
                    missions_available[mission_to_choose].find_element_by_tag_name("button").click()
                    time.sleep(10)
                    self.driver.find_element_by_class_name("featured-objects-modal").find_element_by_tag_name("button").click()
                    time.sleep(10)
                    # if mission booking is not successfult, return False (mission booking failed) and active missions count
                    if "Congratulations" not in self.driver.find_element_by_class_name("my-5").text:
                        return False, active_missions
                    else:
                        self.logger.debug(f"Mission booked successfully for object url - {object_url}.")
                except:
                    return False, active_missions
            # if mission url is not loaded correctly, return False (mission booking failed) and active missions count using 'get_active_missions'
            else:
                return False, self.get_active_missions_count()

            # Assume everything went well and return True (mission booking successfult) and active missions count incremented by 1
            return True, active_missions + 1
        # else if login fails, return False (mission boooking failed) and -1 (active missions count)
        else:
            self.logger.debug("Not logged in before trying to book mission.")
            return False, -1
        
    def get_active_missions_count(self):
        # if login is successful, proceed to extract active missions count
        if(self.login()):
            try:
                # load slooh1000 page where active missions count is available
                self.driver.get("https://slooh.com/missions/bySlooh1000")
                time.sleep(10)
                
                # extract and return active missions count
                mission_quota = self.driver.find_element_by_class_name("mission-quota-text").text
                return int(re.search('\d+', mission_quota).group())
            # if active missions count extraction fails, return max allowed active missions
            except Exception as err:
                self.logger.debug(f"Error while trying to get active missions - {str(err)}")
                return 5
        # else if login is not successful, return max allowed active missions
        else:
            self.logger.debug("Not logged in before trying to get active missions.")
            return 5