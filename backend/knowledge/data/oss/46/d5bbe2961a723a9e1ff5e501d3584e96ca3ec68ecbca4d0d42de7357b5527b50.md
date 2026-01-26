# 知识库 46

## 标题
为何使用 Hyperlink 函数为多个工作表创建目录时提示“引用无效”？

## 问题描述
关于 Hyperlink 函数的使用，官方网站上有详细的参数说明，下面就以前一篇的目录设置为例，详细解释一下如何在同一工作簿内部各工作表间实现 Hyperlink 链接。

## 分类
主类别: 预装软件
子类别: Office软件

## 关键词
Hyperlink, 函数, 工作表, 引用无效

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
前一篇文章[如何实现 index 函数自动更新](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_1344242244805.html)介绍了如何为工作簿中的多个工作表做索引目录。在实际生活中，我们一般会进一步为各项目录加上超链接以方便跳转操作。除了逐一右击添加超链接之外，更快捷的方法是使用 Hyperlink 函数。可不少同学应用函数时，总收到报错信息，如“引用无效”。哪里出问题了呢？

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242928546_464.png)

关于 Hyperlink 函数的使用，官方网站上有[详细的参数说明](http://office.microsoft.com/zh-cn/excel-help/hyperlink-function-HP010342583.aspx)，下面小易就以前一篇的目录设置为例，详细解释一下如何在同一工作簿内部各工作表间实现 Hyperlink 链接。

在[前一篇文章](http://support1.lenovo.com.cn/lenovo/wsi/htmls/detail_1344242244805.html)中，我们了解了如何制作目录。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242928546_374.png)

我们希望实现这样一种功能：单击某个工作表名称就直接跳转到相应的工作表。

可以这么做：

1.单击 C1 单元格，输入：=HYPERLINK（"#'"&B1&"'!C2",B1）

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242928546_806.png)

这里使用了HYPERLINK（link\_location,friendly\_name）

第一个参数 Link\_location 是超链接文件的路径和文件名，或要跳转的单元格地址。特别要注意：

# 表示引用的工作表在当前工作簿中

 '"&B1&"'! 表示 B1 对应的工作表，不要漏掉任何一个符号；

 C2 表示的是 B1 对应的工作表中 C2 单元格。Hyperlink 函数必须要具体链接到工作表中的某一单元格，不过这个单元格可以任意指定。

第二个参数是随意指定的字符串或某一单元格的值，是你希望在超级链接单元格中显示的内容。为了示例清晰，我们仍调用 B1 单元格的内容。

上述参数中任一错漏都会导致报错，请一定要留心符号的输入哦。

2.完成后单击回车键，即可看到 C1 生成了淡蓝色的超链接。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242928546_327.png)

3.单击超链接跳转到相应的工作表。

然后选中 C1 单元格，将鼠标移动到右下角，变成黑色十字时往下拖动生成多行超链接。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344242928546_653.png)

这样就可以了。

来源：[微软知识库](http://support.microsoft.com/kb/2740184/zh-cn)

<!-- 文档主题：为何使用 Hyperlink 函数为多个工作表创建目录时提示“引用无效”？ (知识库库编号: 46) -->