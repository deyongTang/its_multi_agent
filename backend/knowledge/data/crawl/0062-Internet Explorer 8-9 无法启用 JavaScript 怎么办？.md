# 知识库 62

## 标题
Internet Explorer 8/9 无法启用 JavaScript 怎么办？

## 问题描述
在浏览网页中可能会遇到插件无法运行，提示脚本错误等问题，此现象可能是由于JavaScript 没有启用引起的，下文将针对该问题给出解决方案。

## 分类
主类别: 操作系统故障
子类别: 浏览器

## 关键词
浏览器, IE, JavaScript, 插件

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**故障现象：**

在 Internet Expllorer 8/9 中，有些同学在浏览网页时，收到提示：“需要启用 JavaScript …”，并且会发现网页上某些功能不能用了，比如点击网页里的按钮没反应等等。

**解决方案：**

1、单击 **开始** 按钮，按一下 **运行** 按钮，打开 **运行** 对话框（或者按 Windows 徽标键 + R 打开也可），输入 regsvr32 jscript.dll 后，点击 **确定**，重新注册 jscript.dll 来修复 JavaScript；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120906/1346915679496_406.png)

2、看到注册成功的对话框，点击 **确定；**

![](https://webdoc.lenovo.com.cn/lenovowsi/20120906/1346915679496_135.png)

3、打开 Internet Explorer 浏览器，按一下“**工具**”按钮，再单击“**Internet 选项**”；

Internet Explorer 9 用户请看：

![](https://webdoc.lenovo.com.cn/lenovowsi/20120906/1346915679496_713.png)

Internet Explorer 8 用户请看：

![](https://webdoc.lenovo.com.cn/lenovowsi/20120906/1346915679496_59.png)

4、在 安全 选项卡下面的 **该区域下的安全级别** 部分单击 **自定义级别**，打开 **安全设置** 窗口；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120906/1346915679496_868.png)

5、在 **安全设置** 窗口中，确认 **Java 小程序脚本** 和 **活动脚本** 是否已经启用，如果没，请选择 **启动**，然后点击 **确定**。这时候 JavaScript 已经启用，Internet Explorer 恢复正常；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120906/1346915679496_716.png)

来源：[微软知识库](http://support.microsoft.com/kb/2749601/zh-cn)

<!-- 文档主题：Internet Explorer 8/9 无法启用 JavaScript 怎么办？ (知识库库编号: 62) -->