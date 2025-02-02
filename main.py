PIXIV_ID = 103160614 #爬取用户ID
HIDE_WONDOW_LOHON_GETID = False #登入和收藏页面的浏览器窗口是否显示
HIDE_WONDOW_GET_INFORMATION = True #获取图片信息时的浏览器窗口是否显示
GET_INFORMATION_MAXTHREADS = 8 #同时获取图片信息的最大线程
REPEAT_JSON_REPLACEMENT = True #已存在的JSON是否替换 False表示存在就跳过执行

AUTOMATIC_LOGIN_SWITCH = False #是否开启自动登入（不推荐开启，一般不会通过人机验证）
AUTOMATIC_LOGIN_USERNAME = "Username"#用户名
AUTOMATIC_LOGIN_PASSWORD = "Password"#密码


# ----------------------------------------------------------------------------------------------------------------
import os
import time
import json
import sys
import pickle
import re
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def URL_extract_image_id(url):
    # 使用正则表达式提取 ID 部分
    match = re.search(r'https://www\.pixiv\.net/artworks/(\d+)', url)
    if match:
        return match.group(1)  # 返回提取到的 ID
    else:
        return None  # 如果没有匹配到，返回 None
#URL获取ID
def ID_Get_Images(url,cookies_file,hide_window):
    if REPEAT_JSON_REPLACEMENT == True:
        if os.path.exists(f"./json_data/{URL_extract_image_id(url)}.json ") ==True:
            print(f"JSON已存在,跳过执行 {url}")
            return


        # 设置 ChromeDriver 路径和浏览器选项
    chrome_options = Options()

    if hide_window == True:
        chrome_options.add_argument("--headless")  # 不显示浏览器窗口
    #chrome_options.add_argument("--disable-gpu")  # 禁用 GPU 加速

    # 启动 WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # 访问登录页面
    driver.get("https://accounts.pixiv.net/login")
    # 如果 cookies 文件存在，加载 cookies
    try:
        # 删除现有的 cookies，确保域名一致
        driver.delete_all_cookies()
        cookies = pickle.load(open(cookies_file, "rb"))
        for cookie in cookies:
            # 调整 domain 属性为当前页面的域名
            if "domain" in cookie:
                cookie["domain"] = ".pixiv.net"  # 或者使用 `driver.current_url` 动态解析域名
            driver.add_cookie(cookie)
        print(f"已加载 Cookie {url}")
        driver.refresh()  # 刷新页面以加载保存的 cookies
    except Exception as e:
        print(f"加载 cookie {url} 出错: {e}")


    # 目标 URL
    print(f"正在保存页面 {url}")
    # 打开页面
    driver.get(url)

    WebDriverWait(driver, 30).until(
        lambda driver: driver.execute_script("return document.readyState") == "complete"
    )

    # 获取页面源码
    page_source = driver.page_source
    print(f"解析页面源码 {url}")
    # 使用 BeautifulSoup 解析页面源码
    soup = BeautifulSoup(page_source, 'html.parser')

    # 获取图片的原始 URL
    image_url_tag = soup.find('img', class_='sc-1qpw8k9-1 eMdOSW')  # 这个 class 可能会变
    if image_url_tag:
        image_url = image_url_tag['src']
    else:
        image_url = None

    # 获取作者名字
    author_tag = soup.find('div', class_='sc-10gpz4q-5 fJniwh')  # 更新此处
    if author_tag:
        author_name = author_tag.get_text(strip=True)
    else:
        author_name = 'Unknown'

    # 获取图片的标签
    tags = []
    tag_elements = soup.find_all('a', class_='sc-d98f2c-0 gtm-new-work-tag-event-click')
    for tag in tag_elements:
        tags.append(tag.text.strip())

    # 获取上传时间
    upload_time = soup.find('time')['datetime']

    # 计算图片的宽高比例
    img_tag = soup.find('img', class_='sc-1qpw8k9-1 eMdOSW')
    if img_tag:
        width = int(img_tag['width'])
        height = int(img_tag['height'])
        ratio = f"{width}*{height}"
    else:
        ratio = None

    # 判断是否为 R18 内容
    r18 = 'R-18' in page_source

    # 提取图片 ID 从 URL 中（假设 URL 是 https://www.pixiv.net/artworks/114871667）
    image_id = url.split('/')[-1]  # 获取 URL 中的最后一部分作为 ID

    # 创建文件夹，如果不存在的话
    output_dir = 'json_data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 保存为图片 ID 的 JSON 文件
    json_file_path = os.path.join(output_dir, f"{image_id}.json")

    # 构造 JSON 数据
    image_data = {
        "image_url": image_url,
        "author_name": author_name,
        "tags": tags,
        "ratio": ratio,
        "r18": r18,
        "upload_time": upload_time
    }

    # 将数据保存为 JSON 文件
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(image_data, json_file, ensure_ascii=False, indent=4)

    # 关闭 WebDriver
    driver.quit()

    print(f"数据已成功保存为 {json_file_path}！")
