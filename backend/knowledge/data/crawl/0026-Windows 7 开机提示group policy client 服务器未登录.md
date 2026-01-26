# 知识库 26

## 标题
Windows 7 开机提示group policy client 服务器未登录

## 问题描述
由于服务被禁用引起登录 Windows 7 时，提示 Group Policy Client 服务未能登录。拒绝访问。下文将指导修复该问题的方法。

## 分类
主类别: 操作系统故障
子类别: 系统登录问题

## 关键词
Windows 7, group policy client, 服务器未登录, 开机报错

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
**故障现象：**  
登录 Windows 7 时，提示 Group Policy Client 服务未能登录。拒绝访问。

**解决方案：**

在开机或者重启计算机时，不停点击F8按钮，弹出“**高级启动选项**”窗口后，使用键盘上的上下方向箭头移动白色高亮条选中“**安全模式**”，然后按回车键；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_57.png)

登录出问题的用户账户，记录下用户名，我们下面会使用到；（例如: ekbtest）

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_897.png)

附：如果无法进入安全模式，也许该试试一键恢复或者使用修复光盘修复操作系统。

**提醒：修改注册表有风险，请提前备份数据并在专业人士提醒下慎重操作。**

进入安全模式后，打开“**开始-运行**”，键入命令 **regedit.exe**，然后按回车键打开“**注册表编辑器**”；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_192.png)

在注册表编辑器中，找到 **HKEY\_CURRENT\_USER**，右击选择“**权限**”；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_430.png)

弹出权限对话窗后，单击“**添加**”按钮；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_74.png)

在“**对象名称**”一栏输入刚才记录的用户名，点击确定；

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_707.png)

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_461.png)

回到权限窗口，现在“**组或用户名**”中会多出一个用户 ekbtest，并且默认处于选中状态。单击勾选权限栏“**完全控制**”后面的复选框，然后按“**确定**”保存设置。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_916.png)

类似地，我们再添加一个名为“**system**”的用户，并设置完全控制权限。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120711/1341994378781_871.png)

然后退出注册表编辑器，重启计算机。

来源：[微软知识库](http://support.microsoft.com/kb/2724610/zh-cn)

<!-- 文档主题：Windows 7 开机提示group policy client 服务器未登录 (知识库库编号: 26) -->