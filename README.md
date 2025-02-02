
# Pixiv_Crawler
通过pixiv去爬取指定账号ID的收藏，并且通过分类储存到Json中。

此项目用于返回随机的图片
https://github.com/MiaoluoYuanlina/API_Random_Pictures

填写爬取的账号ID 根据url填写 https://www.pixiv.net/users/103160614

    PIXIV_ID = 103160614 #爬取用户ID

    HIDE_WONDOW_LOHON_GETID = False #登入和收藏页面的浏览器窗口是否显示  

    HIDE_WONDOW_GET_INFORMATION = True #获取图片信息时的浏览器窗口是否显示 

    GET_INFORMATION_MAXTHREADS = 8 #同时获取图片信息的最大线程  

    REPEAT_JSON_REPLACEMENT = True #已存在的JSON是否替换 False表示存在就跳过执行 

    AUTOMATIC_LOGIN_SWITCH = False #是否开启自动登入（不推荐开启，一般不会通过人机验证）

    AUTOMATIC_LOGIN_USERNAME = "Username"#用户名  

    AUTOMATIC_LOGIN_PASSWORD = "Password"#密码
