# 知识库 579

## 标题
Win7系统下如何修改hosts文件？

## 问题描述
Win7系统下修改hosts文件的方法。

## 分类
主类别: 操作系统故障
子类别: 系统应用操作

## 关键词
Win7, 修改, hosts, 保存

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
Hosts是一个没有扩展名的[系统文件](/detail/kd_17533.html)，可以用记事本等工具打开，其作用就是将一些常用的网址[域名](/detail/kd_17481.html)与其对应的[IP](/detail/kd_17443.html)地址建立一个关联“[数据库](/detail/kd_17734.html)”，当用户在[浏览器](/detail/kd_17581.html)中输入一个需要登录的网址时，系统会首先自动从Hosts文件中寻找对应的IP地址，一旦找到，系统会立即打开对应网页，如果没有找到，则系统再会将网址提交[DNS](/detail/kd_17386.html)域名解析[服务器](/detail/kd_17589.html)进行IP地址的解析。

[host](/detail/kd_17528.html)s文件在不同操作系统（甚至不同Windows版本）的位置都不大一样，因为除了[Win7](/detail/kd_17983.html)之外的系统已经很少使用了，所以在此只介绍Win7中修改[hosts文件](/detail/kd_18040.html)的方法。

1、打开[C盘](/detail/kd_17454.html)中的系统目录[Windows 7](/detail/kd_17984.html)系统，文件路径为..WindowsSystem3[2D](/detail/kd_17682.html)riversetc，找到hosts文件并点击打开；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447832648548_317.jpg)

2、在出现的弹出窗口中选择打开方式，一般记事本等文本工具就可以打开；

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447832648548_87.jpg)

3、根据文件中原有的示例添加自己想要解析的网址。添加的格式正如localhost本机地址127.0.0.1       localhost一样，先输入需要解析的IP地址，空格后输入对应的域名，注意中间的空格最好使用Tab键来输入，即美观又不容易编写失误。

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447832648548_596.jpg)

4、这里我将以百度的IP进行示范，百度的IP地址是202.108.22.5，我输入的对应的名称是love。保存完成后只要在浏览器的地址栏中输入love，系统会自动解析为百度的IP地址并进行连接。

![](https://webdoc.lenovo.com.cn/lenovowsi/20151118/1447832648548_5.jpg)

5、编辑完成后点击关闭并保存。如果想使某一行失效或注销某一行，只需要在这一行的前面添加“#”号即可。

<!-- 文档主题：Win7系统下如何修改hosts文件？ (知识库库编号: 579) -->