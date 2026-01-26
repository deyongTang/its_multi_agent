from bs4 import BeautifulSoup
"""
解析网页： 它可以将下载下来的 HTML 源代码（即使是格式混乱、标签闭合不全”）解析成一个标准的树状结构。

"""
# 模拟一段脏 HTML (包含脚本、内联样式、以及你不想要的广告块)
dirty_html = """
<html>
 <head><title>示例页面</title></head>
<body>
    <h1>万全T168服务器故障分析</h1>
    <a href="http://example.com/one" id="link1">第一个链接</a>
   
    <script>console.log("tracking code");</script>
    <style>.red { color: red; }</style>

    <p>服务器开机有类似救护车的报警声。</p>

    <div class="content-body">
        <p>可能原因：1. 内存松动；2. 主板故障。</p>
        <img src="error.jpg" alt="报错图片">
    </div>

    <ul class="mceNonEditable">
        <li>
            <img src="ad.png">
            <span>联想专家一对一重装系统服务...广告内容...</span>
        </li>
    </ul>

    <br><br><br> </body>
</html>
"""


def clean_html_with_bs4(html_content):
    # 1. 创建 Soup 对象 (解析器推荐用 html.parser)
    soup = BeautifulSoup(html_content, 'html.parser')
    print("--- 原始结构中包含广告和脚本 ---")

    # 1. 查找title标签的属性
    print(soup.title.text)

    # 2. 查找特定标签的属性
    link = soup.find('a')
    print(link['href'])

    # 3. 移除所有的 script 和 style 标签
    for tag in soup(["script", "style"]):
        tag.decompose()

    # 4. 移除特定的广告类 (根据你的 JSON 数据)
    # select() 使用 CSS 选择器，非常灵活
    for ad in soup.select('.mceNonEditable'):
        ad.decompose()

    # 4. 输出清洗后的 HTML 字符串
    return str(soup)


# --- 运行测试 ---
cleaned = clean_html_with_bs4(dirty_html)

print("\n--- 清洗后的 HTML (准备交给 markdownify) ---")
print(cleaned)