# 知识库 39

## 标题
Internet Explorer版本升级说明

## 问题描述
本文向您介绍 Windows 操作系统与 Internet Explorer（以下简称 IE）浏览器的版本升级对应关系。您可以通过本文了解您的 Windows 支持哪些版本的 IE 浏览器，并了解为您的 Windows 升级或卸载 IE 浏览器的技巧。

## 分类
主类别: 操作系统故障
子类别: 浏览器

## 关键词
ie, 升级, Internet Explorer, 浏览器

## 元信息
创建时间:2024-12-15|版本:1.0

## 解决方案
Windows 集成的 IE 浏览器版本与可升级的 IE 浏览器版本

IE 浏览器作为 Windows 操作系统的一个组成部分，每一个版本的 Windows 都自带有一个集成的默认版本 IE。集成的默认版本 IE 无法单独卸载或单独重新安装，也无法降级为比这个默认的版本更低的 IE 版本。

每一个版本的 Windows 都可能会有一个或两个可供升级的、比集成的默认版本更高的 IE 版本。更高版本的 IE 需要通过 Windows 自动更新、Microsoft Update 更新，或者您手动下载[安装程序](/detail/kd_17506.html)进行安装升级。升级之后的新版本 IE 将取代您的 Windows 集成的默认版本 IE。

例如，[Windows 7](/detail/kd_17984.html) 集成的默认版本的 IE 为 IE 8。您可以通过 Windows 自动更新、Microsoft Update、或手动下载安装的方式升级至 IE 9。但您无法单独卸载或单独重新安装 IE 8，也无法在 Windows 7 中降级为 IE7、IE 6 等更低的版本。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344236192413_603.png)

以下表格为您说明了各种不同版本的 Windows 集成的 IE 版本与可升级的 IE 版本：

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344236192413_816.png)

Windows 操作系统 IE 浏览器的版本唯一性

Windows 操作系统只能具有一个唯一的 IE 版本。当您安装了可升级的更新版本的 IE，Windows 集成的默认版本的 IE 就将被取代；当您卸载了升级后的更新版本的 IE，Windows 就会自动恢复其集成的 IE 默认版本。不同版本的 IE 无法在 Windows 操作系统中共存。

在您安装了可升级的更新版本的 IE 之后，如果您自行删除了更新版本 IE 的卸载程序，那么您将无法卸载更新版本的 IE，也不能单独重新安装 Windows 集成的默认版本 IE。此时，您将只能通过重新安装 Windows 的方法恢复 Windows 集成的默认版本 IE。

[Windows 8](/detail/kd_17985.html)、Windows Server 2012：

Windows 8、Windows Server 2012 只能使用集成的默认版本 －IE 10，无法降级为任何早期版本的 IE。截止至 2012 年，没有版本高于 IE 10 的，可供 Windows 8、Windows Server 2012 升级的更新版本的 IE。

Windows 8 的 IE 10 具有桌面版、Metro 版两种不同的形态，分别为桌面操作体验与触控操作体验而设。您可以在 Windows 8 的 Internet 选项中选择桌面版或 Metro 版作为 IE 10 打开链接的默认方式。

