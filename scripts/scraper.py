import time         # unconditional wait (testing)
import csv

from selenium import webdriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait   # conditional wait
from selenium.webdriver.support import expected_conditions as ec

from utils import extract_numeric, extract_coordinates

options = uc.ChromeOptions()
prefs = {
    "profile.default_content_setting_values.notifications": 2,  # Block notifications
    "translate": {"enabled": False}  # Disable translation prompt
}
options.add_experimental_option("prefs", prefs)
options.add_argument("--start-maximized")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--no-first-run --no-service-autorun --password-store=basic")

driver = uc.Chrome(options=options)

for i in range(501,552):
    all_data = []
    
    for j in range(20):
        new_line = {
            "price": None,
            "area": None,
            "n_bedrooms": None,
            "n_bathrooms": None,
            "legal": None,
            "interior": None,
            "facing_direction": None,
            "balcony_direction": None,
            "front_width": None,
            "front_road_width": None,
            "description": None,
            "latitude": None,
            "longitude": None,
            "verified": None,
            "location": None,
        }
        driver.get(f"https://batdongsan.com.vn/nha-dat-ban/p{i+1}?sortValue=8")
        print("Tried going back")

        WebDriverWait(driver, 60).until(
            ec.presence_of_element_located((By.CLASS_NAME, "re__card-info"))
        )
        print(f"item {j} in page {i+1}")
        page_result = driver.find_elements(By.CLASS_NAME, "re__card-info")[j]       # refetch results after driver.back()

        try:
            new_line["location"] = page_result.find_elements(By.CSS_SELECTOR, ".re__card-location > *")[1].text.strip()
        except Exception as e:
            new_line["location"] = None
            print(e)

        link = page_result.find_element(By.CLASS_NAME, "re__card-title")
        link.click()
        time.sleep(1)

        info_fields = driver.find_elements(By.CLASS_NAME, "re__pr-specs-content-item")
        for field in info_fields:
            i_type = field.find_element(By.CLASS_NAME, "re__pr-specs-content-item-title").text.strip()
            i_val = field.find_element(By.CLASS_NAME, "re__pr-specs-content-item-value").text.strip()
            match i_type:
                case "Khoảng giá":
                    new_line["price"] = i_val
                case "Diện tích":
                    new_line["area"] = i_val
                case "Số phòng ngủ":
                    new_line["n_bedrooms"] = i_val
                case "Số phòng tắm, vệ sinh":
                    new_line["n_bathrooms"] = i_val
                case "Pháp lý":
                    new_line["legal"] = i_val
                case "Nội thất":
                    new_line["interior"] = i_val
                case "Hướng nhà":                           # phong thủy đồ nè
                    new_line["facing_direction"] = i_val
                case "Hướng ban công":                      # view đồ nè
                    new_line["balcony_direction"] = i_val
                case "Mặt tiền":                            # bao nhiêu mét giáp mặt đường
                    new_line["front_width"] = i_val
                case "Đường vào":                           # Đường trước nhà rộng nhiêu? lớn khum?
                    new_line["front_road_width"] = i_val
        
        # get verification status
        try:
            driver.find_element(By.CLASS_NAME, "re__pr-stick-listing-verified")
        except:
            new_line["verified"] = 0
        else:
            new_line["verified"] = 1


        # find coordinates of the place -> location analysis
        for _ in range(7):
            try:
                map = driver.find_element(
                    By.CSS_SELECTOR, 
                    ".re__section.re__pr-map.js__section.js__li-other .re__section-body.js__section-body"
                )
                embed_map_link = map.find_element(By.TAG_NAME, "iframe").get_attribute("data-src")
                new_line["latitude"], new_line["longitude"] = extract_coordinates(embed_map_link)
                break
            except:
                driver.execute_script("window.scrollBy(0, 550);")
                time.sleep(0.2)

        # get description of post
        new_line["description"] = driver.find_element(
            By.CLASS_NAME, 
            "re__section-body.re__detail-content.js__section-body.js__pr-description.js__tracking"
        ).text

        all_data.append(new_line)
        print({k:v for k,v in new_line.items() if k != "description"})

    # write result after scraping a full page
    mode = "w" if i == 0 else "a"
    with open("data/raw/batdongsan_com_vn.csv", mode, encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, new_line.keys())
        if mode == "w":
            writer.writeheader()
        writer.writerows(all_data)

    print(f"page {i+1} scraped successfully")

driver.quit()