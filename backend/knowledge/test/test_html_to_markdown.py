from markdownify import markdownify as md
import  re
# 1. HTML 内容
# 这是从知识库网页上爬取下来的内容片段

origin_html_content="""
<html>\n <head></head>\n <body>\n  <p><strong>解决方案</strong><strong>：</strong></p>\n  <p>&nbsp;</p>\n  <p>利用软碟通软件（UltraISO）实现</p>\n  <p>&nbsp;</p>\n  <p>一、双击软碟通软件UltraISO，选择“文件”---“打开”找到Windows 7操作系统的光盘镜像ISO文件，单</p>\n  <p>击“启动光盘”---“写入硬盘映像”；</p>\n  <p>&nbsp;</p>\n  <p><img src=\"https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20160128/1453944749628319.jpg\" alt=\"\"></p>\n  <p><br>二、点击“写入”将镜像文件写入U盘，注意在“硬盘驱动器”列表谨慎选择磁盘，如下图所示：</p>\n  <p>&nbsp;</p>\n  <p><img title=\"1622802922519206.png\" src=\"https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20210604/1622802922519206.png\" alt=\"w0002如何使用U盘安装Windows 7操作系统第2张图.png\"></p>\n  <p>&nbsp;</p>\n  <p>&nbsp;</p>\n  <p>&nbsp;</p>\n  <p><strong>注意事项：</strong>此操作会格式化所选择的U盘，操作一定谨慎！</p>\n  <p>&nbsp;</p>\n  <p>此方法同时适用Windows Vista、Windows Server2008及Windows Server2008R2各版本。</p>\n  <ul style=\"padding: 10px 0px; width: 94%;\">\n   <li class=\"mceNonEditable require_0x2ae48d04\" style=\"list-style: none; max-height: 400px; overflow-y: auto;\" contenteditable=\"false\"><p><img src=\"https://chinakb.lenovo.com.cn/ueditor/php/upload/image/20190523/1558590983697581.png\" width=\"30\" height=\"21\"><span style=\"font-size: 16px;\">安装或升级系统太麻烦？没有时间？<a href=\"https://item.lenovo.com.cn/product/1000630.html?pmf_group=23as&amp;pmf_medium=23as&amp;pmf_source=Z00005044T000\"><span style=\"text-decoration: underline; color: blue;\">联想专家一对一重装系统服务</span></a>，通过远程的方式重装系统，让电脑重新恢复活力，速度更快；清除电脑存在的潜在威胁，让您的数据更安全！</span></p></li>\n  </ul>\n </body>\n</html>
"""

print(origin_html_content)


# # # 2. 调用 md()
# markdown_content = md(origin_html_content)
#
# print(markdown_content)