![](https://webdoc.lenovo.com.cn/lenovowsi/20120806/1344236192413_349.png)

Windows 7、Windows Server 2008 R2：

Windows 7、Windows Server 2008 R2 集成的默认版本是 IE 8，可以选择升级至 IE 9。IE 9 是惟一没有被集成在任何 Windows 中的 IE 版本，它只能在 Windows 7、Windows Server 2008 R2 中单独安装升级。

您可以通过 Windows 自动更新、Microsoft Update、或手动下载安装的方式在 Windows 7、Windows Server 2008 R2 中升级至 IE 9。如果需要卸载 IE 9，请在 Windows 7、Windows Server 2008 R2 的[控制面板](/detail/kd_18077.html)中选择“**打开或关闭 Windows 功能**”－“**已安装的更新**”，在已安装的更新列表中选择 IE 9 进行卸载，卸载后 Windows 7、Windows Server 2008 R2 将自动恢复为默认版本 IE 8。

Windows Vista、Windows Server 2008：

Windows Vista、Windows Server 2008 集成的默认版本是 IE 7，可以选择升级至 IE 8 或 IE 9。如果要升级至 IE 9，您既可以首先升级至 IE 8 再升级至 IE 9，也可以不升级至 IE 8、从 IE 7 直接升级至 IE 9。

如果需要卸载 IE 8 或 IE 9，您可能会遇到如下情况：

1. 如果您首先升级至 IE 8、然后又升级至 IE 9，那么您将在“**打开或关闭 Windows 功能**”－“**已安装的更新**”中同时看到 IE 8、IE 9 的卸载程序。此时，如果您选择先卸载 IE 9，卸载后 Windows Vista、Windows Server 2008 将恢复为 IE 8。如需恢复为 IE 7，您需要再次选择继续卸载 IE 8。

2. 如果您首先升级至 IE 8、然后又升级至 IE 9，那么您将在“**打开或关闭 Windows 功能**”－“**已安装的更新**”中同时看到 IE 8、IE 9 的卸载程序。此时，如果您选择先卸载 IE 8，Windows Vista、Windows Server 2008 只会将 IE 8 的有关[系统文件](/detail/kd_17533.html)删除，但此时的 IE 版本将依旧是 IE 9。如需恢复为 IE 7，您依然需要再次选择卸载 IE 9。

3. 如果您没有升级过 IE 8，而是从 IE 7 直接升级至 IE 9，那么您将在“**打开或关闭 Windows 功能**”－“**已安装的更新**”中只看到 IE 9 的卸载程序。如果您选择卸载 IE 9，卸载后 Windows Vista、Windows Server 2008 将自动恢复为 IE 7。

4. 如果您没有升级过 IE 9，而是从 IE 7 仅升级至 IE 8，那么您将在“**打开或关闭 Windows 功能**”－“**已安装的更新**”中只看到 IE 8 的卸载程序。如果您选择卸载 IE 8，卸载后 Windows Vista、Windows Server 2008 将自动恢复为 IE 7。

Windows XP、[Windows Server 2003](/detail/kd_17893.html)（R2）：

Windows XP、Windows Server 2003（R2） 集成的默认版本是 IE 6，可以选择升级至 IE 7 或 IE 8。如果要升级至 IE 8，您既可以首先升级至 IE 7 再升级至 IE 8，也可以不升级至 IE 7、从 IE 6 直接升级至 IE 8。

如果需要卸载 IE 7 或 IE 8，请在 Windows XP、Windows Server 2003（R2） 的控制面板中选择“**添加删除程序**”，并在已安装的程序列表中选择 IE 7 或 IE 8 进行卸载。在卸载 IE 7 或 IE 8 时，您可能会遇到如下情况：

1. 如果您首先升级至 IE 7、然后又升级至 IE 8，那么您将在“**添加删除程序**”列表中看到 IE 8 的卸载程序、不会看到 IE 7 的卸载程序。如果您选择卸载 IE 8，卸载后 Windows XP、Windows Server 2003（R2） 将恢复为 IE 7。此时，您将在“**添加删除程序**”列表中重新看到 IE 7 卸载程序。如需恢复为 IE 6，您需要再次选择继续卸载 IE 7。

2. 如果您没有升级过 IE 7，而是从 IE 6 直接升级至 IE 8，那么您依然将在“**添加删除程序**”列表中看到 IE 8 的卸载程序。如果选择卸载 IE 8，卸载后 Windows XP、Windows Server 2003（R2） 将自动恢复为 IE 6。

3. 如果您没有升级过 IE 8，而是从 IE 6 仅升级至 IE 7，那么您将在“**添加删除程序**”列表中看到 IE 7 的卸载程序。如果选择卸载 IE 7，卸载后 Windows XP、Windows Server 2003（R2） 将自动恢复为 IE 6。

Windows 2000:

Windows 2000 集成的默认版本是 IE 5，可以选择升级至 IE 6。需要注意，Windows 2000 可以升级的 IE 6 版本最高为 IE 6 SP1，低于 Windows XP、Windows Server 2003（R2） 集成的 IE 6 版本（IE 6 SP2 或 IE 6 SP3）。

如果需要卸载 IE6，请在 Windows 2000 的控制面板中选择“**添加删除程序**”，然后在已安装的程序列表中选择 IE 6 进行卸载，卸载后 Windows 2000 将自动恢复为默认的版本 IE 5。

来源：[微软知识库](http://support.microsoft.com/kb/2734420/zh-cn)

<!-- 文档主题：Internet Explorer版本升级说明 (知识库库编号: 39) -->