#获取图片信息
def update_progress(i, total):
    print(f"处理进度：{i}/{total}")
#处理进度
def merge_json_files(folder_path, output_path):
    # 获取文件夹中所有的 .json 文件
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

    merged_data = []  # 存储合并后的数据

    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)

        # 打开并读取每个 JSON 文件的内容
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):  # 确保读取到的数据是列表
                merged_data.extend(data)  # 合并到一个大的列表中
            else:
                merged_data.append(data)  # 如果是单个字典，直接添加

    # 将合并后的数据保存到输出文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)
#多个json合成一个json

if __name__ == '__main__':
    print("程序开始运行")
    # 配置Chrome选项
    options = Options()
    if HIDE_WONDOW_LOHON_GETID==True:
        options.add_argument("--headless")

    # 设置Selenium WebDriver，自动下载ChromeDriver
    service = Service(ChromeDriverManager().install())

    # 创建WebDriver实例
    driver = webdriver.Chrome(service=service, options=options)

    # 设置保存的 cookies 文件路径
    cookies_file = "pixiv_cookies.pkl"

    # 访问登录页面
    driver.get("https://accounts.pixiv.net/login")

    # 如果 cookies 文件存在，加载 cookies
    try:
        # 删除现有的 cookies，确保域名一致
        driver.delete_all_cookies()
        cookies = pickle.load(open(cookies_file, "rb"))
        for cookie in cookies:
            # 调整 domain 属性为当前页面的域名
            if "domain" in cookie:
                cookie["domain"] = ".pixiv.net"  # 或者使用 `driver.current_url` 动态解析域名
            driver.add_cookie(cookie)
        print("已加载 Cookie。")
        time.sleep(2)
        driver.refresh()  # 刷新页面以加载保存的 cookies

    except Exception as e:
        print(f"加载 cookie 出错: {e}")

    # 检查是否已经登录
    if driver.current_url == "https://accounts.pixiv.net/login":
        print("请登入...")
        if AUTOMATIC_LOGIN_SWITCH == True :
            # 填写用户名和密码
            username = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="邮箱地址或pixiv ID"]')
            password = driver.find_element(By.CSS_SELECTOR, 'input[placeholder="密码"]')

            # 输入用户名和密码
            username.send_keys(AUTOMATIC_LOGIN_USERNAME)
            password.send_keys(AUTOMATIC_LOGIN_PASSWORD)

            # 提交表单
            password.submit()

            WebDriverWait(driver, 30).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        else:
            # 等待登录完成
            input("等待登入完成，按回车键继续...")  # 阻塞脚本，等待用户按下回车

        # 保存 cookies
        pickle.dump(driver.get_cookies(), open(cookies_file, "wb"))
        print("Cookies 已保存。")

    # 登录后等待页面加载
    WebDriverWait(driver, 10).until(EC.url_changes('https://accounts.pixiv.net/login'))  # 等待 URL 改变

    image_ids = []
    p=0
    while True:
        # 加载Pixiv页面，获取某个作品的页面
        p=p+1
        driver.get(f'https://www.pixiv.net/users/{PIXIV_ID}/bookmarks/artworks?p={p}')# 收藏主页

        #等待页面加载
        WebDriverWait(driver, 30).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        time.sleep(1)  # 延时 1 秒

        if driver.current_url != f'https://www.pixiv.net/users/{PIXIV_ID}/bookmarks/artworks?p={p}':
            break  # 退出循环

        # 获取页面的HTML内容
        html = driver.page_source

        # 解析HTML
        soup = BeautifulSoup(html, 'html.parser')

        # 查找所有包含图片ID的链接
        artworks = soup.find_all('a', href=True)

        # 提取所有的图片ID
        image_id = 0
        for artwork in artworks:
            href = artwork['href']
            if '/artworks/' in href:
                image_id = href.split('/artworks/')[1]  # 提取图片ID
                print("爬取ID:"+image_id)
                image_ids.append(image_id)



    # 删除重复的图片ID
    image_ids = list(set(image_ids))
    # 删除包含指定字符的成员
    image_ids = [item for item in image_ids if "%" not in item]

    #输出全部ID
    print(f"共有{len(image_ids)}个ID。")
    print("爬取到的全部ID:")
    print(image_ids)

    # 关闭浏览器
    driver.quit()

    # 使用 ThreadPoolExecutor 并发处理 URL 列表中的所有任务
    i = 0
    with ThreadPoolExecutor(max_workers=GET_INFORMATION_MAXTHREADS) as executor:
        # executor.map 会并行调用 ID_Get_Images
        for _ in executor.map(
                ID_Get_Images,
                ['https://www.pixiv.net/artworks/' + image_id for image_id in image_ids],
                ["pixiv_cookies.pkl"] * len(image_ids),
                [HIDE_WONDOW_GET_INFORMATION] * len(image_ids)
        ):
            i += 1
            update_progress(i, len(image_ids))

    print("合并json")
    merge_json_files("./json_data","./merged.json")
    sys.exit(0)
